"""
Operaciones Microservice - Unified Service
Combines: Inventory, Purchases, Sales, and Logistics
- Manages inventory items and stock levels
- Handles purchase orders from suppliers
- Processes sales orders to customers
- Monitors stock levels and generates alerts
- Tracks logistics requests and movements
"""

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Optional
from io import BytesIO
import psycopg
import os

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
except ImportError:
    pass

app = FastAPI(title="Operaciones Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://operaciones:operaciones@localhost:5432/transactions_db")

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def initialize_database():
    """Create all operational tables"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Suppliers table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS suppliers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    contact_email VARCHAR(255),
                    phone VARCHAR(20),
                    address TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100),
                    supplier_type VARCHAR(50) DEFAULT 'supplier',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Customers table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    contact_email VARCHAR(255),
                    phone VARCHAR(20),
                    address TEXT,
                    city VARCHAR(100),
                    country VARCHAR(100),
                    customer_type VARCHAR(50) DEFAULT 'retail',
                    credit_limit DECIMAL(12, 2),
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Items table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    sku VARCHAR(50) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    quantity_on_hand INTEGER NOT NULL DEFAULT 0,
                    minimum_threshold INTEGER NOT NULL DEFAULT 10,
                    reorder_quantity INTEGER NOT NULL DEFAULT 50,
                    unit_cost DECIMAL(10, 2) NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    unit_of_measure VARCHAR(20) DEFAULT 'unidad',
                    supplier_id INTEGER,
                    category VARCHAR(100),
                    active BOOLEAN DEFAULT TRUE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            """)
            
            # Purchase Orders
            cur.execute("""
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
            """)
            
            # Sales Orders
            cur.execute("""
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
            """)
            
            # Stock movements
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    movement_type VARCHAR(50),
                    quantity INTEGER NOT NULL,
                    reason TEXT,
                    reference_id VARCHAR(100),
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            
            # Logistics requests
            cur.execute("""
                CREATE TABLE IF NOT EXISTS solicitudes_logistica (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    requested_quantity INTEGER NOT NULL,
                    reason VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'pending',
                    priority VARCHAR(20) DEFAULT 'normal',
                    notes TEXT,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by VARCHAR(100),
                    approved_at TIMESTAMP,
                    fulfilled_at TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            
            # Stock alerts
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_alerts (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    alert_type VARCHAR(50),
                    current_quantity INTEGER,
                    threshold INTEGER,
                    severity VARCHAR(20) DEFAULT 'warning',
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by VARCHAR(100),
                    acknowledged_at TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
        
        conn.commit()

def seed_data():
    """Seed suppliers, customers, and sample items"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Seed suppliers
            cur.execute("SELECT COUNT(*) FROM suppliers")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO suppliers (name, contact_email, phone, city, country)
                    VALUES 
                        ('TechSupply Inc', 'sales@techsupply.com', '+1234567890', 'New York', 'USA'),
                        ('Industrial Parts Ltd', 'info@industrial.co.uk', '+442071234567', 'London', 'UK'),
                        ('Global Logistics Co', 'procurement@global.cn', '+86-10-1234-5678', 'Beijing', 'China')
                """)
            
            # Seed customers
            cur.execute("SELECT COUNT(*) FROM customers")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO customers (name, contact_email, phone, city, country, customer_type, credit_limit)
                    VALUES 
                        ('ABC Retail Store', 'manager@abc.com', '+5551234567', 'Miami', 'USA', 'retail', 50000.00),
                        ('XYZ Distributor', 'sales@xyz.com', '+5559876543', 'Los Angeles', 'USA', 'wholesale', 100000.00),
                        ('Corner Shop', 'owner@corner.com', '+5551111111', 'Chicago', 'USA', 'retail', 20000.00)
                """)
            
            # Seed items
            cur.execute("SELECT COUNT(*) FROM items")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO items (sku, name, description, quantity_on_hand, minimum_threshold,
                                       reorder_quantity, unit_cost, unit_price, unit_of_measure, supplier_id, category)
                    VALUES
                        ('SKU-001', 'Laptop Dell XPS 13', 'High-performance laptop', 8, 3, 10, 1200.00, 1499.99, 'unidad', 1, 'Electrónica'),
                        ('SKU-002', 'Monitor LG 27"', 'Full HD Monitor', 15, 5, 15, 250.00, 349.99, 'unidad', 1, 'Electrónica'),
                        ('SKU-003', 'Toner HP LaserJet', 'Black toner cartridge', 52, 10, 20, 45.00, 89.99, 'unidad', 2, 'Suministros'),
                        ('SKU-004', 'Papel A4 80gsm', 'Resma de papel blanco', 140, 30, 50, 8.50, 12.99, 'resma', 2, 'Suministros'),
                        ('SKU-005', 'Cable HDMI 2M', 'High-speed HDMI cable', 85, 20, 30, 5.99, 9.99, 'unidad', 1, 'Accesorios'),
                        ('SKU-006', 'Mouse Logitech', 'Ergonomic mouse pad', 40, 10, 25, 12.00, 24.99, 'unidad', 1, 'Accesorios'),
                        ('SKU-007', 'Cinta Adhesiva', 'Industrial duct tape', 220, 50, 100, 2.50, 4.99, 'rollo', 3, 'Suministros')
                """)
            
        conn.commit()

def generate_purchase_order_pdf(po_id: int, item_sku: str, item_name: str, 
                                quantity: int, unit_price: float, supplier_name: str,
                                supplier_email: str, expected_delivery: str):
    """Generate PDF for purchase order"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("PURCHASE ORDER", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    info_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    elements.append(Paragraph(f"<b>PO #:</b> {po_id}", info_style))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
    elements.append(Paragraph(f"<b>Expected Delivery:</b> {expected_delivery}", info_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("<b>Supplier:</b>", styles['Heading3']))
    elements.append(Paragraph(f"{supplier_name}", info_style))
    elements.append(Paragraph(f"Email: {supplier_email}", info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("<b>Items:</b>", styles['Heading3']))
    
    table_data = [
        ['SKU', 'Description', 'Qty', 'Unit Price', 'Total'],
        [item_sku, item_name, str(quantity), f'${unit_price:.2f}', f'${quantity * unit_price:.2f}']
    ]
    
    table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"<b>Total:</b> ${quantity * unit_price:.2f}", info_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

def generate_sales_invoice_pdf(so_id: int, item_sku: str, item_name: str, 
                               quantity: int, unit_price: float, customer_name: str,
                               customer_email: str, expected_delivery: str):
    """Generate PDF invoice for sales order"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#27ae60'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    elements.append(Paragraph("SALES INVOICE", title_style))
    elements.append(Spacer(1, 0.3*inch))
    
    info_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    elements.append(Paragraph(f"<b>Invoice #:</b> {so_id}", info_style))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
    elements.append(Paragraph(f"<b>Expected Delivery:</b> {expected_delivery}", info_style))
    elements.append(Spacer(1, 0.2*inch))
    
    elements.append(Paragraph("<b>Customer:</b>", styles['Heading3']))
    elements.append(Paragraph(f"{customer_name}", info_style))
    elements.append(Paragraph(f"Email: {customer_email}", info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    elements.append(Paragraph("<b>Items:</b>", styles['Heading3']))
    
    table_data = [
        ['SKU', 'Description', 'Qty', 'Unit Price', 'Total'],
        [item_sku, item_name, str(quantity), f'${unit_price:.2f}', f'${quantity * unit_price:.2f}']
    ]
    
    table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 0.8*inch, 1.2*inch, 1.1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(f"<b>Total Amount Due:</b> ${quantity * unit_price:.2f}", info_style))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ============ HEALTH CHECK ============

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "operaciones"}

# ============ ITEMS / INVENTORY ============

@app.get("/items")
def list_items(
    user_name: str = Header(None),
    category: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """List inventory items"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if category:
                cur.execute("""
                    SELECT id, sku, name, quantity_on_hand, minimum_threshold,
                           unit_price, category
                    FROM items
                    WHERE category = %s AND active = TRUE
                    ORDER BY sku
                    LIMIT %s OFFSET %s
                """, (category, limit, skip))
            else:
                cur.execute("""
                    SELECT id, sku, name, quantity_on_hand, minimum_threshold,
                           unit_price, category
                    FROM items
                    WHERE active = TRUE
                    ORDER BY sku
                    LIMIT %s OFFSET %s
                """, (limit, skip))
            
            items = []
            for row in cur.fetchall():
                items.append({
                    "id": row[0],
                    "sku": row[1],
                    "name": row[2],
                    "quantity_on_hand": row[3],
                    "minimum_threshold": row[4],
                    "unit_price": float(row[5]),
                    "category": row[6],
                    "below_minimum": row[3] < row[4],
                })
            
            return items

@app.post("/items/{item_id}/stock/update")
def update_stock(
    item_id: int,
    quantity_change: int,
    reason: str,
    reference_id: Optional[str] = None,
    user_name: str = Header(None)
):
    """Update item stock"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT quantity_on_hand FROM items WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Item not found")
            
            current_qty = row[0]
            new_qty = current_qty + quantity_change
            
            if new_qty < 0:
                raise HTTPException(status_code=400, detail="Insufficient stock")
            
            cur.execute("""
                UPDATE items
                SET quantity_on_hand = %s, last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_qty, item_id))
            
            movement_type = "in" if quantity_change > 0 else "out"
            cur.execute("""
                INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (item_id, movement_type, abs(quantity_change), reason, reference_id, user_name))
        
        conn.commit()
    
    return {"item_id": item_id, "new_quantity": new_qty}

# ============ PURCHASE ORDERS (COMPRAS) ============

@app.get("/purchase-orders")
def list_purchase_orders(
    user_name: str = Header(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """List purchase orders"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute("""
                    SELECT po.id, po.item_id, po.supplier_id, po.quantity, po.unit_price,
                           po.total_amount, po.status, po.created_at, po.expected_delivery_date,
                           i.sku, i.name, s.name
                    FROM purchase_orders po
                    JOIN items i ON po.item_id = i.id
                    JOIN suppliers s ON po.supplier_id = s.id
                    WHERE po.status = %s
                    ORDER BY po.created_at DESC
                    LIMIT %s OFFSET %s
                """, (status, limit, skip))
            else:
                cur.execute("""
                    SELECT po.id, po.item_id, po.supplier_id, po.quantity, po.unit_price,
                           po.total_amount, po.status, po.created_at, po.expected_delivery_date,
                           i.sku, i.name, s.name
                    FROM purchase_orders po
                    JOIN items i ON po.item_id = i.id
                    JOIN suppliers s ON po.supplier_id = s.id
                    ORDER BY po.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, skip))
            
            orders = []
            for row in cur.fetchall():
                orders.append({
                    "id": row[0],
                    "item_id": row[1],
                    "supplier_id": row[2],
                    "quantity": row[3],
                    "unit_price": float(row[4]),
                    "total_amount": float(row[5]) if row[5] else None,
                    "status": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "expected_delivery_date": row[8].isoformat() if row[8] else None,
                    "item_sku": row[9],
                    "item_name": row[10],
                    "supplier_name": row[11],
                })
            
            return orders

