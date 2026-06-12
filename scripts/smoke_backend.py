"""In-process backend smoke test via FastAPI TestClient. MySQL test-БД.

Создаёт временную БД `belpomoshnik_smoke` в локальном MySQL, гоняет сценарии и
дропает её. Переменные окружения выставляются ДО импорта backend.*
"""
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

import pymysql

# Изолированная MySQL-БД ДО импорта backend (engine читает env при импорте).
# Можно переопределить через BELPOMOSHNIK_SMOKE_DATABASE_URL.
_DEFAULT_SMOKE_URL = "mysql+pymysql://root:belp_root@127.0.0.1:3306/belpomoshnik_smoke?charset=utf8mb4"
os.environ["BELPOMOSHNIK_DATABASE_URL"] = os.environ.get(
    "BELPOMOSHNIK_SMOKE_DATABASE_URL", _DEFAULT_SMOKE_URL
)
os.environ["BELPOMOSHNIK_SECRET_KEY"] = "smoke-test-secret-key-256bit-aaaaaaaaaaaa"

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from backend.config import get_database_url  # noqa: E402

# Создаём БД если её нет.
_parsed = urlparse(get_database_url().replace("mysql+pymysql://", "mysql://", 1))
_db_name = _parsed.path.lstrip("/").split("?")[0]
_admin = pymysql.connect(
    host=_parsed.hostname,
    port=_parsed.port or 3306,
    user=_parsed.username or "root",
    password=_parsed.password or "",
    charset="utf8mb4",
)
try:
    with _admin.cursor() as cur:
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{_db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
    _admin.commit()
finally:
    _admin.close()

from fastapi.testclient import TestClient  # noqa: E402

from backend.app import app  # noqa: E402
from backend.auth import hash_password  # noqa: E402
from backend.database import SessionLocal, engine  # noqa: E402
from backend.models import Base, Role, User  # noqa: E402

PASS, FAIL = 0, 0


def check(name: str, cond: bool, extra: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {extra}")


def setup_db() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        for rid, title in [("citizen", "Гражданин"), ("content_editor", "Редактор"), ("platform_admin", "Администратор")]:
            if not db.get(Role, rid):
                db.add(Role(id=rid, title=title))
        db.commit()
        # content_editor for admin endpoints
        editor = User(email="editor@bel.by", hashed_password=hash_password("editor-pass-123"), name="Editor", role_id="content_editor")
        db.add(editor)
        db.commit()
    finally:
        db.close()


def main() -> int:
    print("== setup ==")
    setup_db()
    client = TestClient(app)  # triggers lifespan (scheduler start)

    print("== bcrypt hashing ==")
    from backend.auth import hash_password as hp, verify_password as vp
    h = hp("hello-world-pw")
    check("hash+verify roundtrip", vp("hello-world-pw", h))
    check("verify rejects wrong", not vp("nope", h))
    check("verify rejects garbage hash", not vp("x", "not-a-hash"))

    print("== health ==")
    r = client.get("/api/health")
    check("health 200", r.status_code == 200, str(r.status_code))

    print("== register (citizen) ==")
    r = client.post("/api/auth/register", json={"email": "user1@bel.by", "password": "user-pass-123", "name": "User One"})
    check("register 201", r.status_code == 201, r.text[:120])
    tok = r.json() if r.status_code == 201 else {}
    check("register returns access_token", bool(tok.get("access_token")))
    check("register returns refresh_token", bool(tok.get("refresh_token")))

    print("== register duplicate -> 409 ==")
    r = client.post("/api/auth/register", json={"email": "user1@bel.by", "password": "user-pass-123", "name": "Dup"})
    check("duplicate email 409", r.status_code == 409, str(r.status_code))

    print("== login wrong password -> 401 ==")
    r = client.post("/api/auth/login", data={"username": "user1@bel.by", "password": "WRONG"})
    check("login wrong 401", r.status_code == 401, str(r.status_code))

    print("== login correct ==")
    r = client.post("/api/auth/login", data={"username": "user1@bel.by", "password": "user-pass-123"})
    check("login 200", r.status_code == 200, r.text[:120])
    user_tok = r.json().get("access_token", "") if r.status_code == 200 else ""

    print("== /me ==")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {user_tok}"})
    check("/me 200", r.status_code == 200, str(r.status_code))
    check("/me role citizen", r.json().get("role") == "citizen" if r.status_code == 200 else False)

    print("== citizen cannot access admin -> 403 ==")
    r = client.get("/api/admin/problems", headers={"Authorization": f"Bearer {user_tok}"})
    check("citizen admin 403", r.status_code == 403, str(r.status_code))

    print("== no token admin -> 401 ==")
    r = client.get("/api/admin/problems")
    check("no token admin 401", r.status_code == 401, str(r.status_code))

    print("== editor login + admin access ==")
    r = client.post("/api/auth/login", data={"username": "editor@bel.by", "password": "editor-pass-123"})
    editor_tok = r.json().get("access_token", "") if r.status_code == 200 else ""
    H = {"Authorization": f"Bearer {editor_tok}"}
    r = client.get("/api/admin/problems", headers=H)
    check("editor admin 200", r.status_code == 200, str(r.status_code))

    print("== admin CRUD: problem -> scenario -> verify ==")
    r = client.post("/api/admin/problems", headers=H, json={"title": "Тестовая проблема", "slug": "test-problem"})
    check("create problem 201", r.status_code == 201, r.text[:160])
    pid = r.json().get("id") if r.status_code == 201 else None

    r = client.post("/api/admin/scenarios", headers=H, json={"problem_id": pid, "title": "Тестовый сценарий", "slug": "test-scn"})
    check("create scenario 201", r.status_code == 201, r.text[:160])
    sid = r.json().get("id") if r.status_code == 201 else None

    r = client.post(f"/api/admin/scenarios/{sid}/verify", headers=H)
    check("verify scenario 200", r.status_code == 200, r.text[:160])
    check("verified_at set", bool(r.json().get("content_verified_at")) if r.status_code == 200 else False)
    check("verified_by editor", r.json().get("verified_by") == "editor@bel.by" if r.status_code == 200 else False)

    print("== reorder stages ==")
    s1 = client.post(f"/api/admin/scenarios/{sid}/stages", headers=H, json={"scenario_id": sid, "title": "Этап 1", "order_index": 0}).json()
    s2 = client.post(f"/api/admin/scenarios/{sid}/stages", headers=H, json={"scenario_id": sid, "title": "Этап 2", "order_index": 1}).json()
    r = client.patch(f"/api/admin/scenarios/{sid}/stages/reorder", headers=H, json={"ids": [s2["id"], s1["id"]]})
    check("reorder stages 204", r.status_code == 204, str(r.status_code))
    detail = client.get(f"/api/admin/scenarios/{sid}", headers=H).json()
    new_order = [st["id"] for st in sorted(detail["stages"], key=lambda x: x["order_index"])]
    check("reorder applied", new_order == [s2["id"], s1["id"]], str(new_order))

    print("== delete problem (cascade) ==")
    r = client.delete(f"/api/admin/problems/{pid}", headers=H)
    check("delete problem 204", r.status_code == 204, str(r.status_code))

    print("== audit log captured events ==")
    r = client.get("/api/admin/audit-logs", headers=H)
    actions = [a.get("action", "") for a in r.json()] if r.status_code == 200 else []
    check("audit has verify event", any("верифиц" in a.lower() for a in actions), str(len(actions)))
    check("audit has delete event", any("удал" in a.lower() for a in actions))

    print("== rate limiting (6 bad logins -> 429) ==")
    codes = []
    for _ in range(7):
        rr = client.post("/api/auth/login", data={"username": "ratelimit@bel.by", "password": "x"})
        codes.append(rr.status_code)
    check("rate limit triggers 429", 429 in codes, str(codes))

    print("== refresh token rotation ==")
    r = client.post("/api/auth/login", data={"username": "user1@bel.by", "password": "user-pass-123"})
    rt = r.json().get("refresh_token", "")
    r = client.post("/api/auth/refresh", json={"refresh_token": rt})
    check("refresh 200", r.status_code == 200, str(r.status_code))
    r2 = client.post("/api/auth/refresh", json={"refresh_token": rt})
    check("old refresh revoked -> 401", r2.status_code == 401, str(r2.status_code))

    print(f"\n== RESULT: {PASS} passed, {FAIL} failed ==")
    # Дропаем временную БД, чтобы не оставлять мусор.
    try:
        _drop = pymysql.connect(
            host=_parsed.hostname,
            port=_parsed.port or 3306,
            user=_parsed.username or "root",
            password=_parsed.password or "",
            charset="utf8mb4",
        )
        with _drop.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{_db_name}`")
        _drop.commit()
        _drop.close()
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] не удалось дропнуть {_db_name}: {exc}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
