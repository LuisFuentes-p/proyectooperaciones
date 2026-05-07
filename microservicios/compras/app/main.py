"""
Compras Microservice
- Manages suppliers, customers, items, purchase orders and sales orders
- Generates PDFs for purchase orders and sales invoices
- Tracks stock movements when orders are received or sold
- Stores transaction payments and commercial history
"""

from contextlib import contextmanager
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Optional
import os

import psycopg
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except ImportError:
    pass


app = FastAPI(title="Compras Service", version="2.0.0")

# CORS configuration driven by environment to avoid wildcard+credentials issues
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
allow_credentials = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/transactions_db"))


class SupplierIn(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None


class CustomerIn(BaseModel):
    name: str
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    customer_type: str = "retail"
    credit_limit: float = 0.0


class ItemIn(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    quantity_on_hand: int = 0
    minimum_threshold: int = 10
    reorder_quantity: int = 50
    unit_cost: float
    unit_price: float
    unit_of_measure: str = "unidad"
    supplier_id: Optional[int] = None
    category: Optional[str] = None


class PurchaseOrderIn(BaseModel):
    item_id: int
    supplier_id: int
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)
    expected_delivery_days: int = 7


class SalesOrderIn(BaseModel):
    item_id: int
    customer_id: int
    quantity: int = Field(gt=0)
    expected_delivery_days: int = 3


class PaymentIn(BaseModel):
    order_id: int
    amount: float = Field(gt=0)
    payment_method: str = "transfer"
    notes: Optional[str] = None


@contextmanager
def get_db():
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def initialize_database() -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS suppliers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    contact_email VARCHAR(255),
                    phone VARCHAR(20),
                    address TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100),
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    contact_email VARCHAR(255),
                    phone VARCHAR(20),
                    address TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100),
                    customer_type VARCHAR(50) DEFAULT 'retail',
                    credit_limit DECIMAL(12, 2) DEFAULT 0,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    sku VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
                    minimum_threshold INTEGER NOT NULL DEFAULT 10,
                    reorder_quantity INTEGER NOT NULL DEFAULT 50,
                    unit_cost DECIMAL(10, 2) NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL DEFAULT 0,
                    unit_of_measure VARCHAR(20) DEFAULT 'unidad',
                    supplier_id INTEGER,
                    category VARCHAR(100),
                    active BOOLEAN DEFAULT TRUE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
                """
            )
            cur.execute(
                "ALTER TABLE items ADD COLUMN IF NOT EXISTS unit_price DECIMAL(10, 2) NOT NULL DEFAULT 0"
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_amount DECIMAL(12, 2),
                    status VARCHAR(50) DEFAULT 'pending',
                    pdf_content BYTEA,
                    pdf_filename VARCHAR(255),
                    requested_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expected_delivery_date DATE,
                    received_at TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id),
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS sales_orders (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    customer_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_amount DECIMAL(12, 2),
                    status VARCHAR(50) DEFAULT 'pending',
                    invoice_content BYTEA,
                    invoice_filename VARCHAR(255),
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expected_delivery_date DATE,
                    shipped_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    movement_type VARCHAR(50) NOT NULL,
                    quantity INTEGER NOT NULL,
                    reason TEXT,
                    reference_id VARCHAR(100),
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_records (
                    id SERIAL PRIMARY KEY,
                    order_type VARCHAR(20) NOT NULL,
                    order_id INTEGER NOT NULL,
                    counterparty_type VARCHAR(20) NOT NULL,
                    counterparty_name VARCHAR(255) NOT NULL,
                    amount DECIMAL(12, 2) NOT NULL,
                    payment_method VARCHAR(50) NOT NULL,
                    notes TEXT,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        conn.commit()


def seed_data() -> None:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM suppliers")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    """
                    INSERT INTO suppliers (name, contact_email, phone, city, country)
                    VALUES
                        ('TechSupply Inc', 'sales@techsupply.com', '+1234567890', 'New York', 'USA'),
                        ('Industrial Parts Ltd', 'info@industrialparts.co.uk', '+442071234567', 'London', 'UK'),
                        ('Global Logistics Co', 'procurement@globallogistics.cn', '+86-10-1234-5678', 'Beijing', 'China')
                    """
                )

            cur.execute("SELECT COUNT(*) FROM customers")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    """
                    INSERT INTO customers (name, contact_email, phone, city, country, customer_type, credit_limit)
                    VALUES
                        ('ABC Retail Store', 'manager@abc.com', '+5551234567', 'Miami', 'USA', 'retail', 50000.00),
                        ('XYZ Distributor', 'sales@xyz.com', '+5559876543', 'Los Angeles', 'USA', 'wholesale', 100000.00),
                        ('Corner Shop', 'owner@corner.com', '+5551111111', 'Chicago', 'USA', 'retail', 20000.00)
                    """
                )

            cur.execute("SELECT COUNT(*) FROM items")
            if cur.fetchone()[0] == 0:
                cur.execute(
                    """
                    INSERT INTO items (
                        sku, name, description, quantity_on_hand, minimum_threshold,
                        reorder_quantity, unit_cost, unit_price, unit_of_measure, supplier_id, category
                    )
                    VALUES
                        ('SKU-001', 'Laptop Dell XPS 13', 'High-performance laptop', 8, 3, 10, 1200.00, 1499.99, 'unidad', 1, 'Electrónica'),
                        ('SKU-002', 'Monitor LG 27 inch', 'Full HD Monitor', 15, 5, 15, 250.00, 349.99, 'unidad', 1, 'Electrónica'),
                        ('SKU-003', 'Toner HP LaserJet', 'Black toner cartridge', 52, 10, 20, 45.00, 89.99, 'unidad', 2, 'Suministros'),
                        ('SKU-004', 'Papel A4 80gsm', 'Resma de papel blanco', 140, 30, 50, 8.50, 12.99, 'resma', 2, 'Suministros'),
                        ('SKU-005', 'Cable HDMI 2M', 'High-speed HDMI cable', 85, 20, 30, 5.99, 9.99, 'unidad', 1, 'Accesorios'),
                        ('SKU-006', 'Mouse Logitech', 'Ergonomic mouse pad', 40, 10, 25, 12.00, 24.99, 'unidad', 1, 'Accesorios'),
                        ('SKU-007', 'Cinta Adhesiva', 'Industrial duct tape', 220, 50, 100, 2.50, 4.99, 'rollo', 3, 'Suministros')
                    """
                )
        conn.commit()


def _pdf_response(pdf_bytes: bytes, filename: str) -> Response:
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


def generate_purchase_order_pdf(
    po_id: int,
    item_sku: str,
    item_name: str,
    quantity: int,
    unit_price: float,
    supplier_name: str,
    supplier_email: str,
    expected_delivery: str,
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PurchaseTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=24,
        alignment=TA_CENTER,
    )
    info_style = ParagraphStyle(
        "PurchaseInfo",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
    )

    elements = [
        Paragraph("PURCHASE ORDER", title_style),
        Spacer(1, 0.2 * inch),
        Paragraph(f"<b>Purchase Order #:</b> {po_id}", info_style),
        Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style),
        Paragraph(f"<b>Expected Delivery:</b> {expected_delivery}", info_style),
        Spacer(1, 0.1 * inch),
        Paragraph("<b>Supplier Information:</b>", styles["Heading3"]),
        Paragraph(supplier_name, info_style),
        Paragraph(f"Email: {supplier_email}", info_style),
        Spacer(1, 0.2 * inch),
        Paragraph("<b>Order Items:</b>", styles["Heading3"]),
    ]

    table_data = [
        ["SKU", "Item Name", "Quantity", "Unit Price", "Total"],
        [item_sku, item_name, str(quantity), f"${unit_price:.2f}", f"${quantity * unit_price:.2f}"],
    ]
    table = Table(table_data, colWidths=[1.1 * inch, 2.5 * inch, 0.9 * inch, 1.2 * inch, 1.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    elements.extend([table, Spacer(1, 0.25 * inch)])
    elements.append(
        Paragraph(
            f"<b>Total Amount:</b> ${quantity * unit_price:.2f}",
            ParagraphStyle("PurchaseSummary", parent=styles["Normal"], fontSize=12, textColor=colors.HexColor("#e74c3c")),
        )
    )
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph("Thank you for your business!", ParagraphStyle("Footer", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER)))

    document.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def generate_sales_invoice_pdf(
    so_id: int,
    item_sku: str,
    item_name: str,
    quantity: int,
    unit_price: float,
    customer_name: str,
    customer_email: str,
    expected_delivery: str,
) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SalesTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=colors.HexColor("#1f7a3a"),
        spaceAfter=24,
        alignment=TA_CENTER,
    )
    info_style = ParagraphStyle(
        "SalesInfo",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=6,
    )

    elements = [
        Paragraph("SALES INVOICE", title_style),
        Spacer(1, 0.2 * inch),
        Paragraph(f"<b>Invoice #:</b> {so_id}", info_style),
        Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style),
        Paragraph(f"<b>Expected Delivery:</b> {expected_delivery}", info_style),
        Spacer(1, 0.1 * inch),
        Paragraph("<b>Customer Information:</b>", styles["Heading3"]),
        Paragraph(customer_name, info_style),
        Paragraph(f"Email: {customer_email}", info_style),
        Spacer(1, 0.2 * inch),
        Paragraph("<b>Order Items:</b>", styles["Heading3"]),
    ]

    table_data = [
        ["SKU", "Item Name", "Quantity", "Unit Price", "Total"],
        [item_sku, item_name, str(quantity), f"${unit_price:.2f}", f"${quantity * unit_price:.2f}"],
    ]
    table = Table(table_data, colWidths=[1.1 * inch, 2.5 * inch, 0.9 * inch, 1.2 * inch, 1.1 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f855a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    elements.extend([table, Spacer(1, 0.25 * inch)])
    elements.append(
        Paragraph(
            f"<b>Total Amount:</b> ${quantity * unit_price:.2f}",
            ParagraphStyle("SalesSummary", parent=styles["Normal"], fontSize=12, textColor=colors.HexColor("#1f7a3a")),
        )
    )
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Paragraph("Thank you for your purchase!", ParagraphStyle("Footer", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER)))

    document.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _fetch_one(query: str, params: tuple[Any, ...]) -> Optional[tuple[Any, ...]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()


@app.on_event("startup")
def startup() -> None:
    initialize_database()
    seed_data()


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "compras"}


@app.get("/suppliers")
def list_suppliers(
    user_name: str = Header(None),
    active_only: bool = Query(True),
) -> list[dict[str, Any]]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            if active_only:
                cur.execute(
                    """
                    SELECT id, name, contact_email, phone, address, city, country, active, created_at
                    FROM suppliers
                    WHERE active = TRUE
                    ORDER BY name
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, contact_email, phone, address, city, country, active, created_at
                    FROM suppliers
                    ORDER BY name
                    """
                )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "contact_email": row[2],
            "phone": row[3],
            "address": row[4],
            "city": row[5],
            "country": row[6],
            "active": row[7],
            "created_at": row[8].isoformat() if row[8] else None,
        }
        for row in rows
    ]


@app.post("/suppliers")
def create_supplier(payload: SupplierIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO suppliers (name, contact_email, phone, address, city, country)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (payload.name, payload.contact_email, payload.phone, payload.address, payload.city, payload.country),
            )
            row = cur.fetchone()
        conn.commit()

    return {"id": row[0], "name": payload.name, "created_at": row[1].isoformat() if row[1] else None}


@app.get("/customers")
def list_customers(
    user_name: str = Header(None),
    active_only: bool = Query(True),
) -> list[dict[str, Any]]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            if active_only:
                cur.execute(
                    """
                    SELECT id, name, contact_email, phone, address, city, country, customer_type, credit_limit, active, created_at
                    FROM customers
                    WHERE active = TRUE
                    ORDER BY name
                    """
                )
            else:
                cur.execute(
                    """
                    SELECT id, name, contact_email, phone, address, city, country, customer_type, credit_limit, active, created_at
                    FROM customers
                    ORDER BY name
                    """
                )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "name": row[1],
            "contact_email": row[2],
            "phone": row[3],
            "address": row[4],
            "city": row[5],
            "country": row[6],
            "customer_type": row[7],
            "credit_limit": float(row[8]) if row[8] is not None else 0.0,
            "active": row[9],
            "created_at": row[10].isoformat() if row[10] else None,
        }
        for row in rows
    ]


@app.post("/customers")
def create_customer(payload: CustomerIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO customers (name, contact_email, phone, address, city, country, customer_type, credit_limit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    payload.name,
                    payload.contact_email,
                    payload.phone,
                    payload.address,
                    payload.city,
                    payload.country,
                    payload.customer_type,
                    payload.credit_limit,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return {"id": row[0], "name": payload.name, "created_at": row[1].isoformat() if row[1] else None}


@app.get("/items")
def list_items(
    user_name: str = Header(None),
    category: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
) -> list[dict[str, Any]]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            if category:
                cur.execute(
                    """
                    SELECT id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity,
                           unit_cost, unit_price, unit_of_measure, supplier_id, category, active, last_updated
                    FROM items
                    WHERE category = %s AND active = TRUE
                    ORDER BY sku
                    LIMIT %s OFFSET %s
                    """,
                    (category, limit, skip),
                )
            else:
                cur.execute(
                    """
                    SELECT id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity,
                           unit_cost, unit_price, unit_of_measure, supplier_id, category, active, last_updated
                    FROM items
                    WHERE active = TRUE
                    ORDER BY sku
                    LIMIT %s OFFSET %s
                    """,
                    (limit, skip),
                )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "sku": row[1],
            "name": row[2],
            "description": row[3],
            "quantity_on_hand": row[4],
            "minimum_threshold": row[5],
            "reorder_quantity": row[6],
            "unit_cost": float(row[7]),
            "unit_price": float(row[8]),
            "unit_of_measure": row[9],
            "supplier_id": row[10],
            "category": row[11],
            "active": row[12],
            "last_updated": row[13].isoformat() if row[13] else None,
            "below_minimum": row[4] < row[5],
        }
        for row in rows
    ]


@app.post("/items")
def create_item(payload: ItemIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            if payload.supplier_id is not None:
                cur.execute("SELECT id FROM suppliers WHERE id = %s", (payload.supplier_id,))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Supplier not found")

            cur.execute(
                """
                INSERT INTO items (
                    sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity,
                    unit_cost, unit_price, unit_of_measure, supplier_id, category
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    payload.sku,
                    payload.name,
                    payload.description,
                    payload.quantity_on_hand,
                    payload.minimum_threshold,
                    payload.reorder_quantity,
                    payload.unit_cost,
                    payload.unit_price,
                    payload.unit_of_measure,
                    payload.supplier_id,
                    payload.category,
                ),
            )
            row = cur.fetchone()
        conn.commit()

    return {"id": row[0], "sku": payload.sku, "created_at": row[1].isoformat() if row[1] else None}


