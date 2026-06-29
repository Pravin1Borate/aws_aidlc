from __future__ import annotations


# ─── helpers ────────────────────────────────────────────────────────────


def _register_login(client, email: str = "owner@example.com", password: str = "Password1") -> str:
    client.post(
        "/auth/register",
        json={"email": email, "password": password, "full_name": "Owner"},
    )
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_task(client, token: str, **fields) -> dict:
    resp = client.post("/tasks/", json={"title": "Task", **fields}, headers=_auth(token))
    assert resp.status_code == 201, resp.text
    return resp.json()


# ─── auth enforcement ────────────────────────────────────────────────────


class TestAuthEnforcement:
    def test_list_requires_auth(self, client):
        assert client.get("/tasks/").status_code == 401

    def test_create_requires_auth(self, client):
        assert client.post("/tasks/", json={"title": "X"}).status_code == 401

    def test_get_requires_auth(self, client):
        assert client.get("/tasks/some-id").status_code == 401

    def test_put_requires_auth(self, client):
        assert client.put("/tasks/some-id", json={"title": "X"}).status_code == 401

    def test_patch_requires_auth(self, client):
        assert client.patch("/tasks/some-id", json={}).status_code == 401

    def test_delete_requires_auth(self, client):
        assert client.delete("/tasks/some-id").status_code == 401


# ─── create ──────────────────────────────────────────────────────────────


class TestCreateTask:
    def test_create_minimal_task(self, client):
        token = _register_login(client)
        resp = client.post("/tasks/", json={"title": "My Task"}, headers=_auth(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Task"
        assert data["status"] == "todo"
        assert data["priority"] == "medium"
        assert "id" in data
        assert "deleted_at" not in data

    def test_create_task_with_all_fields(self, client):
        token = _register_login(client)
        resp = client.post(
            "/tasks/",
            json={
                "title": "Full Task",
                "description": "desc",
                "status": "in_progress",
                "priority": "high",
                "due_date": "2025-12-31",
                "category": "work",
                "tags": ["urgent"],
            },
            headers=_auth(token),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["due_date"] == "2025-12-31"
        assert "urgent" in data["tags"]

    def test_create_without_title_returns_422(self, client):
        token = _register_login(client)
        assert client.post("/tasks/", json={}, headers=_auth(token)).status_code == 422

    def test_create_with_invalid_status_returns_422(self, client):
        token = _register_login(client)
        resp = client.post(
            "/tasks/", json={"title": "T", "status": "invalid"}, headers=_auth(token)
        )
        assert resp.status_code == 422


# ─── get ─────────────────────────────────────────────────────────────────


class TestGetTask:
    def test_get_by_id(self, client):
        token = _register_login(client)
        created = _create_task(client, token)
        resp = client.get(f"/tasks/{created['id']}", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_get_nonexistent_returns_404(self, client):
        token = _register_login(client)
        assert client.get("/tasks/nonexistent", headers=_auth(token)).status_code == 404

    def test_any_authenticated_user_can_read(self, client):
        owner = _register_login(client, "own2@example.com")
        other = _register_login(client, "oth2@example.com")
        created = _create_task(client, owner)
        assert client.get(f"/tasks/{created['id']}", headers=_auth(other)).status_code == 200


# ─── list ────────────────────────────────────────────────────────────────


class TestListTasks:
    def test_returns_paginated_shape(self, client):
        token = _register_login(client)
        _create_task(client, token)
        resp = client.get("/tasks/", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        for key in ("items", "total", "limit", "offset"):
            assert key in data

    def test_filter_by_status(self, client):
        token = _register_login(client)
        _create_task(client, token, status="todo")
        _create_task(client, token, status="done")
        data = client.get("/tasks/?status=todo", headers=_auth(token)).json()
        assert all(t["status"] == "todo" for t in data["items"])

    def test_filter_by_priority(self, client):
        token = _register_login(client)
        _create_task(client, token, priority="high")
        _create_task(client, token, priority="low")
        data = client.get("/tasks/?priority=high", headers=_auth(token)).json()
        assert all(t["priority"] == "high" for t in data["items"])

    def test_pagination(self, client):
        token = _register_login(client)
        for i in range(5):
            _create_task(client, token, title=f"Task {i}")
        data = client.get("/tasks/?limit=2&offset=0", headers=_auth(token)).json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["limit"] == 2

    def test_soft_deleted_not_in_list(self, client):
        token = _register_login(client)
        created = _create_task(client, token)
        client.delete(f"/tasks/{created['id']}", headers=_auth(token))
        ids = [t["id"] for t in client.get("/tasks/", headers=_auth(token)).json()["items"]]
        assert created["id"] not in ids


# ─── full update ─────────────────────────────────────────────────────────


class TestUpdateTask:
    def test_owner_can_full_update(self, client):
        token = _register_login(client)
        created = _create_task(client, token)
        resp = client.put(
            f"/tasks/{created['id']}",
            json={"title": "Updated", "status": "done"},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated"
        assert data["status"] == "done"

    def test_unrelated_user_gets_403(self, client):
        owner = _register_login(client, "own3@example.com")
        other = _register_login(client, "oth3@example.com")
        created = _create_task(client, owner)
        resp = client.put(
            f"/tasks/{created['id']}", json={"title": "Hack"}, headers=_auth(other)
        )
        assert resp.status_code == 403

    def test_nonexistent_task_returns_404(self, client):
        token = _register_login(client)
        assert (
            client.put("/tasks/nope", json={"title": "X"}, headers=_auth(token)).status_code
            == 404
        )


# ─── patch ───────────────────────────────────────────────────────────────


class TestPatchTask:
    def test_partial_update_preserves_unchanged_fields(self, client):
        token = _register_login(client)
        created = _create_task(client, token, priority="high")
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "done"}, headers=_auth(token)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert data["priority"] == "high"

    def test_tag_merge(self, client):
        token = _register_login(client)
        created = _create_task(client, token, tags=["a", "b"])
        resp = client.patch(
            f"/tasks/{created['id']}",
            json={"tags": ["c"], "tags_remove": ["a"]},
            headers=_auth(token),
        )
        assert resp.status_code == 200
        assert set(resp.json()["tags"]) == {"b", "c"}


# ─── delete ──────────────────────────────────────────────────────────────


class TestDeleteTask:
    def test_owner_can_delete(self, client):
        token = _register_login(client)
        created = _create_task(client, token)
        assert client.delete(f"/tasks/{created['id']}", headers=_auth(token)).status_code == 204

    def test_deleted_task_returns_404(self, client):
        token = _register_login(client)
        created = _create_task(client, token)
        client.delete(f"/tasks/{created['id']}", headers=_auth(token))
        assert client.get(f"/tasks/{created['id']}", headers=_auth(token)).status_code == 404

    def test_non_owner_cannot_delete(self, client):
        owner = _register_login(client, "own4@example.com")
        other = _register_login(client, "oth4@example.com")
        created = _create_task(client, owner)
        assert (
            client.delete(f"/tasks/{created['id']}", headers=_auth(other)).status_code == 403
        )
