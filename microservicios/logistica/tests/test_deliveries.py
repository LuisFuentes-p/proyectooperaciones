from datetime import datetime

from fastapi.testclient import TestClient
import pytest

import app.main as logistica_app


class FakeCursor:
    def __init__(self, store):
        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("insert into deliveries"):
            d_id = len(self.store["deliveries"]) + 1
            record = {
                "id": d_id,
                "order_id": params[0],
                "delivery_address": params[1],
                "assigned_to": params[2],
                "vehicle": params[3],
                "status": params[4],
                "created_by": params[5],
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
                "assigned_at": None,
                "delivered_at": None,
            }
            self.store["deliveries"].append(record)
            self._result = (record["id"], record["status"], record["created_at"])
        elif normalized.startswith("update deliveries set assigned_to = %s, vehicle = %s"):
            assigned_to, vehicle, d_id = params
            record = next((r for r in self.store["deliveries"] if r["id"] == d_id), None)
            if record:
                record["assigned_to"] = assigned_to
                record["vehicle"] = vehicle
                record["assigned_at"] = datetime(2026, 5, 6, 12, 5, 0)
                self._result = (record["id"], record["assigned_to"], record["vehicle"]) 
            else:
                self._result = None
        elif normalized.startswith("update deliveries set status = %s, delivered_at = now() where id = %s"):
            status, d_id = params
            record = next((r for r in self.store["deliveries"] if r["id"] == d_id), None)
            if record:
                record["status"] = status
                record["delivered_at"] = datetime(2026, 5, 6, 12, 10, 0)
                self._result = (record["id"], record["status"], record["delivered_at"]) 
            else:
                self._result = None
        elif normalized.startswith("update deliveries set status = %s where id = %s"):
            status, d_id = params
            record = next((r for r in self.store["deliveries"] if r["id"] == d_id), None)
            if record:
                record["status"] = status
                self._result = (record["id"], record["status"]) 
            else:
                self._result = None
        elif normalized.startswith("select id, order_id, delivery_address, assigned_to, vehicle, status, created_by, created_at, assigned_at, delivered_at from deliveries where id = %s"):
            d_id = params[0]
            record = next((r for r in self.store["deliveries"] if r["id"] == d_id), None)
            if record:
                self._result = (
                    record["id"], record["order_id"], record["delivery_address"], record["assigned_to"], record["vehicle"], record["status"], record["created_by"], record["created_at"], record["assigned_at"], record["delivered_at"],
                )
            else:
                self._result = None
        elif normalized.startswith("select id, order_id, delivery_address, assigned_to, vehicle, status from deliveries order by created_at desc"):
            rows = []
            for r in self.store["deliveries"]:
                rows.append((r["id"], r["order_id"], r["delivery_address"], r["assigned_to"], r["vehicle"], r["status"]))
            self._results = rows
        else:
            self._result = None
            self._results = []

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, store):
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
    store = {"deliveries": []}
    monkeypatch.setattr(logistica_app, "get_db", lambda: FakeConn(store))
    # prevent startup seeding that expects real DB
    monkeypatch.setattr(logistica_app, "seed_items", lambda: None)
    with TestClient(logistica_app.app) as test_client:
        yield test_client


def test_create_assign_and_update_delivery_flow(client):
    # health
    health = client.get('/health')
    assert health.status_code == 200

    # create
    resp = client.post("/deliveries", json={"order_id": 10, "delivery_address": "Calle Falsa 123"}, headers={"user-name": "logistica"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    d_id = data["id"]

    # assign
    resp2 = client.patch(f"/deliveries/{d_id}/assign", json={"assigned_to": "Juan", "vehicle": "Van-01"}, headers={"user-name": "logistica"})
    assert resp2.status_code == 200
    assert resp2.json()["assigned_to"] == "Juan"

    # update status to in_transit
    resp3 = client.patch(f"/deliveries/{d_id}/status", json={"status": "in_transit"}, headers={"user-name": "logistica"})
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "in_transit"

    # update status to delivered
    resp4 = client.patch(f"/deliveries/{d_id}/status", json={"status": "delivered"}, headers={"user-name": "logistica"})
    assert resp4.status_code == 200
    assert resp4.json()["status"] == "delivered"

    # get
    resp5 = client.get(f"/deliveries/{d_id}", headers={"user-name": "logistica"})
    assert resp5.status_code == 200
    got = resp5.json()
    assert got["id"] == d_id
    assert got["status"] == "delivered"

    # list
    resp6 = client.get("/deliveries", headers={"user-name": "logistica"})
    assert resp6.status_code == 200
    arr = resp6.json()
    assert any(d["id"] == d_id for d in arr)
