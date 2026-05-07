from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
import pytest

import app.main as log_app


class FakeCursor:
    def __init__(self, store: dict[str, list[dict]]):
        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("select i.id, i.sku, i.name, i.quantity_on_hand, i.minimum_threshold, i.reorder_quantity, s.name as supplier_name, i.unit_cost from items i left join suppliers s on i.supplier_id = s.id where i.quantity_on_hand < i.minimum_threshold and i.active = true order by (i.minimum_threshold - i.quantity_on_hand) desc"):
            rows = [item for item in self.store["items"] if item["active"] and item["quantity_on_hand"] < item["minimum_threshold"]]
            self._results = [self._item_below_row(item) for item in rows]
        elif normalized.startswith("select i.id, i.sku, i.name, i.reorder_quantity, s.name as supplier_name, i.minimum_threshold from items i left join suppliers s on i.supplier_id = s.id where i.quantity_on_hand = 0 and i.active = true order by i.last_updated desc"):
            rows = [item for item in self.store["items"] if item["active"] and item["quantity_on_hand"] == 0]
            self._results = [self._stockout_row(item) for item in rows]
        elif normalized.startswith("select count(*) as total_items"):
            active_items = [item for item in self.store["items"] if item["active"]]
            total_items = len(active_items)
            stockout_count = sum(1 for item in active_items if item["quantity_on_hand"] == 0)
            below_minimum_count = sum(1 for item in active_items if item["quantity_on_hand"] < item["minimum_threshold"])
            total_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in active_items)
            self._result = (total_items, stockout_count, below_minimum_count, total_value)
        elif normalized.startswith("select id, quantity_on_hand, minimum_threshold, reorder_quantity from items where quantity_on_hand < minimum_threshold and active = true"):
            rows = [item for item in self.store["items"] if item["active"] and item["quantity_on_hand"] < item["minimum_threshold"]]
            self._results = [(item["id"], item["quantity_on_hand"], item["minimum_threshold"], item["reorder_quantity"]) for item in rows]
        elif normalized.startswith("select id from stock_alerts where item_id = %s and resolved = false and alert_type = 'below_minimum'"):
            item_id = params[0]
            row = next((alert for alert in self.store["alerts"] if alert["item_id"] == item_id and not alert["resolved"] and alert["alert_type"] == "below_minimum"), None)
            self._result = (row["id"],) if row else None
        elif normalized.startswith("insert into stock_alerts"):
            alert_id = len(self.store["alerts"]) + 1
            self.store["alerts"].append(
                {
                    "id": alert_id,
                    "item_id": params[0],
                    "alert_type": params[1],
                    "current_quantity": params[2],
                    "threshold": params[3],
                    "severity": params[4],
                    "acknowledged": False,
                    "resolved": False,
                    "created_at": datetime(2026, 5, 6, 12, 0, 0),
                }
            )
        elif normalized.startswith("select id from solicitudes_logistica where item_id = %s and (status = 'pending' or status = 'approved')"):
            item_id = params[0]
            row = next((request for request in self.store["requests"] if request["item_id"] == item_id and request["status"] in {"pending", "approved"}), None)
            self._result = (row["id"],) if row else None
        elif normalized.startswith("insert into solicitudes_logistica"):
            request_id = len(self.store["requests"]) + 1
            self.store["requests"].append(
                {
                    "id": request_id,
                    "item_id": params[0],
                    "requested_quantity": params[1],
                    "reason": params[2],
                    "priority": params[3],
                    "status": "pending",
                    "created_at": datetime(2026, 5, 6, 12, 0, 0),
                }
            )
        else:
            self._result = None
            self._results = []

    def _item_below_row(self, item: dict):
        supplier_name = next((supplier["name"] for supplier in self.store["suppliers"] if supplier["id"] == item["supplier_id"]), None)
        return (
            item["id"],
            item["sku"],
            item["name"],
            item["quantity_on_hand"],
            item["minimum_threshold"],
            item["reorder_quantity"],
            supplier_name,
            item["unit_cost"],
        )

    def _stockout_row(self, item: dict):
        supplier_name = next((supplier["name"] for supplier in self.store["suppliers"] if supplier["id"] == item["supplier_id"]), None)
        return (
            item["id"],
            item["sku"],
            item["name"],
            item["reorder_quantity"],
            supplier_name,
            item["minimum_threshold"],
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
        "suppliers": [{"id": 1, "name": "TechSupply Inc"}],
        "items": [
            {
                "id": 1,
                "sku": "SKU-001",
                "name": "Laptop",
                "quantity_on_hand": 2,
                "minimum_threshold": 5,
                "reorder_quantity": 10,
                "supplier_id": 1,
                "unit_cost": 1200.0,
                "active": True,
                "last_updated": datetime(2026, 5, 6, 10, 0, 0),
            }
        ],
        "alerts": [],
        "requests": [],
    }
    monkeypatch.setattr(log_app, "get_db", lambda: FakeConn(store))
    with TestClient(log_app.app) as test_client:
        yield test_client


def test_items_below_minimum_and_dashboard(client):
    response = client.get("/monitor/items-below-minimum", headers={"user-name": "ops"})
    assert response.status_code == 200
    assert response.json()[0]["needs_reorder"] is True

    dashboard = client.get("/monitor/stock-status-dashboard", headers={"user-name": "ops"})
    assert dashboard.status_code == 200
    assert dashboard.json()["below_minimum_count"] == 1


def test_alert_generation(client):
    response = client.post("/monitor/check-and-alert", headers={"user-name": "ops"})
    assert response.status_code == 200
    assert response.json()["alerts_created"] == 1
