"""Prompt 7: содержимое сайта видно и проверяется в админке."""


def test_dashboard_stats_include_core_entities(client, admin_headers):
    problem = client.post("/api/admin/problems", headers=admin_headers, json={"title": "Проблема", "slug": "stats-problem", "status": "published"}).json()
    client.post("/api/admin/scenarios", headers=admin_headers, json={"problem_id": problem["id"], "title": "Сценарий", "slug": "stats-scenario", "status": "published"})

    stats = client.get("/api/admin/dashboard/stats", headers=admin_headers).json()
    assert stats["users_total"] >= 1
    assert stats["problems_total"] >= 1
    assert stats["scenarios_total"] >= 1


def test_problems_and_scenarios_are_visible_with_filters(client, admin_headers):
    problem = client.post(
        "/api/admin/problems",
        headers=admin_headers,
        json={"title": "Потеря паспорта", "slug": "passport-admin", "category": "Документы", "status": "published"},
    ).json()
    scenario = client.post(
        "/api/admin/scenarios",
        headers=admin_headers,
        json={"problem_id": problem["id"], "title": "Восстановить паспорт", "slug": "passport-restore-admin", "status": "published"},
    ).json()

    problems = client.get("/api/admin/problems", headers=admin_headers, params={"search": "паспорт", "status": "published"}).json()
    assert any(item["id"] == problem["id"] for item in problems)

    scenarios = client.get("/api/admin/scenarios", headers=admin_headers, params={"search": "паспорт", "status": "published"}).json()
    found = next(item for item in scenarios if item["id"] == scenario["id"])
    assert found["category"] == "Документы"


def test_scenario_integrity_reports_errors_and_warnings(client, admin_headers):
    problem = client.post("/api/admin/problems", headers=admin_headers, json={"title": "Проблема", "slug": "integrity-problem"}).json()
    scenario = client.post("/api/admin/scenarios", headers=admin_headers, json={"problem_id": problem["id"], "title": "Сценарий", "slug": "integrity-scenario"}).json()

    report = client.get(f"/api/admin/scenarios/{scenario['id']}/integrity", headers=admin_headers).json()
    assert report["is_valid"] is False
    assert any("описание" in item.lower() for item in report["errors"])
    assert any("этап" in item.lower() for item in report["errors"])


def test_admin_can_change_publication_status(client, admin_headers):
    r = client.post(
        "/api/articles",
        headers=admin_headers,
        json={"title": "Материал", "summary": "Кратко", "body_html": "<p>Текст</p>", "status": "draft"},
    )
    assert r.status_code == 201
    article_id = r.json()["id"]
    r = client.put(f"/api/articles/{article_id}", headers=admin_headers, json={"status": "published"})
    assert r.status_code == 200
    assert r.json()["status"] == "published"