@app.post("/purchase-orders")
def create_purchase_order(
    item_id: int,
    supplier_id: int,
    quantity: int,
    unit_price: float,
    expected_delivery_days: int = 7,
    user_name: str = Header(None)
):
    """Create purchase order"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT sku, name FROM items WHERE id = %s", (item_id,))
            item_row = cur.fetchone()
            if not item_row:
                raise HTTPException(status_code=404, detail="Item not found")
            
            cur.execute("SELECT name, contact_email FROM suppliers WHERE id = %s", (supplier_id,))
            supplier_row = cur.fetchone()
            if not supplier_row:
                raise HTTPException(status_code=404, detail="Supplier not found")
            
            total_amount = quantity * unit_price
            expected_delivery = (datetime.now() + timedelta(days=expected_delivery_days)).date()
            
            cur.execute("""
                INSERT INTO purchase_orders 
                (item_id, supplier_id, quantity, unit_price, total_amount, 
                 expected_delivery_date, requested_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (item_id, supplier_id, quantity, unit_price, total_amount, 
                  expected_delivery, user_name))
            
            result = cur.fetchone()
            po_id = result[0]
            
            try:
                pdf_content = generate_purchase_order_pdf(
                    po_id=po_id,
                    item_sku=item_row[0],
                    item_name=item_row[1],
                    quantity=quantity,
                    unit_price=unit_price,
                    supplier_name=supplier_row[0],
                    supplier_email=supplier_row[1] or "N/A",
                    expected_delivery=expected_delivery.isoformat()
                )
                
                pdf_filename = f"PO-{po_id}-{item_row[0]}.pdf"
                cur.execute("""
                    UPDATE purchase_orders
                    SET pdf_content = %s, pdf_filename = %s
                    WHERE id = %s
                """, (pdf_content, pdf_filename, po_id))
            except:
                pass
            
            conn.commit()
            
            return {
                "id": po_id,
                "item_id": item_id,
                "supplier_id": supplier_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "status": "pending",
                "expected_delivery_date": expected_delivery.isoformat(),
            }

