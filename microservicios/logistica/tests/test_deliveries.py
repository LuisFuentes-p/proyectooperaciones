from datetime import datetime
import unittest

from fastapi.testclient import TestClient

import app.main as logistica_app


class FakeCursor:

    def __init__(self, store):
        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):

        normalized = " ".join(query.split()).lower()

        # CREATE DELIVERY
        if "insert into deliveries" in normalized:

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

            self._result = (
                record["id"],
                record["status"],
                record["created_at"]
            )

        # ASSIGN DELIVERY
        elif "update deliveries set assigned_to" in normalized:

            assigned_to, vehicle, d_id = params

            record = next(
                (
                    r for r in self.store["deliveries"]
                    if r["id"] == d_id
                ),
                None
            )

            if record:

                record["assigned_to"] = assigned_to
                record["vehicle"] = vehicle
                record["assigned_at"] = datetime(
                    2026, 5, 6, 12, 5, 0
                )

                self._result = (
                    record["id"],
                    record["assigned_to"],
                    record["vehicle"],
                )

            else:
                self._result = None

        # UPDATE DELIVERED
        elif (
            "update deliveries set status = %s, delivered_at = now()"
            in normalized
        ):

            status, d_id = params

            record = next(
                (
                    r for r in self.store["deliveries"]
                    if r["id"] == d_id
                ),
                None
            )

            if record:

                record["status"] = status
                record["delivered_at"] = datetime(
                    2026, 5, 6, 12, 10, 0
                )

                self._result = (
                    record["id"],
                    record["status"],
                    record["delivered_at"],
                )

            else:
                self._result = None

        # UPDATE STATUS
        elif (
            "update deliveries set status = %s where id = %s"
            in normalized
        ):

            status, d_id = params

            record = next(
                (
                    r for r in self.store["deliveries"]
                    if r["id"] == d_id
                ),
                None
            )

            if record:

                record["status"] = status

                self._result = (
                    record["id"],
                    record["status"],
                )

            else:
                self._result = None

        # GET DELIVERY
        elif (
            "from deliveries where id = %s"
            in normalized
        ):

            d_id = params[0]

            record = next(
                (
                    r for r in self.store["deliveries"]
                    if r["id"] == d_id
                ),
                None
            )

            if record:

                self._result = (
                    record["id"],
                    record["order_id"],
                    record["delivery_address"],
                    record["assigned_to"],
                    record["vehicle"],
                    record["status"],
                    record["created_by"],
                    record["created_at"],
                    record["assigned_at"],
                    record["delivered_at"],
                )

            else:
                self._result = None

        # LIST DELIVERIES
        elif "from deliveries order by created_at desc" in normalized:

            rows = []

            for r in self.store["deliveries"]:

                rows.append((
                    r["id"],
                    r["order_id"],
                    r["delivery_address"],
                    r["assigned_to"],
                    r["vehicle"],
                    r["status"],
                ))

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
        return False


class LogisticaDeliveryTests(unittest.TestCase):

    def setUp(self):

        self.store = {
            "deliveries": []
        }

        self._orig_get_db = logistica_app.get_db

        logistica_app.get_db = (
            lambda: FakeConn(self.store)
        )

        self.client = TestClient(logistica_app.app)

    def tearDown(self):

        self.client.close()

        logistica_app.get_db = (
            self._orig_get_db
        )

    def test_create_assign_and_update_delivery_flow(self):

        health = self.client.get("/health")

        self.assertEqual(
            health.status_code,
            200
        )

        # CREATE
        response = self.client.post(
            "/deliveries",
            json={
                "order_id": 10,
                "delivery_address": "Calle Falsa 123"
            },
            headers={
                "user-name": "logistica"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        data = response.json()

        self.assertEqual(
            data["status"],
            "pending"
        )

        delivery_id = data["id"]

        # ASSIGN
        response = self.client.patch(
            f"/deliveries/{delivery_id}/assign",
            json={
                "assigned_to": "Juan",
                "vehicle": "Van-01"
            },
            headers={
                "user-name": "logistica"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json()["assigned_to"],
            "Juan"
        )

        # IN TRANSIT
        response = self.client.patch(
            f"/deliveries/{delivery_id}/status",
            json={
                "status": "in_transit"
            },
            headers={
                "user-name": "logistica"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json()["status"],
            "in_transit"
        )

        # DELIVERED
        response = self.client.patch(
            f"/deliveries/{delivery_id}/status",
            json={
                "status": "delivered"
            },
            headers={
                "user-name": "logistica"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        self.assertEqual(
            response.json()["status"],
            "delivered"
        )

        # GET DELIVERY
        response = self.client.get(
            f"/deliveries/{delivery_id}",
            headers={
                "user-name": "logistica"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        delivery = response.json()

        self.assertEqual(
            delivery["id"],
            delivery_id
        )

        self.assertEqual(
            delivery["status"],
            "delivered"
        )

        # LIST
        response = self.client.get(
            "/deliveries",
            headers={
                "user-name": "logistica"
            }
        )

        self.assertEqual(
            response.status_code,
            200
        )

        deliveries = response.json()

        self.assertTrue(
            any(
                d["id"] == delivery_id
                for d in deliveries
            )
        )