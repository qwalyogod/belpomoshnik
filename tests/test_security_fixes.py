"""Prompt 7: защитные проверки модерации и предложений."""


def test_blocked_submitter_cannot_create_proposal(client, citizen_token, admin_headers):
    users = client.get("/api/admin/users", headers=admin_headers, params={"search": "citizen@bel.by"}).json()
    uid = users[0]["id"]

    assert client.post(f"/api/articles/blocked/{uid}", headers=admin_headers).status_code == 200
    h = {"Authorization": f"Bearer {citizen_token}"}
    r = client.post(
        "/api/articles",
        headers=h,
        json={"title": "Предложение", "summary": "Кратко", "body_html": "<p>Текст</p>", "status": "review", "as_proposal": True},
    )
    assert r.status_code == 403
