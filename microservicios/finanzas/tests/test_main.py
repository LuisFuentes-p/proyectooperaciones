from __future__ import annotations

from datetime import datetime
import unittest

from fastapi.testclient import TestClient

import app.main as fin_app


class FakeCursor:
    def __init__(self, store: dict[str, list[dict]]):
        self.store = store
        self._result = None
        self._results = []
        self.rowcount = 0

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("select id, username, display_name, role, active, created_at from app_users where username = %s and active = true"):
            username = params[0]
            user = next((row for row in self.store["users"] if row["username"] == username and row["active"]), None)
            self._result = self._user_row(user) if user else None
        elif normalized.startswith("select id, username, display_name, role, active, created_at from app_users order by id asc"):
            self._results = [self._user_row(row) for row in sorted(self.store["users"], key=lambda item: item["id"])]
        elif normalized.startswith("insert into report_files"):
            report_id = len(self.store["reports"]) + 1
            record = {
                "id": report_id,
                "report_key": params[0],
                "title": params[1],
                "filename": params[2],
                "content_type": params[3],
                "file_bytes": params[4],
                "file_size": params[5],
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
            }
            self.store["reports"].append(record)
            self._result = (report_id, record["created_at"])
        elif normalized.startswith("select id, report_key, title, filename, content_type, file_size, created_at from report_files order by created_at desc, id desc"):
            ordered = sorted(self.store["reports"], key=lambda item: (item["created_at"], item["id"]), reverse=True)
            self._results = [
                (
                    row["id"],
                    row["report_key"],
                    row["title"],
                    row["filename"],
                    row["content_type"],
                    row["file_size"],
                    row["created_at"],
                )
                for row in ordered
            ]
        elif normalized.startswith("select file_bytes, filename, content_type from report_files where id = %s"):
            report_id = params[0]
            row = next((item for item in self.store["reports"] if item["id"] == report_id), None)
            self._result = (row["file_bytes"], row["filename"], row["content_type"]) if row else None
        elif normalized.startswith("delete from report_files where id = %s"):
            report_id = params[0]
            before = len(self.store["reports"])
            self.store["reports"] = [item for item in self.store["reports"] if item["id"] != report_id]
            self.rowcount = before - len(self.store["reports"])
        else:
            self._result = None
            self._results = []

    def _user_row(self, user: dict):
        return (
            user["id"],
            user["username"],
            user["display_name"],
            user["role"],
            user["active"],
            user["created_at"],
        )

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, store: dict[str, list[dict]]):
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
        return False


class FinanzasServiceTests(unittest.TestCase):
    def setUp(self):
        self.store = {
            "users": [
                {"id": 1, "username": "admin", "display_name": "Administrador", "role": "admin", "active": True, "created_at": datetime(2026, 5, 6, 10, 0, 0)},
                {"id": 2, "username": "viewer", "display_name": "Consulta General", "role": "viewer", "active": True, "created_at": datetime(2026, 5, 6, 10, 5, 0)},
            ],
            "reports": [],
        }
        self._orig_initialize_database = fin_app.initialize_database
        self._orig_get_connection = fin_app.get_connection

        fin_app.initialize_database = lambda: None
        fin_app.get_connection = lambda: FakeConn(self.store)
        self.client = TestClient(fin_app.app)

    def tearDown(self):
        self.client.close()
        fin_app.initialize_database = self._orig_initialize_database
        fin_app.get_connection = self._orig_get_connection

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_user_permissions_and_report_creation(self):
        user_response = self.client.get("/users/me", headers={"X-User-Name": "admin"})
        self.assertEqual(user_response.status_code, 200)
        self.assertIn("finanzas", user_response.json()["permissions"])

        list_response = self.client.get("/users", headers={"X-User-Name": "admin"})
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["items"]), 2)

        report_response = self.client.post("/reports/ingresos-totales", headers={"X-User-Name": "admin"})
        self.assertEqual(report_response.status_code, 200)
        payload = report_response.json()
        self.assertEqual(payload["report_key"], "ingresos_totales")
        self.assertGreater(payload["file_size"], 0)
        self.assertEqual(payload["id"], 1)
