from __future__ import annotations

from datetime import datetime
import unittest

from fastapi.testclient import TestClient

import app.main as nomina_app


class FakeCursor:
    def __init__(self, store: dict):
        self.store = store
        self._result = None
        self._results = []

    def execute(self, query: str, params=None):
        normalized = " ".join(query.split()).lower()

        # =========================================================
        # EMPLOYEES
        # =========================================================

        if normalized.startswith(
            "select id, employee_code, full_name, email, department, position, base_salary, commission_percentage, active, created_at from employees where active = true"
        ):
            rows = []

            for employee in self.store["employees"]:
                if employee["active"]:
                    rows.append((
                        employee["id"],
                        employee["employee_code"],
                        employee["full_name"],
                        employee["email"],
                        employee["department"],
                        employee["position"],
                        employee["base_salary"],
                        employee["commission_percentage"],
                        employee["active"],
                        employee["created_at"],
                    ))

            self._results = rows

        elif normalized.startswith(
            "insert into employees"
        ):
            employee_id = len(self.store["employees"]) + 1

            employee = {
                "id": employee_id,
                "employee_code": params[0],
                "full_name": params[1],
                "email": params[2],
                "department": params[3],
                "position": params[4],
                "base_salary": float(params[5]),
                "commission_percentage": float(params[6]),
                "active": True,
                "created_at": datetime(2026, 5, 6, 12, 0, 0),
            }

            self.store["employees"].append(employee)

            self._result = (
                employee["id"],
                employee["created_at"],
            )

        # =========================================================
        # ATTENDANCE
        # =========================================================

        elif normalized.startswith(
            "insert into attendance"
        ):
            attendance_id = len(self.store["attendance"]) + 1

            record = {
                "id": attendance_id,
                "employee_id": params[0],
                "attendance_date": params[1],
                "status": params[2],
                "notes": params[3],
            }

            self.store["attendance"].append(record)

            self._result = (attendance_id,)

        elif normalized.startswith(
            "select id, employee_id, attendance_date, status, notes from attendance where employee_id = %s"
        ):
            employee_id = params[0]

            rows = []

            for record in self.store["attendance"]:
                if record["employee_id"] == employee_id:
                    rows.append((
                        record["id"],
                        record["employee_id"],
                        record["attendance_date"],
                        record["status"],
                        record["notes"],
                    ))

            self._results = rows

        elif normalized.startswith(
            "select id, employee_id, attendance_date, status, notes from attendance order by attendance_date desc"
        ):
            rows = []

            for record in self.store["attendance"]:
                rows.append((
                    record["id"],
                    record["employee_id"],
                    record["attendance_date"],
                    record["status"],
                    record["notes"],
                ))

            self._results = rows

        # =========================================================
        # PAYROLL
        # =========================================================

        elif normalized.startswith(
            "insert into payroll_runs"
        ):
            payroll_run_id = len(self.store["payroll_runs"]) + 1

            payroll_run = {
                "id": payroll_run_id,
                "payroll_period": params[0],
                "executed_by": params[1],
            }

            self.store["payroll_runs"].append(payroll_run)

            self._result = (payroll_run_id,)

        elif normalized.startswith(
            "select id, base_salary, commission_percentage from employees where active = true"
        ):
            rows = []

            for employee in self.store["employees"]:
                if employee["active"]:
                    rows.append((
                        employee["id"],
                        employee["base_salary"],
                        employee["commission_percentage"],
                    ))

            self._results = rows

        elif normalized.startswith(
            "insert into payroll_payments"
        ):
            payment_id = len(self.store["payments"]) + 1

            payment = {
                "id": payment_id,
                "payroll_run_id": params[0],
                "employee_id": params[1],
                "base_salary": float(params[2]),
                "commission_amount": float(params[3]),
                "deductions": float(params[4]),
                "total_payment": float(params[5]),
                "payment_date": datetime(2026, 5, 6, 12, 30, 0),
            }

            self.store["payments"].append(payment)

            self._result = (payment_id,)

        # =========================================================
        # PAYROLL HISTORY
        # =========================================================

        elif normalized.startswith(
            "select pp.id, pp.employee_id, e.full_name, pp.base_salary, pp.commission_amount, pp.deductions, pp.total_payment, pp.payment_date from payroll_payments pp join employees e on pp.employee_id = e.id where pp.employee_id = %s"
        ):
            employee_id = params[0]

            rows = []

            for payment in self.store["payments"]:

                if payment["employee_id"] == employee_id:

                    employee = next(
                        e for e in self.store["employees"]
                        if e["id"] == employee_id
                    )

                    rows.append((
                        payment["id"],
                        payment["employee_id"],
                        employee["full_name"],
                        payment["base_salary"],
                        payment["commission_amount"],
                        payment["deductions"],
                        payment["total_payment"],
                        payment["payment_date"],
                    ))

            self._results = rows

        elif normalized.startswith(
            "select pp.id, pp.employee_id, e.full_name, pp.base_salary, pp.commission_amount, pp.deductions, pp.total_payment, pp.payment_date from payroll_payments pp join employees e on pp.employee_id = e.id order by pp.payment_date desc"
        ):
            rows = []

            for payment in self.store["payments"]:

                employee = next(
                    e for e in self.store["employees"]
                    if e["id"] == payment["employee_id"]
                )

                rows.append((
                    payment["id"],
                    payment["employee_id"],
                    employee["full_name"],
                    payment["base_salary"],
                    payment["commission_amount"],
                    payment["deductions"],
                    payment["total_payment"],
                    payment["payment_date"],
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
    def __init__(self, store: dict):
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


class NominaServiceTests(unittest.TestCase):

    def setUp(self):

        self.store = {
            "employees": [
                {
                    "id": 1,
                    "employee_code": "EMP-001",
                    "full_name": "Juan Perez",
                    "email": "juan@empresa.com",
                    "department": "Ventas",
                    "position": "Ejecutivo",
                    "base_salary": 25000.0,
                    "commission_percentage": 5.0,
                    "active": True,
                    "created_at": datetime(2026, 5, 6, 10, 0, 0),
                }
            ],
            "attendance": [],
            "payroll_runs": [],
            "payments": [],
        }

        self._orig_get_db = nomina_app.get_db
        self._orig_seed_data = nomina_app.seed_data

        nomina_app.get_db = lambda: FakeConn(self.store)
        nomina_app.seed_data = lambda: None

        self.client = TestClient(nomina_app.app)

    def tearDown(self):

        self.client.close()

        nomina_app.get_db = self._orig_get_db
        nomina_app.seed_data = self._orig_seed_data

    # =========================================================
    # HEALTH
    # =========================================================

    def test_health(self):

        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["service"], "nomina")

    # =========================================================
    # EMPLOYEES
    # =========================================================

    def test_list_employees(self):

        response = self.client.get(
            "/employees",
            headers={"user-name": "admin"},
        )

        self.assertEqual(response.status_code, 200)

        employees = response.json()

        self.assertEqual(len(employees), 1)
        self.assertEqual(
            employees[0]["employee_code"],
            "EMP-001"
        )

    def test_create_employee(self):

        response = self.client.post(
            "/employees",
            headers={"user-name": "admin"},
            json={
                "employee_code": "EMP-002",
                "full_name": "Maria Lopez",
                "base_salary": 18000,
                "department": "RH",
            },
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["id"], 2)

    # =========================================================
    # ATTENDANCE
    # =========================================================

    def test_register_attendance(self):

        response = self.client.post(
            "/attendance",
            headers={"user-name": "admin"},
            json={
                "employee_id": 1,
                "attendance_date": "2026-05-06",
                "status": "present",
                "notes": "On time",
            },
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["employee_id"], 1)
        self.assertEqual(body["status"], "present")

    def test_list_attendance(self):

        self.store["attendance"].append({
            "id": 1,
            "employee_id": 1,
            "attendance_date": datetime(2026, 5, 6).date(),
            "status": "present",
            "notes": "On time",
        })

        response = self.client.get(
            "/attendance",
            headers={"user-name": "admin"},
        )

        self.assertEqual(response.status_code, 200)

        records = response.json()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["status"], "present")

    # =========================================================
    # PAYROLL
    # =========================================================

    def test_execute_payroll(self):

        response = self.client.post(
            "/payroll/run",
            headers={"user-name": "admin"},
            params={"payroll_period": "2026-05"},
        )

        self.assertEqual(response.status_code, 200)

        body = response.json()

        self.assertEqual(body["payments_generated"], 1)
        self.assertEqual(body["payments"][0]["employee_id"], 1)

    def test_payroll_history(self):

        self.store["payments"].append({
            "id": 1,
            "payroll_run_id": 1,
            "employee_id": 1,
            "base_salary": 25000.0,
            "commission_amount": 1250.0,
            "deductions": 0.0,
            "total_payment": 26250.0,
            "payment_date": datetime(2026, 5, 6, 12, 30, 0),
        })

        response = self.client.get(
            "/payroll/history",
            headers={"user-name": "admin"},
        )

        self.assertEqual(response.status_code, 200)

        history = response.json()

        self.assertEqual(len(history), 1)
        self.assertEqual(
            history[0]["employee_name"],
            "Juan Perez"
        )
        self.assertEqual(
            history[0]["total_payment"],
            26250.0
        )