@app.get("/purchase-orders/{po_id}/pdf")
def get_purchase_order_pdf(po_id: int, user_name: str = Header(None)):
    """Download purchase order PDF"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pdf_content, pdf_filename
                FROM purchase_orders
                WHERE id = %s
            """, (po_id,))
            
            row = cur.fetchone()
            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="PDF not found")
            
            return FileResponse(
                BytesIO(row[0]),
                media_type="application/pdf",
                filename=row[1] or f"purchase-order-{po_id}.pdf"
            )

@app.patch("/purchase-orders/{po_id}/status")
def update_purchase_order_status(
    po_id: int,
    new_status: str,
    user_name: str = Header(None)
):
    """Update purchase order status"""
    valid_statuses = ['pending', 'confirmed', 'shipped', 'received', 'cancelled']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status")
    
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT item_id, quantity, status
                FROM purchase_orders
                WHERE id = %s
            """, (po_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="PO not found")
            
            item_id, quantity, old_status = row
            
            cur.execute("""
                UPDATE purchase_orders
                SET status = %s
                WHERE id = %s
            """, (new_status, po_id))
            
            # Auto-update inventory when received
            if new_status == 'received' and old_status != 'received':
                cur.execute("""
                    UPDATE items
                    SET quantity_on_hand = quantity_on_hand + %s, last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (quantity, item_id))
                
                cur.execute("""
                    INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (item_id, 'in', quantity, 'purchase_order_received', f'PO-{po_id}', user_name))
            
            conn.commit()
    
    return {"id": po_id, "status": new_status}

# ============ SALES ORDERS (VENTAS) ============

@app.get("/sales-orders")
def list_sales_orders(
    user_name: str = Header(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """List sales orders"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute("""
                    SELECT so.id, so.item_id, so.customer_id, so.quantity, so.unit_price,
                           so.total_amount, so.status, so.created_at, so.expected_delivery_date,
                           i.sku, i.name, c.name
                    FROM sales_orders so
                    JOIN items i ON so.item_id = i.id
                    JOIN customers c ON so.customer_id = c.id
                    WHERE so.status = %s
                    ORDER BY so.created_at DESC
                    LIMIT %s OFFSET %s
                """, (status, limit, skip))
            else:
                cur.execute("""
                    SELECT so.id, so.item_id, so.customer_id, so.quantity, so.unit_price,
                           so.total_amount, so.status, so.created_at, so.expected_delivery_date,
                           i.sku, i.name, c.name
                    FROM sales_orders so
                    JOIN items i ON so.item_id = i.id
                    JOIN customers c ON so.customer_id = c.id
                    ORDER BY so.created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, skip))
            
            orders = []
            for row in cur.fetchall():
                orders.append({
                    "id": row[0],
                    "item_id": row[1],
                    "customer_id": row[2],
                    "quantity": row[3],
                    "unit_price": float(row[4]),
                    "total_amount": float(row[5]) if row[5] else None,
                    "status": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                    "expected_delivery_date": row[8].isoformat() if row[8] else None,
                    "item_sku": row[9],
                    "item_name": row[10],
                    "customer_name": row[11],
                })
            
            return orders

