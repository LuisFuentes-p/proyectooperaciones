"""
Nomina Microservice
- Registro de empleados
- Control de asistencia
- Cálculo de nómina
- Historial de pagos
"""

from contextlib import contextmanager
from datetime import date, datetime
from typing import Optional

import os
import psycopg
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Nomina Service", version="1.0.0")

# =========================
# CORS
# =========================

allowed_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")

allow_credentials = os.getenv(
    "ALLOW_CREDENTIALS",
    "false"
).lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# DATABASE
# =========================

DATABASE_URL = os.getenv(
    "POSTGRES_URL",
    os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/transactions_db"
    ),
)


@contextmanager
def get_db():
    conn = psycopg.connect(DATABASE_URL)

    try:
        yield conn
    finally:
        conn.close()


# =========================
# DATABASE INIT
# =========================

def initialize_database():
    with get_db() as conn:
        with conn.cursor() as cur:

            # Employees
            cur.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id SERIAL PRIMARY KEY,
                    employee_code VARCHAR(50) UNIQUE NOT NULL,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255),
                    department VARCHAR(100),
                    position VARCHAR(100),
                    base_salary DECIMAL(12,2) NOT NULL,
                    commission_percentage DECIMAL(5,2) DEFAULT 0,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Attendance
            cur.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id SERIAL PRIMARY KEY,
                    employee_id INTEGER NOT NULL,
                    attendance_date DATE NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)

            # Payroll Runs
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payroll_runs (
                    id SERIAL PRIMARY KEY,
                    payroll_period VARCHAR(50) NOT NULL,
                    executed_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Payroll Payments
            cur.execute("""
                CREATE TABLE IF NOT EXISTS payroll_payments (
                    id SERIAL PRIMARY KEY,
                    payroll_run_id INTEGER NOT NULL,
                    employee_id INTEGER NOT NULL,
                    base_salary DECIMAL(12,2) NOT NULL,
                    commission_amount DECIMAL(12,2) DEFAULT 0,
                    deductions DECIMAL(12,2) DEFAULT 0,
                    total_payment DECIMAL(12,2) NOT NULL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (payroll_run_id) REFERENCES payroll_runs(id),
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)

            # Indexes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_attendance_employee
                ON attendance(employee_id)
            """)

            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_payroll_employee
                ON payroll_payments(employee_id)
            """)

        conn.commit()


# =========================
# SEED DATA
# =========================

def seed_data():
    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT COUNT(*) FROM employees")

            if cur.fetchone()[0] == 0:

                cur.execute("""
                    INSERT INTO employees
                    (
                        employee_code,
                        full_name,
                        email,
                        department,
                        position,
                        base_salary,
                        commission_percentage
                    )
                    VALUES
                    (
                        'EMP-001',
                        'Juan Perez',
                        'juan@empresa.com',
                        'Ventas',
                        'Ejecutivo Comercial',
                        25000,
                        5
                    ),
                    (
                        'EMP-002',
                        'Maria Lopez',
                        'maria@empresa.com',
                        'RH',
                        'Analista RH',
                        18000,
                        0
                    ),
                    (
                        'EMP-003',
                        'Carlos Ramirez',
                        'carlos@empresa.com',
                        'Logistica',
                        'Supervisor',
                        22000,
                        2
                    )
                """)

        conn.commit()


@app.on_event("startup")
def startup():
    initialize_database()
    seed_data()


# =========================
# HELPERS
# =========================

def validate_user(user_name: Optional[str]):
    if not user_name or not user_name.strip():
        raise HTTPException(
            status_code=403,
            detail="User not identified"
        )


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "nomina"
    }


# =========================
# EMPLOYEES
# =========================

@app.get("/employees")
def list_employees(
    user_name: str = Header(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    validate_user(user_name)

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    employee_code,
                    full_name,
                    email,
                    department,
                    position,
                    base_salary,
                    commission_percentage,
                    active,
                    created_at
                FROM employees
                WHERE active = TRUE
                ORDER BY id ASC
                LIMIT %s OFFSET %s
            """, (limit, skip))

            employees = []

            for row in cur.fetchall():
                employees.append({
                    "id": row[0],
                    "employee_code": row[1],
                    "full_name": row[2],
                    "email": row[3],
                    "department": row[4],
                    "position": row[5],
                    "base_salary": float(row[6]),
                    "commission_percentage": float(row[7]),
                    "active": row[8],
                    "created_at": row[9].isoformat() if row[9] else None,
                })

            return employees


