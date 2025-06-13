import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def tokens(client: TestClient):
    r = client.post("/register", json={"username":"user1","password":"pass1"})
    assert r.status_code == 201
    r = client.post("/login", data={"username":"user1","password":"pass1"})
    assert r.status_code == 200
    token1 = r.json()["access_token"]

    r = client.post("/register", json={"username":"user2","password":"pass2"})
    assert r.status_code == 201
    r = client.post("/login", data={"username":"user2","password":"pass2"})
    assert r.status_code == 200
    token2 = r.json()["access_token"]

    return {"user1": token1, "user2": token2}


def test_protected_profile(client: TestClient, tokens):
    r = client.get("/users/me")
    assert r.status_code == 401

    r = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {tokens['user1']}"}
    )
    assert r.status_code == 200
    assert r.json()["username"] == "user1"


def test_crud_notes_and_access_control(client: TestClient, tokens):
    h1 = {"Authorization": f"Bearer {tokens['user1']}"}
    h2 = {"Authorization": f"Bearer {tokens['user2']}"}

    r = client.post("/notes", json={"title":"T1","content":"C1"}, headers=h1)
    assert r.status_code == 201
    note_id = r.json()["id"]

    r = client.get("/notes", headers=h1)
    assert r.status_code == 200 and len(r.json()) == 1
    r = client.get(f"/notes/{note_id}", headers=h1)
    assert r.status_code == 200

    for method, url, body in [
        ("get", f"/notes/{note_id}", None),
        ("put", f"/notes/{note_id}", {"content":"x"}),
        ("delete", f"/notes/{note_id}", None),
    ]:
        kwargs = {"headers": h2}
        if body is not None:
            kwargs["json"] = body
        r = getattr(client, method)(url, **kwargs)
        assert r.status_code == 404

    r = client.put(
        f"/notes/{note_id}",
        json={"content":"C1-upd"},
        headers=h1
    )
    assert r.status_code == 200 and r.json()["content"] == "C1-upd"
    r = client.delete(f"/notes/{note_id}", headers=h1)
    assert r.status_code == 204

    r = client.get(f"/notes/{note_id}", headers=h1)
    assert r.status_code == 404
