from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

import app.main as auth_app


class FakeUniqueViolation(Exception):
    pass


class FakeCursor:
    def __init__(self, store: dict[str, dict[str, str]]):
        self.store = store
        self._result = None

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("insert into auth_users"):
            username, password_hash = params
            if username in self.store["users"]:
                raise FakeUniqueViolation()
            user_id = len(self.store["users"]) + 1
            self.store["users"][username] = {"id": user_id, "password_hash": password_hash}
            self._result = (user_id,)
        elif normalized.startswith("select id, password_hash from auth_users where username = %s"):
            username = params[0]
            user = self.store["users"].get(username)
            self._result = (user["id"], user["password_hash"]) if user else None
        else:
            self._result = None

    def fetchone(self):
        return self._result

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, store: dict[str, dict[str, str]]):
        self.store = store

    def cursor(self):
        return FakeCursor(self.store)

    def commit(self):
        return None

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False


@pytest.fixture()
def client(monkeypatch):
    store = {"users": {}}
    monkeypatch.setattr(auth_app, "initialize_database", lambda: None)
    monkeypatch.setattr(auth_app.psycopg.errors, "UniqueViolation", FakeUniqueViolation)
    monkeypatch.setattr(auth_app, "get_conn", lambda: FakeConn(store))
    monkeypatch.setattr(auth_app.bcrypt, "hash", lambda value: f"hashed:{value}")
    monkeypatch.setattr(auth_app.bcrypt, "verify", lambda value, hashed: hashed == f"hashed:{value}")
    with TestClient(auth_app.app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "autenticacion"


def test_register_and_login(client):
    register_response = client.post("/register", json={"username": "alice", "password": "secret"})
    assert register_response.status_code == 200
    assert register_response.json()["message"] == "user created"

    login_response = client.post("/login", json={"username": "alice", "password": "secret"})
    assert login_response.status_code == 200
    assert login_response.json()["token_type"] == "bearer"
    assert login_response.json()["access_token"]
