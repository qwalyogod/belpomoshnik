"""
End-to-end Client->API integration: real urllib client classes against a
live uvicorn server. Proves the Flet client's data layer works over HTTP.

Run: .venv/bin/python scripts/integration_client.py
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

PORT = 8077
BASE = f"http://127.0.0.1:{PORT}"
PASS, FAIL = 0, 0


def check(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {extra}")


def wait_health(timeout=30):
    for _ in range(timeout * 2):
        try:
            with urllib.request.urlopen(f"{BASE}/api/health", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def main():
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.close()
    env = dict(os.environ)
    env["BELPOMOSHNIK_DATABASE_URL"] = f"sqlite:///{tmp.name}"
    env["BELPOMOSHNIK_SECRET_KEY"] = "integration-secret-256bit-aaaaaaaaaaaa"
    env["PYTHONPATH"] = str(SRC)

    # Bootstrap schema + roles
    subprocess.run([sys.executable, "-m", "backend.bootstrap"], cwd=str(SRC), env=env, check=True)

    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.app:app", "--port", str(PORT), "--log-level", "warning"],
        cwd=str(SRC), env=env,
    )
    try:
        if not wait_health():
            print("[FATAL] server did not start")
            return 1

        from services.auth_api import AuthAPIClient
        from services.user_api import UserAPIClient

        auth = AuthAPIClient(BASE)
        check("server healthy", auth.health())

        tokens = auth.register("Integration User", "int@bel.by", "int-pass-123")
        check("register returns token", bool(tokens.get("access_token")))

        api = UserAPIClient(BASE, access_token=tokens["access_token"])

        # Profile
        prof = api.update_profile({"city": "Минск", "interest_tags": ["family"]})
        check("profile updated", prof["city"] == "Минск" and prof["interest_tags"] == ["family"])

        # Settings
        api.update_settings({"dark_theme": True})
        check("settings persisted", api.get_settings().get("dark_theme") is True)

        # Documents
        doc = api.create_document({"title": "Паспорт", "doc_type": "passport", "expiry_date": "2030-01-01"})
        check("document created", bool(doc.get("id")))
        api.update_document(doc["id"], {"comment": "ок"})
        check("document in list", any(d["id"] == doc["id"] for d in api.list_documents()))
        api.delete_document(doc["id"])
        check("document deleted", all(d["id"] != doc["id"] for d in api.list_documents()))

        # Situation + task progress
        sit = api.create_situation({"title": "Рождение ребёнка", "tasks": [{"title": "A"}, {"title": "B"}]})
        check("situation progress 0", sit["progress"] == 0)
        api.update_task(sit["tasks"][0]["id"], {"completed": True})
        refreshed = api.get_situation(sit["id"])
        check("progress 50 after one task", refreshed["progress"] == 50)

        # Notifications
        notif = api.create_notification({"title": "Срок завтра"})
        check("notification created", bool(notif.get("id")))
        check("notification read", api.mark_notification_read(notif["id"])["is_read"] is True)

        # Utility
        acc = api.create_utility_account({"address": "ул. Независимости, 25", "provider": "РСЦ"})
        acc2 = api.add_utility_payment(acc["id"], {"period": "Май 2026", "amount": 78.4})
        check("utility payment added", len(acc2["payments"]) == 1 and acc2["payments"][0]["amount"] == 78.4)

        # Taxes
        tax = api.create_tax({"title": "Декларация", "deadline": "2026-03-01"})
        check("tax created", bool(tax.get("id")))
        api.update_tax(tax["id"], {"status": "Оплачено"})
        check("tax updated", any(t["status"] == "Оплачено" for t in api.list_taxes()))

        print(f"\n== INTEGRATION: {PASS} passed, {FAIL} failed ==")
        return 1 if FAIL else 0
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())