@app.post("/employees")
def create_employee(
    payload: dict,
    user_name: str = Header(None),
):
    validate_user(user_name)

    required_fields = [
        "employee_code",
        "full_name",
        "base_salary",
    ]

    for field in required_fields:
        if field not in payload:
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required"
            )

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO employees
                (
                    employee_code,
                    full_name,
                    email,
                    department,
                    position,
                    base_salary,
                    commission_percentage
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                RETURNING id, created_at
            """, (
                payload["employee_code"],
                payload["full_name"],
                payload.get("email"),
                payload.get("department"),
                payload.get("position"),
                payload["base_salary"],
                payload.get("commission_percentage", 0),
            ))

            row = cur.fetchone()

        conn.commit()

    return {
        "id": row[0],
        "created_at": row[1].isoformat() if row[1] else None,
    }


# =========================
# ATTENDANCE
# =========================

@app.post("/attendance")
def register_attendance(
    payload: dict,
    user_name: str = Header(None),
):
    validate_user(user_name)

    employee_id = payload.get("employee_id")
    attendance_date = payload.get("attendance_date")
    status = payload.get("status")

    if not employee_id:
        raise HTTPException(400, "employee_id required")

    if not attendance_date:
        raise HTTPException(400, "attendance_date required")

    if status not in ("present", "absent", "late"):
        raise HTTPException(400, "invalid status")

    with get_db() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO attendance
                (
                    employee_id,
                    attendance_date,
                    status,
                    notes
                )
                VALUES (%s,%s,%s,%s)
                RETURNING id
            """, (
                employee_id,
                attendance_date,
                status,
                payload.get("notes"),
            ))

            row = cur.fetchone()

        conn.commit()

    return {
        "id": row[0],
        "employee_id": employee_id,
        "status": status,
    }


@app.get("/attendance")
def list_attendance(
    user_name: str = Header(None),
    employee_id: Optional[int] = Query(None),
):
    validate_user(user_name)

    with get_db() as conn:
        with conn.cursor() as cur:

            if employee_id:
                cur.execute("""
                    SELECT
                        id,
                        employee_id,
                        attendance_date,
                        status,
                        notes
                    FROM attendance
                    WHERE employee_id = %s
                    ORDER BY attendance_date DESC
                """, (employee_id,))
            else:
                cur.execute("""
                    SELECT
                        id,
                        employee_id,
                        attendance_date,
                        status,
                        notes
                    FROM attendance
                    ORDER BY attendance_date DESC
                """)

            records = []

            for row in cur.fetchall():
                records.append({
                    "id": row[0],
                    "employee_id": row[1],
                    "attendance_date": row[2].isoformat(),
                    "status": row[3],
                    "notes": row[4],
                })

            return records


# =========================
# PAYROLL
# =========================

@app.post("/payroll/run")
def execute_payroll(
    payroll_period: str,
    user_name: str = Header(None),
):
    validate_user(user_name)

    with get_db() as conn:
        with conn.cursor() as cur:

            # Create payroll run
            cur.execute("""
                INSERT INTO payroll_runs
                (
                    payroll_period,
                    executed_by
                )
                VALUES (%s,%s)
                RETURNING id
            """, (
                payroll_period,
                user_name,
            ))

            payroll_run_id = cur.fetchone()[0]

            # Get employees
            cur.execute("""
                SELECT
                    id,
                    base_salary,
                    commission_percentage
                FROM employees
                WHERE active = TRUE
            """)

            employees = cur.fetchall()

            payments = []

            for employee in employees:

                employee_id = employee[0]
                base_salary = float(employee[1])
                commission_percentage = float(employee[2])

                commission_amount = (
                    base_salary * commission_percentage / 100
                )

                deductions = 0

                total_payment = (
                    base_salary +
                    commission_amount -
                    deductions
                )

                cur.execute("""
                    INSERT INTO payroll_payments
                    (
                        payroll_run_id,
                        employee_id,
                        base_salary,
                        commission_amount,
                        deductions,
                        total_payment
                    )
                    VALUES (%s,%s,%s,%s,%s,%s)
                    RETURNING id
                """, (
                    payroll_run_id,
                    employee_id,
                    base_salary,
                    commission_amount,
                    deductions,
                    total_payment,
                ))

                payment_id = cur.fetchone()[0]

                payments.append({
                    "payment_id": payment_id,
                    "employee_id": employee_id,
                    "total_payment": total_payment,
                })

        conn.commit()

    return {
        "payroll_run_id": payroll_run_id,
        "payroll_period": payroll_period,
        "payments_generated": len(payments),
        "payments": payments,
    }


# =========================
# PAYMENTS HISTORY
# =========================

@app.get("/payroll/history")
def payroll_history(
    user_name: str = Header(None),
    employee_id: Optional[int] = Query(None),
):
    validate_user(user_name)

    with get_db() as conn:
        with conn.cursor() as cur:

            if employee_id:

                cur.execute("""
                    SELECT
                        pp.id,
                        pp.employee_id,
                        e.full_name,
                        pp.base_salary,
                        pp.commission_amount,
                        pp.deductions,
                        pp.total_payment,
                        pp.payment_date
                    FROM payroll_payments pp
                    JOIN employees e
                    ON pp.employee_id = e.id
                    WHERE pp.employee_id = %s
                    ORDER BY pp.payment_date DESC
                """, (employee_id,))

            else:

                cur.execute("""
                    SELECT
                        pp.id,
                        pp.employee_id,
                        e.full_name,
                        pp.base_salary,
                        pp.commission_amount,
                        pp.deductions,
                        pp.total_payment,
                        pp.payment_date
                    FROM payroll_payments pp
                    JOIN employees e
                    ON pp.employee_id = e.id
                    ORDER BY pp.payment_date DESC
                """)

            payments = []

            for row in cur.fetchall():
                payments.append({
                    "payment_id": row[0],
                    "employee_id": row[1],
                    "employee_name": row[2],
                    "base_salary": float(row[3]),
                    "commission_amount": float(row[4]),
                    "deductions": float(row[5]),
                    "total_payment": float(row[6]),
                    "payment_date": row[7].isoformat() if row[7] else None,
                })

            return payments