from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
import pytest

import app.main as inv_app


class FakeCursor:
    def __init__(self, store: dict[str, list[dict]]):
        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("select id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity, unit_cost, unit_of_measure, supplier_id, category, active, last_updated from items where active = true order by sku limit %s offset %s"):
            self._results = [self._item_row(item) for item in sorted(self.store["items"], key=lambda row: row["sku"]) if item["active"]]
        elif normalized.startswith("select id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity, unit_cost, unit_of_measure, supplier_id, category, active, last_updated from items where category = %s and active = true order by sku limit %s offset %s"):
            category = params[0]
            self._results = [self._item_row(item) for item in sorted(self.store["items"], key=lambda row: row["sku"]) if item["active"] and item["category"] == category]
        elif normalized.startswith("select id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity, unit_cost, unit_of_measure, supplier_id, category, active, last_updated from items where id = %s"):
            item_id = params[0]
            item = next((row for row in self.store["items"] if row["id"] == item_id), None)
            self._result = self._item_row(item) if item else None
        elif normalized.startswith("select quantity_on_hand from items where id = %s"):
            item_id = params[0]
            item = next((row for row in self.store["items"] if row["id"] == item_id), None)
            self._result = (item["quantity_on_hand"],) if item else None
        elif normalized.startswith("update items set quantity_on_hand = %s, last_updated = current_timestamp where id = %s"):
            new_qty, item_id = params
            item = next((row for row in self.store["items"] if row["id"] == item_id), None)
            if item:
                item["quantity_on_hand"] = new_qty
                item["last_updated"] = datetime(2026, 5, 6, 12, 0, 0)
        elif normalized.startswith("insert into stock_movements"):
            item_id, movement_type, quantity, reason, reference_id, created_by = params
            self.store["stock_movements"].append(
                {
                    "id": len(self.store["stock_movements"]) + 1,
                    "item_id": item_id,
                    "movement_type": movement_type,
                    "quantity": quantity,
                    "reason": reason,
                    "reference_id": reference_id,
                    "created_by": created_by,
                    "created_at": datetime(2026, 5, 6, 12, 0, 0),
                }
            )
        elif normalized.startswith("select id from items where id = %s"):
            item_id = params[0]
            item = next((row for row in self.store["items"] if row["id"] == item_id), None)
            self._result = (item_id,) if item else None
        elif normalized.startswith("insert into solicitudes_logistica"):
            request_id = len(self.store["requests"]) + 1
            request = {
                "id": request_id,
                "item_id": params[0],
                "requested_quantity": params[1],
                "reason": params[2],
                "priority": params[3],
                "notes": params[4],
                "created_by": params[5],
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
                "status": "pending",
            }
            self.store["requests"].append(request)
            self._result = (request_id, request["created_at"])
        else:
            self._result = None
            self._results = []

    def _item_row(self, item: dict):
        return (
            item["id"],
            item["sku"],
            item["name"],
            item["description"],
            item["quantity_on_hand"],
            item["minimum_threshold"],
            item["reorder_quantity"],
            item["unit_cost"],
            item["unit_of_measure"],
            item["supplier_id"],
            item["category"],
            item["active"],
            item["last_updated"],
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
        self.close()
        return False


@pytest.fixture()
def client(monkeypatch):
    store = {
        "items": [
            {
                "id": 1,
                "sku": "SKU-001",
                "name": "Laptop",
                "description": "Portable",
                "quantity_on_hand": 5,
                "minimum_threshold": 10,
                "reorder_quantity": 20,
                "unit_cost": 1200.0,
                "unit_price": 1500.0,
                "unit_of_measure": "unidad",
                "supplier_id": 1,
                "category": "Electrónica",
                "active": True,
                "last_updated": datetime(2026, 5, 6, 10, 0, 0),
            }
        ],
        "stock_movements": [],
        "requests": [],
    }
    monkeypatch.setattr(inv_app, "initialize_database", lambda: None)
    monkeypatch.setattr(inv_app, "seed_items", lambda: None)
    monkeypatch.setattr(inv_app, "get_db", lambda: FakeConn(store))
    with TestClient(inv_app.app) as test_client:
        yield test_client


def test_health_and_list_items(client):
    health_response = client.get("/health")
    assert health_response.status_code == 200

    items_response = client.get("/items", headers={"user-name": "ops"})
    assert items_response.status_code == 200
    assert items_response.json()[0]["below_minimum"] is True


def test_update_stock_and_create_request(client):
    update_response = client.post(
        "/items/1/stock/update",
        params={"quantity_change": 3, "reason": "purchase_received"},
        headers={"user-name": "ops"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["new_quantity"] == 8

    request_response = client.post(
        "/solicitudes-logistica",
        params={"item_id": 1, "requested_quantity": 10, "reason": "restock"},
        headers={"user-name": "ops"},
    )
    assert request_response.status_code == 200
    assert request_response.json()["status"] == "pending"
