from __future__ import annotations

import tempfile
import unittest

from fastapi.testclient import TestClient

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


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = {"users": {}}

        auth_app.initialize_database = lambda: None
        auth_app.psycopg.errors.UniqueViolation = FakeUniqueViolation
        auth_app.get_conn = lambda: FakeConn(self.store)
        auth_app.bcrypt.hash = lambda value: f"hashed:{value}"
        auth_app.bcrypt.verify = lambda value, hashed: hashed == f"hashed:{value}"

        self.client = TestClient(auth_app.app)

    def tearDown(self):
        self.client.close()
        self.temp_dir.cleanup()

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["service"], "autenticacion")

    def test_register_and_login(self):
        register_response = self.client.post("/register", json={"username": "alice", "password": "secret"})
        self.assertEqual(register_response.status_code, 200)
        self.assertEqual(register_response.json()["message"], "user created")

        login_response = self.client.post("/login", json={"username": "alice", "password": "secret"})
        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(login_response.json()["token_type"], "bearer")
        self.assertTrue(login_response.json()["access_token"])