@app.get("/items/{item_id}")
def get_item(item_id: int, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity,
                       unit_cost, unit_price, unit_of_measure, supplier_id, category, active, last_updated
                FROM items
                WHERE id = %s
                """,
                (item_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Item not found")

    return {
        "id": row[0],
        "sku": row[1],
        "name": row[2],
        "description": row[3],
        "quantity_on_hand": row[4],
        "minimum_threshold": row[5],
        "reorder_quantity": row[6],
        "unit_cost": float(row[7]),
        "unit_price": float(row[8]),
        "unit_of_measure": row[9],
        "supplier_id": row[10],
        "category": row[11],
        "active": row[12],
        "last_updated": row[13].isoformat() if row[13] else None,
        "below_minimum": row[4] < row[5],
    }


@app.get("/purchase-orders")
def list_purchase_orders(
    user_name: str = Header(None),
    status: Optional[str] = Query(None),
    supplier_id: Optional[int] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
) -> list[dict[str, Any]]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    clauses = []
    params: list[Any] = []
    if status:
        clauses.append("po.status = %s")
        params.append(status)
    if supplier_id is not None:
        clauses.append("po.supplier_id = %s")
        params.append(supplier_id)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT po.id, po.item_id, po.supplier_id, po.quantity, po.unit_price,
                       po.total_amount, po.status, po.created_at, po.expected_delivery_date,
                       po.requested_by, i.sku, i.name, s.name
                FROM purchase_orders po
                JOIN items i ON po.item_id = i.id
                JOIN suppliers s ON po.supplier_id = s.id
                {where_sql}
                ORDER BY po.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, skip),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "item_id": row[1],
            "supplier_id": row[2],
            "quantity": row[3],
            "unit_price": float(row[4]),
            "total_amount": float(row[5]) if row[5] else None,
            "status": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "expected_delivery_date": row[8].isoformat() if row[8] else None,
            "requested_by": row[9],
            "item_sku": row[10],
            "item_name": row[11],
            "supplier_name": row[12],
        }
        for row in rows
    ]


@app.post("/purchase-orders")
def create_purchase_order(payload: PurchaseOrderIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT sku, name FROM items WHERE id = %s", (payload.item_id,))
            item_row = cur.fetchone()
            if not item_row:
                raise HTTPException(status_code=404, detail="Item not found")

            cur.execute("SELECT name, contact_email FROM suppliers WHERE id = %s", (payload.supplier_id,))
            supplier_row = cur.fetchone()
            if not supplier_row:
                raise HTTPException(status_code=404, detail="Supplier not found")

            total_amount = payload.quantity * payload.unit_price
            expected_delivery = (datetime.now() + timedelta(days=payload.expected_delivery_days)).date()
            cur.execute(
                """
                INSERT INTO purchase_orders
                (item_id, supplier_id, quantity, unit_price, total_amount, expected_delivery_date, requested_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    payload.item_id,
                    payload.supplier_id,
                    payload.quantity,
                    payload.unit_price,
                    total_amount,
                    expected_delivery,
                    user_name,
                ),
            )
            row = cur.fetchone()
            po_id = row[0]
            created_at = row[1]

            try:
                pdf_content = generate_purchase_order_pdf(
                    po_id=po_id,
                    item_sku=item_row[0],
                    item_name=item_row[1],
                    quantity=payload.quantity,
                    unit_price=payload.unit_price,
                    supplier_name=supplier_row[0],
                    supplier_email=supplier_row[1] or "N/A",
                    expected_delivery=expected_delivery.isoformat(),
                )
                cur.execute(
                    """
                    UPDATE purchase_orders
                    SET pdf_content = %s, pdf_filename = %s
                    WHERE id = %s
                    """,
                    (pdf_content, f"PO-{po_id}-{item_row[0]}.pdf", po_id),
                )
            except Exception:
                pass

        conn.commit()

    return {
        "id": po_id,
        "item_id": payload.item_id,
        "supplier_id": payload.supplier_id,
        "quantity": payload.quantity,
        "unit_price": payload.unit_price,
        "total_amount": total_amount,
        "status": "pending",
        "expected_delivery_date": expected_delivery.isoformat(),
        "created_at": created_at.isoformat() if created_at else None,
        "requested_by": user_name,
    }


