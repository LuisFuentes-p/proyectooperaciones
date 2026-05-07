from __future__ import annotations

from datetime import datetime
import unittest

from fastapi.testclient import TestClient

import app.main as log_app


# =============================================================================
# FAKE CURSOR
# =============================================================================

class FakeCursor:

    def __init__(self, store: dict[str, list[dict]]):

        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):

        normalized = " ".join(query.split()).lower()

        # =========================================================================
        # ITEMS BELOW MINIMUM
        # =========================================================================

        if (
            "from items i" in normalized
            and "quantity_on_hand < i.minimum_threshold" in normalized
        ):

            rows = [
                item
                for item in self.store["items"]
                if (
                    item["active"]
                    and item["quantity_on_hand"]
                    < item["minimum_threshold"]
                )
            ]

            self._results = [
                self._item_below_row(item)
                for item in rows
            ]

        # =========================================================================
        # STOCKOUT ITEMS
        # =========================================================================

        elif (
            "quantity_on_hand = 0" in normalized
            and "from items i" in normalized
        ):

            rows = [
                item
                for item in self.store["items"]
                if (
                    item["active"]
                    and item["quantity_on_hand"] == 0
                )
            ]

            self._results = [
                self._stockout_row(item)
                for item in rows
            ]

        # =========================================================================
        # DASHBOARD
        # =========================================================================

        elif "count(*) as total_items" in normalized:

            active_items = [
                item
                for item in self.store["items"]
                if item["active"]
            ]

            total_items = len(active_items)

            stockout_count = sum(
                1
                for item in active_items
                if item["quantity_on_hand"] == 0
            )

            below_minimum_count = sum(
                1
                for item in active_items
                if (
                    item["quantity_on_hand"]
                    < item["minimum_threshold"]
                )
            )

            total_value = sum(
                item["quantity_on_hand"]
                * item["unit_cost"]
                for item in active_items
            )

            self._result = (
                total_items,
                stockout_count,
                below_minimum_count,
                total_value,
            )

        # =========================================================================
        # ITEMS FOR ALERT CHECK
        # =========================================================================

        elif (
            "from items" in normalized
            and "quantity_on_hand < minimum_threshold" in normalized
        ):

            rows = [
                item
                for item in self.store["items"]
                if (
                    item["active"]
                    and item["quantity_on_hand"]
                    < item["minimum_threshold"]
                )
            ]

            self._results = [
                (
                    item["id"],
                    item["quantity_on_hand"],
                    item["minimum_threshold"],
                    item["reorder_quantity"],
                )
                for item in rows
            ]

        # =========================================================================
        # EXISTING BELOW MINIMUM ALERT
        # =========================================================================

        elif (
            "from stock_alerts" in normalized
            and "alert_type = 'below_minimum'" in normalized
        ):

            item_id = params[0]

            row = next(
                (
                    alert
                    for alert in self.store["alerts"]
                    if (
                        alert["item_id"] == item_id
                        and not alert["resolved"]
                        and alert["alert_type"]
                        == "below_minimum"
                    )
                ),
                None
            )

            self._result = (
                (row["id"],)
                if row
                else None
            )

        # =========================================================================
        # INSERT ALERT
        # =========================================================================

        elif "insert into stock_alerts" in normalized:

            alert_id = len(self.store["alerts"]) + 1

            self.store["alerts"].append({
                "id": alert_id,
                "item_id": params[0],
                "alert_type": params[1],
                "current_quantity": params[2],
                "threshold": params[3],
                "severity": params[4],
                "acknowledged": False,
                "resolved": False,
                "created_at": datetime(
                    2026,
                    5,
                    6,
                    12,
                    0,
                    0
                ),
            })

        # =========================================================================
        # EXISTING REQUEST
        # =========================================================================

        elif (
            "from solicitudes_logistica" in normalized
            and "status in ('pending', 'approved')" in normalized
        ):

            item_id = params[0]

            row = next(
                (
                    request
                    for request in self.store["requests"]
                    if (
                        request["item_id"] == item_id
                        and request["status"]
                        in {"pending", "approved"}
                    )
                ),
                None
            )

            self._result = (
                (row["id"],)
                if row
                else None
            )

        # =========================================================================
        # INSERT REQUEST
        # =========================================================================

        elif "insert into solicitudes_logistica" in normalized:

            request_id = len(self.store["requests"]) + 1

            self.store["requests"].append({
                "id": request_id,
                "item_id": params[0],
                "requested_quantity": params[1],
                "reason": params[2],
                "priority": params[3],
                "status": "pending",
                "created_at": datetime(
                    2026,
                    5,
                    6,
                    12,
                    0,
                    0
                ),
            })

        else:

            self._result = None
            self._results = []

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _item_below_row(self, item: dict):

        supplier_name = next(
            (
                supplier["name"]
                for supplier in self.store["suppliers"]
                if supplier["id"] == item["supplier_id"]
            ),
            None
        )

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

        supplier_name = next(
            (
                supplier["name"]
                for supplier in self.store["suppliers"]
                if supplier["id"] == item["supplier_id"]
            ),
            None
        )

        return (
            item["id"],
            item["sku"],
            item["name"],
            item["reorder_quantity"],
            supplier_name,
            item["minimum_threshold"],
        )

    # =========================================================================
    # FETCH
    # =========================================================================

    def fetchone(self):
        return self._result

    def fetchall(self):
        return self._results

    # =========================================================================
    # CONTEXT
    # =========================================================================

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


# =============================================================================
# FAKE CONNECTION
# =============================================================================

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


# =============================================================================
# TESTS
# =============================================================================

class LogisticaServiceTests(unittest.TestCase):

    def setUp(self):

        self.store = {
            "suppliers": [
                {
                    "id": 1,
                    "name": "TechSupply Inc"
                }
            ],

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
                    "last_updated": datetime(
                        2026,
                        5,
                        6,
                        10,
                        0,
                        0
                    ),
                }
            ],

            "alerts": [],

            "requests": [],
        }

        self._orig_get_db = log_app.get_db

        log_app.get_db = (
            lambda: FakeConn(self.store)
        )

        self.client = TestClient(log_app.app)

    def tearDown(self):

        self.client.close()

        log_app.get_db = (
            self._orig_get_db
        )

    # =========================================================================
    # ITEMS BELOW MINIMUM + DASHBOARD
    # =========================================================================

    def test_items_below_minimum_and_dashboard(self):

        response = self.client.get(
            "/monitor/items-below-minimum",
            headers={
                "user-name": "ops"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(len(data), 1)

        self.assertTrue(
            data[0]["needs_reorder"]
        )

        dashboard = self.client.get(
            "/monitor/stock-status-dashboard",
            headers={
                "user-name": "ops"
            }
        )

        self.assertEqual(
            dashboard.status_code,
            200
        )

        dashboard_data = dashboard.json()

        self.assertEqual(
            dashboard_data["below_minimum_count"],
            1
        )

    # =========================================================================
    # ALERT GENERATION
    # =========================================================================

    def test_alert_generation(self):

        response = self.client.post(
            "/monitor/check-and-alert",
            headers={
                "user-name": "ops"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            data["alerts_created"],
            1
        )

        self.assertEqual(
            len(self.store["alerts"]),
            1
        )

        self.assertEqual(
            len(self.store["requests"]),
            1
        )

        self.assertEqual(
            self.store["alerts"][0]["alert_type"],
            "below_minimum"
        )