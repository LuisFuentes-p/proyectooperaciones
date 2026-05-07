"""
Inventario Microservice
- Manages inventory items (SKU, stock levels, reorder thresholds)
- Tracks logistics requests (restock, returns, damage reports)
- Updates stock when compras service fulfills purchase orders
- Provides stock status for logistica service monitoring
"""

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
import psycopg
import os

app = FastAPI(title="Inventario Service", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/transactions_db"))

@contextmanager
def get_db():
    """Database connection context manager"""
    conn = psycopg.connect(DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()

def initialize_database():
    """Create inventory tables if they don't exist"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # Suppliers/Vendors table
            cur.execute("""
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
            """)
            
            # Items table - core inventory
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
                    unit_of_measure VARCHAR(20) DEFAULT 'unidad',
                    supplier_id INTEGER,
                    category VARCHAR(100),
                    active BOOLEAN DEFAULT TRUE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
                )
            """)
            
            # Stock movement history - for audit trail
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    movement_type VARCHAR(50) NOT NULL,  -- in, out, adjustment, return, damage
                    quantity INTEGER NOT NULL,
                    reason TEXT,
                    reference_id VARCHAR(100),  -- Purchase order, solicitud, etc
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            
            # Logistica requests table - stock alerts and requests
            cur.execute("""
                CREATE TABLE IF NOT EXISTS solicitudes_logistica (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    requested_quantity INTEGER NOT NULL,
                    reason VARCHAR(100) NOT NULL,  -- restock, return, damage, adjustment
                    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, fulfilled
                    priority VARCHAR(20) DEFAULT 'normal',  -- low, normal, high, urgent
                    notes TEXT,
                    created_by VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by VARCHAR(100),
                    approved_at TIMESTAMP,
                    fulfilled_at TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            
            # Purchase orders table - for compras service integration
            cur.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    total_amount DECIMAL(12, 2),
                    status VARCHAR(50) DEFAULT 'pending',  -- pending, confirmed, shipped, received, cancelled
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
            
            # Stock alerts table - for logistica monitoring
            cur.execute("""
                CREATE TABLE IF NOT EXISTS stock_alerts (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER NOT NULL,
                    alert_type VARCHAR(50) NOT NULL,  -- below_minimum, stockout, overstock
                    current_quantity INTEGER,
                    threshold INTEGER,
                    severity VARCHAR(20) DEFAULT 'warning',  -- info, warning, critical
                    acknowledged BOOLEAN DEFAULT FALSE,
                    acknowledged_by VARCHAR(100),
                    acknowledged_at TIMESTAMP,
                    resolved BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)
            
        conn.commit()

def seed_items():
    """Seed with sample inventory items"""
    with get_db() as conn:
        with conn.cursor() as cur:
            # First, ensure suppliers exist
            cur.execute("SELECT COUNT(*) FROM suppliers")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO suppliers (name, contact_email, phone, city, country)
                    VALUES 
                        ('TechSupply Inc', 'sales@techsupply.com', '+1234567890', 'New York', 'USA'),
                        ('Industrial Parts Ltd', 'info@industrialparts.co.uk', '+442071234567', 'London', 'UK'),
                        ('Global Logistics Co', 'procurement@globallogistics.cn', '+86-10-1234-5678', 'Beijing', 'China')
                """)
            
            # Then seed items
            cur.execute("SELECT COUNT(*) FROM items")
            if cur.fetchone()[0] == 0:
                cur.execute("""
                    INSERT INTO items (sku, name, description, quantity_on_hand, minimum_threshold, 
                                       reorder_quantity, unit_cost, unit_of_measure, supplier_id, category)
                    VALUES
                        ('SKU-001', 'Laptop Dell XPS 13', 'High-performance laptop', 5, 3, 10, 1200.00, 'unidad', 1, 'Electrónica'),
                        ('SKU-002', 'Monitor LG 27 inch', 'Full HD Monitor', 12, 5, 15, 250.00, 'unidad', 1, 'Electrónica'),
                        ('SKU-003', 'Toner HP LaserJet', 'Black toner cartridge', 45, 10, 20, 45.00, 'unidad', 2, 'Suministros'),
                        ('SKU-004', 'Papel A4 80gsm', 'Resma de papel blanco', 120, 30, 50, 8.50, 'resma', 2, 'Suministros'),
                        ('SKU-005', 'Cable HDMI 2M', 'High-speed HDMI cable', 78, 20, 30, 5.99, 'unidad', 1, 'Accesorios'),
                        ('SKU-006', 'Mousepads Logitech', 'Ergonomic mouse pad', 35, 10, 25, 12.00, 'unidad', 1, 'Accesorios'),
                        ('SKU-007', 'Cinta adhesiva profesional', 'Industrial duct tape', 200, 50, 100, 2.50, 'rollo', 3, 'Suministros')
                """)
            
        conn.commit()

# Health check
@app.get("/health")
def health_check():
    """Service health check"""
    return {"status": "ok", "service": "inventario"}

# ============ ITEMS ENDPOINTS ============

@app.get("/items")
def list_items(
    user_name: str = Header(None),
    category: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """List all inventory items with optional filtering"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if category:
                cur.execute("""
                    SELECT id, sku, name, description, quantity_on_hand, minimum_threshold,
                           reorder_quantity, unit_cost, unit_of_measure, supplier_id, category,
                           active, last_updated
                    FROM items
                    WHERE category = %s AND active = TRUE
                    ORDER BY sku
                    LIMIT %s OFFSET %s
                """, (category, limit, skip))
            else:
                cur.execute("""
                    SELECT id, sku, name, description, quantity_on_hand, minimum_threshold,
                           reorder_quantity, unit_cost, unit_of_measure, supplier_id, category,
                           active, last_updated
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
                    "description": row[3],
                    "quantity_on_hand": row[4],
                    "minimum_threshold": row[5],
                    "reorder_quantity": row[6],
                    "unit_cost": float(row[7]),
                    "unit_of_measure": row[8],
                    "supplier_id": row[9],
                    "category": row[10],
                    "active": row[11],
                    "last_updated": row[12].isoformat() if row[12] else None,
                    "below_minimum": row[4] < row[5]  # Add computed flag
                })
            
            return items

@app.get("/items/{item_id}")
def get_item(item_id: int, user_name: str = Header(None)):
    """Get single item details"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, sku, name, description, quantity_on_hand, minimum_threshold,
                       reorder_quantity, unit_cost, unit_of_measure, supplier_id, category,
                       active, last_updated
                FROM items
                WHERE id = %s
            """, (item_id,))
            
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
                "unit_of_measure": row[8],
                "supplier_id": row[9],
                "category": row[10],
                "active": row[11],
                "last_updated": row[12].isoformat() if row[12] else None,
                "below_minimum": row[4] < row[5]
            }

@app.post("/items/{item_id}/stock/update")
def update_stock(
    item_id: int,
    quantity_change: int,
    reason: str,
    reference_id: Optional[str] = None,
    user_name: str = Header(None)
):
    """Update item stock quantity (positive for increase, negative for decrease)"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get current quantity
            cur.execute("SELECT quantity_on_hand FROM items WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Item not found")
            
            current_qty = row[0]
            new_qty = current_qty + quantity_change
            
            if new_qty < 0:
                raise HTTPException(status_code=400, detail="Insufficient stock")
            
            # Update item quantity
            cur.execute("""
                UPDATE items
                SET quantity_on_hand = %s, last_updated = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_qty, item_id))
            
            # Log stock movement
            movement_type = "in" if quantity_change > 0 else "out"
            cur.execute("""
                INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (item_id, movement_type, abs(quantity_change), reason, reference_id, user_name))
            
        conn.commit()
    
    return {"item_id": item_id, "new_quantity": new_qty, "change": quantity_change}

# ============ LOGISTICA REQUESTS ENDPOINTS ============

@app.get("/solicitudes-logistica")
def list_logistica_requests(
    user_name: str = Header(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """List all logistics requests (solicitudes de logistica)"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if status:
                cur.execute("""
                    SELECT id, item_id, requested_quantity, reason, status, priority, notes,
                           created_by, created_at, approved_by, approved_at, fulfilled_at
                    FROM solicitudes_logistica
                    WHERE status = %s
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (status, limit, skip))
            else:
                cur.execute("""
                    SELECT id, item_id, requested_quantity, reason, status, priority, notes,
                           created_by, created_at, approved_by, approved_at, fulfilled_at
                    FROM solicitudes_logistica
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                """, (limit, skip))
            
            requests = []
            for row in cur.fetchall():
                requests.append({
                    "id": row[0],
                    "item_id": row[1],
                    "requested_quantity": row[2],
                    "reason": row[3],
                    "status": row[4],
                    "priority": row[5],
                    "notes": row[6],
                    "created_by": row[7],
                    "created_at": row[8].isoformat() if row[8] else None,
                    "approved_by": row[9],
                    "approved_at": row[10].isoformat() if row[10] else None,
                    "fulfilled_at": row[11].isoformat() if row[11] else None,
                })
            
            return requests

@app.post("/solicitudes-logistica")
def create_logistica_request(
    item_id: int,
    requested_quantity: int,
    reason: str,
    priority: str = "normal",
    notes: Optional[str] = None,
    user_name: str = Header(None)
):
    """Create a new logistics request (auto-triggered when stock below minimum)"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Verify item exists
            cur.execute("SELECT id FROM items WHERE id = %s", (item_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")
            
            # Create solicitud
            cur.execute("""
                INSERT INTO solicitudes_logistica (item_id, requested_quantity, reason, priority, notes, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id, created_at
            """, (item_id, requested_quantity, reason, priority, notes, user_name))
            
            result = cur.fetchone()
            conn.commit()
            
            return {
                "id": result[0],
                "item_id": item_id,
                "requested_quantity": requested_quantity,
                "reason": reason,
                "priority": priority,
                "status": "pending",
                "created_by": user_name,
                "created_at": result[1].isoformat()
            }

@app.patch("/solicitudes-logistica/{request_id}/approve")
def approve_logistica_request(
    request_id: int,
    user_name: str = Header(None)
):
    """Approve a logistics request"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE solicitudes_logistica
                SET status = 'approved', approved_by = %s, approved_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'pending'
                RETURNING id, status
            """, (user_name, request_id))
            
            result = cur.fetchone()
            conn.commit()
            
            if not result:
                raise HTTPException(status_code=404, detail="Request not found or already processed")
            
            return {"id": result[0], "status": result[1]}

@app.patch("/solicitudes-logistica/{request_id}/fulfill")
def fulfill_logistica_request(
    request_id: int,
    user_name: str = Header(None)
):
    """Mark a logistics request as fulfilled"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE solicitudes_logistica
                SET status = 'fulfilled', fulfilled_at = CURRENT_TIMESTAMP
                WHERE id = %s AND status = 'approved'
                RETURNING id, status, item_id, requested_quantity
            """, (request_id,))
            
            result = cur.fetchone()
            conn.commit()
            
            if not result:
                raise HTTPException(status_code=404, detail="Request not found or not approved")
            
            return {
                "id": result[0],
                "status": result[1],
                "item_id": result[2],
                "requested_quantity": result[3]
            }

# ============ STOCK ALERTS ENDPOINTS ============

@app.get("/stock-alerts")
def list_stock_alerts(
    user_name: str = Header(None),
    unacknowledged_only: bool = Query(False)
):
    """List stock alerts for logistica monitoring"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            if unacknowledged_only:
                cur.execute("""
                    SELECT id, item_id, alert_type, current_quantity, threshold, severity,
                           acknowledged, created_at
                    FROM stock_alerts
                    WHERE acknowledged = FALSE AND resolved = FALSE
                    ORDER BY severity DESC, created_at DESC
                """)
            else:
                cur.execute("""
                    SELECT id, item_id, alert_type, current_quantity, threshold, severity,
                           acknowledged, created_at
                    FROM stock_alerts
                    WHERE resolved = FALSE
                    ORDER BY severity DESC, created_at DESC
                """)
            
            alerts = []
            for row in cur.fetchall():
                alerts.append({
                    "id": row[0],
                    "item_id": row[1],
                    "alert_type": row[2],
                    "current_quantity": row[3],
                    "threshold": row[4],
                    "severity": row[5],
                    "acknowledged": row[6],
                    "created_at": row[7].isoformat() if row[7] else None,
                })
            
            return alerts

@app.post("/stock-alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: int,
    user_name: str = Header(None)
):
    """Acknowledge a stock alert"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE stock_alerts
                SET acknowledged = TRUE, acknowledged_by = %s, acknowledged_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, acknowledged
            """, (user_name, alert_id))
            
            result = cur.fetchone()
            conn.commit()
            
            if not result:
                raise HTTPException(status_code=404, detail="Alert not found")
            
            return {"id": result[0], "acknowledged": result[1]}

# ============ SUPPLIERS ENDPOINTS ============

@app.get("/suppliers")
def list_suppliers(user_name: str = Header(None)):
    """List all suppliers"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, contact_email, phone, city, country, active
                FROM suppliers
                WHERE active = TRUE
                ORDER BY name
            """)
            
            suppliers = []
            for row in cur.fetchall():
                suppliers.append({
                    "id": row[0],
                    "name": row[1],
                    "contact_email": row[2],
                    "phone": row[3],
                    "city": row[4],
                    "country": row[5],
                    "active": row[6],
                })
            
            return suppliers

# ============ STARTUP ============

@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    initialize_database()
    seed_items()