@app.get("/purchase-orders/{po_id}")
def get_purchase_order(po_id: int, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT po.id, po.item_id, po.supplier_id, po.quantity, po.unit_price,
                       po.total_amount, po.status, po.created_at, po.expected_delivery_date,
                       po.requested_by, i.sku, i.name, s.name, s.contact_email
                FROM purchase_orders po
                JOIN items i ON po.item_id = i.id
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.id = %s
                """,
                (po_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Purchase order not found")

    return {
        "id": row[0],
        "item_id": row[1],
        "supplier_id": row[2],
        "quantity": row[3],
        "unit_price": float(row[4]),
        "total_amount": float(row[5]) if row[5] else None,
        "status": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
        "expected_delivery_date": row[8].isoformat() if row[8] else None,
        "requested_by": row[9],
        "item_sku": row[10],
        "item_name": row[11],
        "supplier_name": row[12],
        "supplier_email": row[13],
    }


@app.get("/purchase-orders/{po_id}/pdf")
def get_purchase_order_pdf(po_id: int, user_name: str = Header(None)) -> Response:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    row = _fetch_one(
        """
        SELECT pdf_content, pdf_filename
        FROM purchase_orders
        WHERE id = %s
        """,
        (po_id,),
    )
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="PDF not found")

    return _pdf_response(row[0], row[1] or f"purchase-order-{po_id}.pdf")


@app.patch("/purchase-orders/{po_id}/status")
def update_purchase_order_status(po_id: int, new_status: str, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    valid_statuses = ["pending", "confirmed", "shipped", "received", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_id, quantity, status
                FROM purchase_orders
                WHERE id = %s
                """,
                (po_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Purchase order not found")

            item_id, quantity, old_status = row
            cur.execute(
                """
                UPDATE purchase_orders
                SET status = %s,
                    received_at = CASE WHEN %s = 'received' AND received_at IS NULL THEN CURRENT_TIMESTAMP ELSE received_at END
                WHERE id = %s
                RETURNING status
                """,
                (new_status, new_status, po_id),
            )

            stock_updated = False
            if new_status == "received" and old_status != "received":
                cur.execute(
                    """
                    UPDATE items
                    SET quantity_on_hand = quantity_on_hand + %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (quantity, item_id),
                )
                cur.execute(
                    """
                    INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (item_id, "in", quantity, "purchase_order_received", f"PO-{po_id}", user_name),
                )
                stock_updated = True

        conn.commit()

    return {
        "id": po_id,
        "status": new_status,
        "updated_at": datetime.now().isoformat(),
        "stock_updated": stock_updated,
    }


@app.get("/sales-orders")
def list_sales_orders(
    user_name: str = Header(None),
    status: Optional[str] = Query(None),
    customer_id: Optional[int] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100),
) -> list[dict[str, Any]]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    clauses = []
    params: list[Any] = []
    if status:
        clauses.append("so.status = %s")
        params.append(status)
    if customer_id is not None:
        clauses.append("so.customer_id = %s")
        params.append(customer_id)

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT so.id, so.item_id, so.customer_id, so.quantity, so.unit_price,
                       so.total_amount, so.status, so.created_at, so.expected_delivery_date,
                       so.created_by, i.sku, i.name, c.name
                FROM sales_orders so
                JOIN items i ON so.item_id = i.id
                JOIN customers c ON so.customer_id = c.id
                {where_sql}
                ORDER BY so.created_at DESC
                LIMIT %s OFFSET %s
                """,
                (*params, limit, skip),
            )
            rows = cur.fetchall()

    return [
        {
            "id": row[0],
            "item_id": row[1],
            "customer_id": row[2],
            "quantity": row[3],
            "unit_price": float(row[4]),
            "total_amount": float(row[5]) if row[5] else None,
            "status": row[6],
            "created_at": row[7].isoformat() if row[7] else None,
            "expected_delivery_date": row[8].isoformat() if row[8] else None,
            "created_by": row[9],
            "item_sku": row[10],
            "item_name": row[11],
            "customer_name": row[12],
        }
        for row in rows
    ]


@app.post("/sales-orders")
def create_sales_order(payload: SalesOrderIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sku, name, unit_price, quantity_on_hand
                FROM items
                WHERE id = %s
                """,
                (payload.item_id,),
            )
            item_row = cur.fetchone()
            if not item_row:
                raise HTTPException(status_code=404, detail="Item not found")

            if item_row[3] < payload.quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock")

            cur.execute(
                """
                SELECT name, contact_email
                FROM customers
                WHERE id = %s
                """,
                (payload.customer_id,),
            )
            customer_row = cur.fetchone()
            if not customer_row:
                raise HTTPException(status_code=404, detail="Customer not found")

            unit_price = float(item_row[2]) if item_row[2] else 0.0
            total_amount = payload.quantity * unit_price
            expected_delivery = (datetime.now() + timedelta(days=payload.expected_delivery_days)).date()

            cur.execute(
                """
                INSERT INTO sales_orders
                (item_id, customer_id, quantity, unit_price, total_amount, expected_delivery_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    payload.item_id,
                    payload.customer_id,
                    payload.quantity,
                    unit_price,
                    total_amount,
                    expected_delivery,
                    user_name,
                ),
            )
            row = cur.fetchone()
            so_id = row[0]
            created_at = row[1]

            cur.execute(
                """
                UPDATE items
                SET quantity_on_hand = quantity_on_hand - %s,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (payload.quantity, payload.item_id),
            )
            cur.execute(
                """
                INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (payload.item_id, "out", payload.quantity, "sales_order_created", f"SO-{so_id}", user_name),
            )

            try:
                pdf_content = generate_sales_invoice_pdf(
                    so_id=so_id,
                    item_sku=item_row[0],
                    item_name=item_row[1],
                    quantity=payload.quantity,
                    unit_price=unit_price,
                    customer_name=customer_row[0],
                    customer_email=customer_row[1] or "N/A",
                    expected_delivery=expected_delivery.isoformat(),
                )
                cur.execute(
                    """
                    UPDATE sales_orders
                    SET invoice_content = %s,
                        invoice_filename = %s
                    WHERE id = %s
                    """,
                    (pdf_content, f"INV-{so_id}-{item_row[0]}.pdf", so_id),
                )
            except Exception:
                pass

        conn.commit()

    return {
        "id": so_id,
        "item_id": payload.item_id,
        "customer_id": payload.customer_id,
        "quantity": payload.quantity,
        "unit_price": unit_price,
        "total_amount": total_amount,
        "status": "pending",
        "expected_delivery_date": expected_delivery.isoformat(),
        "created_at": created_at.isoformat() if created_at else None,
        "requested_by": user_name,
    }


@app.get("/sales-orders/{so_id}")
def get_sales_order(so_id: int, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT so.id, so.item_id, so.customer_id, so.quantity, so.unit_price,
                       so.total_amount, so.status, so.created_at, so.expected_delivery_date,
                       so.created_by, i.sku, i.name, c.name, c.contact_email
                FROM sales_orders so
                JOIN items i ON so.item_id = i.id
                JOIN customers c ON so.customer_id = c.id
                WHERE so.id = %s
                """,
                (so_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Sales order not found")

    return {
        "id": row[0],
        "item_id": row[1],
        "customer_id": row[2],
        "quantity": row[3],
        "unit_price": float(row[4]),
        "total_amount": float(row[5]) if row[5] else None,
        "status": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
        "expected_delivery_date": row[8].isoformat() if row[8] else None,
        "created_by": row[9],
        "item_sku": row[10],
        "item_name": row[11],
        "customer_name": row[12],
        "customer_email": row[13],
    }


@app.get("/sales-orders/{so_id}/invoice")
def get_sales_invoice(so_id: int, user_name: str = Header(None)) -> Response:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    row = _fetch_one(
        """
        SELECT invoice_content, invoice_filename
        FROM sales_orders
        WHERE id = %s
        """,
        (so_id,),
    )
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return _pdf_response(row[0], row[1] or f"invoice-{so_id}.pdf")


@app.patch("/sales-orders/{so_id}/status")
def update_sales_order_status(so_id: int, new_status: str, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT item_id, quantity, status
                FROM sales_orders
                WHERE id = %s
                """,
                (so_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Sales order not found")

            item_id, quantity, old_status = row
            cur.execute(
                """
                UPDATE sales_orders
                SET status = %s,
                    shipped_at = CASE WHEN %s = 'shipped' AND shipped_at IS NULL THEN CURRENT_TIMESTAMP ELSE shipped_at END,
                    delivered_at = CASE WHEN %s = 'delivered' AND delivered_at IS NULL THEN CURRENT_TIMESTAMP ELSE delivered_at END
                WHERE id = %s
                RETURNING status
                """,
                (new_status, new_status, new_status, so_id),
            )

            stock_updated = False
            if new_status == "cancelled" and old_status not in ("cancelled", "delivered"):
                cur.execute(
                    """
                    UPDATE items
                    SET quantity_on_hand = quantity_on_hand + %s,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (quantity, item_id),
                )
                cur.execute(
                    """
                    INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (item_id, "in", quantity, "sales_order_cancelled", f"SO-{so_id}", user_name),
                )
                stock_updated = True

        conn.commit()

    return {
        "id": so_id,
        "status": new_status,
        "updated_at": datetime.now().isoformat(),
        "stock_updated": stock_updated,
    }


@app.post("/payments/customer")
def record_customer_payment(payload: PaymentIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT so.total_amount, c.name
                FROM sales_orders so
                JOIN customers c ON so.customer_id = c.id
                WHERE so.id = %s
                """,
                (payload.order_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Sales order not found")

            cur.execute(
                """
                INSERT INTO payment_records (
                    order_type, order_id, counterparty_type, counterparty_name, amount,
                    payment_method, notes, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    "sale",
                    payload.order_id,
                    "customer",
                    row[1],
                    payload.amount,
                    payload.payment_method,
                    payload.notes,
                    user_name,
                ),
            )
            payment_row = cur.fetchone()
        conn.commit()

    return {
        "id": payment_row[0],
        "order_type": "sale",
        "order_id": payload.order_id,
        "counterparty_type": "customer",
        "counterparty_name": row[1],
        "amount": payload.amount,
        "payment_method": payload.payment_method,
        "created_at": payment_row[1].isoformat() if payment_row[1] else None,
    }


@app.post("/payments/supplier")
def record_supplier_payment(payload: PaymentIn, user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT po.total_amount, s.name
                FROM purchase_orders po
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.id = %s
                """,
                (payload.order_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Purchase order not found")

            cur.execute(
                """
                INSERT INTO payment_records (
                    order_type, order_id, counterparty_type, counterparty_name, amount,
                    payment_method, notes, created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
                """,
                (
                    "purchase",
                    payload.order_id,
                    "supplier",
                    row[1],
                    payload.amount,
                    payload.payment_method,
                    payload.notes,
                    user_name,
                ),
            )
            payment_row = cur.fetchone()
        conn.commit()

    return {
        "id": payment_row[0],
        "order_type": "purchase",
        "order_id": payload.order_id,
        "counterparty_type": "supplier",
        "counterparty_name": row[1],
        "amount": payload.amount,
        "payment_method": payload.payment_method,
        "created_at": payment_row[1].isoformat() if payment_row[1] else None,
    }


@app.get("/transactions/history")
def transaction_history(
    user_name: str = Header(None),
    party_type: Optional[str] = Query(None),
    party_name: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    limit: int = Query(100),
) -> list[dict[str, Any]]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    clauses = []
    params: list[Any] = []
    if transaction_type in ("purchase", "sale", "payment"):
        if transaction_type == "payment":
            clauses.append("source_type = 'payment'")
        else:
            clauses.append("source_type = %s")
            params.append(transaction_type)
    if party_type in ("supplier", "customer"):
        clauses.append("counterparty_type = %s")
        params.append(party_type)
    if party_name:
        clauses.append("counterparty_name ILIKE %s")
        params.append(f"%{party_name}%")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT source_type, counterparty_type, counterparty_name, order_id, amount, status, created_at, reference_label
                FROM (
                    SELECT 'purchase' AS source_type,
                           'supplier' AS counterparty_type,
                           s.name AS counterparty_name,
                           po.id AS order_id,
                           po.total_amount AS amount,
                           po.status AS status,
                           po.created_at AS created_at,
                           po.pdf_filename AS reference_label
                    FROM purchase_orders po
                    JOIN suppliers s ON po.supplier_id = s.id
                    UNION ALL
                    SELECT 'sale' AS source_type,
                           'customer' AS counterparty_type,
                           c.name AS counterparty_name,
                           so.id AS order_id,
                           so.total_amount AS amount,
                           so.status AS status,
                           so.created_at AS created_at,
                           so.invoice_filename AS reference_label
                    FROM sales_orders so
                    JOIN customers c ON so.customer_id = c.id
                    UNION ALL
                    SELECT 'payment' AS source_type,
                           pr.counterparty_type AS counterparty_type,
                           pr.counterparty_name AS counterparty_name,
                           pr.order_id AS order_id,
                           pr.amount AS amount,
                           'recorded' AS status,
                           pr.created_at AS created_at,
                           pr.payment_method AS reference_label
                    FROM payment_records pr
                ) AS history
                {where_sql}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (*params, limit),
            )
            rows = cur.fetchall()

    return [
        {
            "transaction_type": row[0],
            "counterparty_type": row[1],
            "counterparty_name": row[2],
            "order_id": row[3],
            "amount": float(row[4]) if row[4] is not None else None,
            "status": row[5],
            "created_at": row[6].isoformat() if row[6] else None,
            "reference_label": row[7],
        }
        for row in rows
    ]


@app.get("/stats/commercial-summary")
def commercial_summary(user_name: str = Header(None)) -> dict[str, Any]:
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 'purchase' AS kind, status, COUNT(*) AS count, COALESCE(SUM(total_amount), 0) AS total_value
                FROM purchase_orders
                GROUP BY status
                UNION ALL
                SELECT 'sale' AS kind, status, COUNT(*) AS count, COALESCE(SUM(total_amount), 0) AS total_value
                FROM sales_orders
                GROUP BY status
                ORDER BY kind, status
                """
            )
            rows = cur.fetchall()

            cur.execute("SELECT COALESCE(SUM(amount), 0) FROM payment_records")
            payment_total = cur.fetchone()[0]

    summary: dict[str, Any] = {"purchase": {}, "sale": {}, "payment_total": float(payment_total) if payment_total else 0.0}
    for row in rows:
        summary[row[0]][row[1]] = {"count": row[2], "total_value": float(row[3])}
    return summary