@app.post("/sales-orders")
def create_sales_order(
    item_id: int,
    customer_id: int,
    quantity: int,
    expected_delivery_days: int = 3,
    user_name: str = Header(None)
):
    """Create sales order"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT sku, name, unit_price, quantity_on_hand FROM items WHERE id = %s", (item_id,))
            item_row = cur.fetchone()
            if not item_row:
                raise HTTPException(status_code=404, detail="Item not found")
            
            if item_row[3] < quantity:
                raise HTTPException(status_code=400, detail="Insufficient stock")
            
            cur.execute("SELECT name, contact_email FROM customers WHERE id = %s", (customer_id,))
            customer_row = cur.fetchone()
            if not customer_row:
                raise HTTPException(status_code=404, detail="Customer not found")
            
            unit_price = float(item_row[2])
            total_amount = quantity * unit_price
            expected_delivery = (datetime.now() + timedelta(days=expected_delivery_days)).date()
            
            cur.execute("""
                INSERT INTO sales_orders 
                (item_id, customer_id, quantity, unit_price, total_amount, 
                 expected_delivery_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (item_id, customer_id, quantity, unit_price, total_amount, 
                  expected_delivery, user_name))
            
            result = cur.fetchone()
            so_id = result[0]
            
            # Deduct from inventory immediately
            cur.execute("""
                UPDATE items
                SET quantity_on_hand = quantity_on_hand - %s, last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (quantity, item_id))
            
            cur.execute("""
                INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (item_id, 'out', quantity, 'sales_order', f'SO-{so_id}', user_name))
            
            try:
                pdf_content = generate_sales_invoice_pdf(
                    so_id=so_id,
                    item_sku=item_row[0],
                    item_name=item_row[1],
                    quantity=quantity,
                    unit_price=unit_price,
                    customer_name=customer_row[0],
                    customer_email=customer_row[1] or "N/A",
                    expected_delivery=expected_delivery.isoformat()
                )
                
                invoice_filename = f"INV-{so_id}-{item_row[0]}.pdf"
                cur.execute("""
                    UPDATE sales_orders
                    SET invoice_content = %s, invoice_filename = %s
                    WHERE id = %s
                """, (pdf_content, invoice_filename, so_id))
            except:
                pass
            
            conn.commit()
            
            return {
                "id": so_id,
                "item_id": item_id,
                "customer_id": customer_id,
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": total_amount,
                "status": "pending",
                "expected_delivery_date": expected_delivery.isoformat(),
            }

@app.get("/sales-orders/{so_id}/invoice")
def get_sales_invoice(so_id: int, user_name: str = Header(None)):
    """Download sales invoice"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT invoice_content, invoice_filename
                FROM sales_orders
                WHERE id = %s
            """, (so_id,))
            
            row = cur.fetchone()
            if not row or not row[0]:
                raise HTTPException(status_code=404, detail="Invoice not found")
            
            return FileResponse(
                BytesIO(row[0]),
                media_type="application/pdf",
                filename=row[1] or f"invoice-{so_id}.pdf"
            )

@app.patch("/sales-orders/{so_id}/status")
def update_sales_order_status(
    so_id: int,
    new_status: str,
    user_name: str = Header(None)
):
    """Update sales order status"""
    valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status")
    
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE sales_orders
                SET status = %s
                WHERE id = %s
            """, (new_status, so_id))
            
            conn.commit()
    
    return {"id": so_id, "status": new_status}

# ============ STARTUP ============

@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    initialize_database()
    seed_data()
