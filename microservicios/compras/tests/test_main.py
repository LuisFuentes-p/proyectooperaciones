from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
import pytest

import app.main as compras_app


class FakeCursor:
    def __init__(self, store: dict[str, list[dict]]):
        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()
        if normalized.startswith("select sku, name from items where id = %s"):
            item_id = params[0]
            item = next((row for row in self.store["items"] if row["id"] == item_id), None)
            self._result = (item["sku"], item["name"]) if item else None
        elif normalized.startswith("select name, contact_email from suppliers where id = %s"):
            supplier_id = params[0]
            supplier = next((row for row in self.store["suppliers"] if row["id"] == supplier_id), None)
            self._result = (supplier["name"], supplier["contact_email"]) if supplier else None
        elif normalized.startswith("insert into purchase_orders"):
            po_id = len(self.store["purchase_orders"]) + 1
            record = {
                "id": po_id,
                "item_id": params[0],
                "supplier_id": params[1],
                "quantity": params[2],
                "unit_price": params[3],
                "total_amount": params[4],
                "expected_delivery_date": params[5],
                "requested_by": params[6],
                "status": "pending",
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
                "pdf_content": None,
                "pdf_filename": None,
            }
            self.store["purchase_orders"].append(record)
            self._result = (po_id, record["created_at"])
        elif normalized.startswith("update purchase_orders set pdf_content = %s, pdf_filename = %s where id = %s"):
            pdf_content, pdf_filename, po_id = params
            record = next(row for row in self.store["purchase_orders"] if row["id"] == po_id)
            record["pdf_content"] = pdf_content
            record["pdf_filename"] = pdf_filename
        elif normalized.startswith("select po.id, po.item_id, po.supplier_id") and "from purchase_orders po" in normalized:
            rows = []
            for po in self.store["purchase_orders"]:
                item = next(row for row in self.store["items"] if row["id"] == po["item_id"])
                supplier = next(row for row in self.store["suppliers"] if row["id"] == po["supplier_id"])
                rows.append(
                    (
                        po["id"],
                        po["item_id"],
                        po["supplier_id"],
                        po["quantity"],
                        po["unit_price"],
                        po["total_amount"],
                        po["status"],
                        po["created_at"],
                        po["expected_delivery_date"],
                        po["requested_by"],
                        item["sku"],
                        item["name"],
                        supplier["name"],
                    )
                )
            self._results = rows
        elif normalized.startswith("select pdf_content, pdf_filename from purchase_orders where id = %s"):
            po_id = params[0]
            record = next((row for row in self.store["purchase_orders"] if row["id"] == po_id), None)
            self._result = (record["pdf_content"], record["pdf_filename"]) if record else None
        elif normalized.startswith("select item_id, quantity, status from purchase_orders where id = %s"):
            po_id = params[0]
            record = next((row for row in self.store["purchase_orders"] if row["id"] == po_id), None)
            self._result = (record["item_id"], record["quantity"], record["status"]) if record else None
        elif normalized.startswith("update purchase_orders set status = %s") and "returning status" in normalized:
            new_status, _repeat_status, po_id = params
            record = next(row for row in self.store["purchase_orders"] if row["id"] == po_id)
            record["status"] = new_status
            record["received_at"] = datetime(2026, 5, 6, 12, 5, 0) if new_status == "received" else record.get("received_at")
            self._result = (new_status,)
        elif normalized.startswith("update items set quantity_on_hand = quantity_on_hand + %s"):
            quantity, item_id = params
            item = next(row for row in self.store["items"] if row["id"] == item_id)
            item["quantity_on_hand"] += quantity
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
        elif normalized.startswith("select sku, name, unit_price, quantity_on_hand from items where id = %s"):
            item_id = params[0]
            item = next((row for row in self.store["items"] if row["id"] == item_id), None)
            self._result = (item["sku"], item["name"], item["unit_price"], item["quantity_on_hand"]) if item else None
        elif normalized.startswith("select name, contact_email from customers where id = %s"):
            customer_id = params[0]
            customer = next((row for row in self.store["customers"] if row["id"] == customer_id), None)
            self._result = (customer["name"], customer["contact_email"]) if customer else None
        elif normalized.startswith("insert into sales_orders"):
            so_id = len(self.store["sales_orders"]) + 1
            record = {
                "id": so_id,
                "item_id": params[0],
                "customer_id": params[1],
                "quantity": params[2],
                "unit_price": params[3],
                "total_amount": params[4],
                "expected_delivery_date": params[5],
                "created_by": params[6],
                "status": "pending",
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
                "invoice_content": None,
                "invoice_filename": None,
            }
            self.store["sales_orders"].append(record)
            self._result = (so_id, record["created_at"])
        elif normalized.startswith("update items set quantity_on_hand = quantity_on_hand - %s"):
            quantity, item_id = params
            item = next(row for row in self.store["items"] if row["id"] == item_id)
            item["quantity_on_hand"] -= quantity
        elif normalized.startswith("update sales_orders set invoice_content = %s, invoice_filename = %s where id = %s"):
            invoice_content, invoice_filename, so_id = params
            record = next(row for row in self.store["sales_orders"] if row["id"] == so_id)
            record["invoice_content"] = invoice_content
            record["invoice_filename"] = invoice_filename
        elif normalized.startswith("select source_type, counterparty_type, counterparty_name, order_id, amount, status, created_at, reference_label from ("):
            rows = []
            for po in self.store["purchase_orders"]:
                supplier = next(row for row in self.store["suppliers"] if row["id"] == po["supplier_id"])
                rows.append(("purchase", "supplier", supplier["name"], po["id"], po["total_amount"], po["status"], po["created_at"], po["pdf_filename"]))
            for so in self.store["sales_orders"]:
                customer = next(row for row in self.store["customers"] if row["id"] == so["customer_id"])
                rows.append(("sale", "customer", customer["name"], so["id"], so["total_amount"], so["status"], so["created_at"], so["invoice_filename"]))
            for payment in self.store["payment_records"]:
                rows.append(("payment", payment["counterparty_type"], payment["counterparty_name"], payment["order_id"], payment["amount"], "recorded", payment["created_at"], payment["payment_method"]))
            self._results = rows
        elif normalized.startswith("select coalesce(sum(amount), 0) from payment_records"):
            total = sum(row["amount"] for row in self.store["payment_records"])
            self._result = (total,)
        elif normalized.startswith("insert into payment_records"):
            payment_id = len(self.store["payment_records"]) + 1
            record = {
                "id": payment_id,
                "order_type": params[0],
                "order_id": params[1],
                "counterparty_type": params[2],
                "counterparty_name": params[3],
                "amount": params[4],
                "payment_method": params[5],
                "notes": params[6],
                "created_by": params[7],
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
            }
            self.store["payment_records"].append(record)
            self._result = (payment_id, record["created_at"])
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
        "suppliers": [{"id": 1, "name": "TechSupply Inc", "contact_email": "sales@techsupply.com"}],
        "customers": [{"id": 1, "name": "ABC Retail Store", "contact_email": "manager@abc.com"}],
        "items": [
            {"id": 1, "sku": "SKU-001", "name": "Laptop", "quantity_on_hand": 10, "unit_cost": 1200.0, "unit_price": 1500.0},
        ],
        "purchase_orders": [],
        "sales_orders": [],
        "stock_movements": [],
        "payment_records": [],
    }
    monkeypatch.setattr(compras_app, "initialize_database", lambda: None)
    monkeypatch.setattr(compras_app, "seed_data", lambda: None)
    monkeypatch.setattr(compras_app, "get_db", lambda: FakeConn(store))
    monkeypatch.setattr(compras_app, "generate_purchase_order_pdf", lambda **kwargs: b"purchase-pdf")
    monkeypatch.setattr(compras_app, "generate_sales_invoice_pdf", lambda **kwargs: b"sales-pdf")
    with TestClient(compras_app.app) as test_client:
        yield test_client


def test_health_and_purchase_order_flow(client):
    response = client.get("/health")
    assert response.status_code == 200

    purchase_response = client.post(
        "/purchase-orders",
        json={"item_id": 1, "supplier_id": 1, "quantity": 2, "unit_price": 1000, "expected_delivery_days": 7},
        headers={"user-name": "compras"},
    )
    assert purchase_response.status_code == 200
    assert purchase_response.json()["status"] == "pending"


def test_sales_flow_and_summary(client):
    sales_response = client.post(
        "/sales-orders",
        json={"item_id": 1, "customer_id": 1, "quantity": 1, "expected_delivery_days": 3},
        headers={"user-name": "ventas"},
    )
    assert sales_response.status_code == 200
    assert sales_response.json()["total_amount"] == 1500.0

    summary_response = client.get("/stats/commercial-summary", headers={"user-name": "ventas"})
    assert summary_response.status_code == 200
    summary = summary_response.json()
    assert "purchase" in summary
    assert "sale" in summary
    assert summary["payment_total"] == 0.0
