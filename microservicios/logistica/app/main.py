"""
Logistica Microservice
- Monitors inventory stock levels
- Generates alerts when stock falls below minimum threshold
- Tracks logistics requests (restock, returns, damage)
- Coordinates with inventario service for stock updates
- Monitors purchase order fulfillment
"""

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import List, Optional
import psycopg
import os

app = FastAPI(title="Logistica Service", version="1.0.0")

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

# Health check
@app.get("/health")
def health_check():
    """Service health check"""
    return {"status": "ok", "service": "logistica"}

# ============ STOCK MONITORING ENDPOINTS ============

@app.get("/monitor/items-below-minimum")
def get_items_below_minimum(user_name: str = Header(None)):
    """Get all items currently below minimum threshold"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT i.id, i.sku, i.name, i.quantity_on_hand, i.minimum_threshold,
                       i.reorder_quantity, s.name as supplier_name, i.unit_cost
                FROM items i
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                WHERE i.quantity_on_hand < i.minimum_threshold AND i.active = TRUE
                ORDER BY (i.minimum_threshold - i.quantity_on_hand) DESC
            """)
            
            items = []
            for row in cur.fetchall():
                shortage = row[4] - row[3]  # minimum_threshold - quantity_on_hand
                items.append({
                    "id": row[0],
                    "sku": row[1],
                    "name": row[2],
                    "current_quantity": row[3],
                    "minimum_threshold": row[4],
                    "reorder_quantity": row[5],
                    "supplier_name": row[6],
                    "unit_cost": float(row[7]),
                    "shortage": shortage,
                    "needs_reorder": True,
                })
            
            return items

@app.get("/monitor/stockout-items")
def get_stockout_items(user_name: str = Header(None)):
    """Get items that are completely out of stock"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT i.id, i.sku, i.name, i.reorder_quantity, s.name as supplier_name,
                       i.minimum_threshold
                FROM items i
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                WHERE i.quantity_on_hand = 0 AND i.active = TRUE
                ORDER BY i.last_updated DESC
            """)
            
            items = []
            for row in cur.fetchall():
                items.append({
                    "id": row[0],
                    "sku": row[1],
                    "name": row[2],
                    "reorder_quantity": row[3],
                    "supplier_name": row[4],
                    "minimum_threshold": row[5],
                    "status": "STOCKOUT",
                    "urgency": "CRITICAL",
                })
            
            return items

@app.get("/monitor/stock-status-dashboard")
def get_stock_status_dashboard(user_name: str = Header(None)):
    """Get overall inventory health dashboard"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Overall stats
            cur.execute("""
                SELECT 
                    COUNT(*) as total_items,
                    COUNT(CASE WHEN quantity_on_hand = 0 THEN 1 END) as stockout_count,
                    COUNT(CASE WHEN quantity_on_hand < minimum_threshold THEN 1 END) as below_minimum_count,
                    SUM(quantity_on_hand * unit_cost) as total_inventory_value
                FROM items
                WHERE active = TRUE
            """)
            
            row = cur.fetchone()
            
            return {
                "total_items": row[0],
                "stockout_count": row[1] or 0,
                "below_minimum_count": row[2] or 0,
                "critical_items": row[1] or 0,
                "total_inventory_value": float(row[3]) if row[3] else 0.0,
                "timestamp": datetime.now().isoformat(),
            }

# ============ LOGISTICS REQUESTS ENDPOINTS ============

@app.get("/solicitudes/pending")
def get_pending_requests(user_name: str = Header(None)):
    """Get pending logistics requests"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sl.id, sl.item_id, sl.requested_quantity, sl.reason, sl.priority,
                       i.sku, i.name, i.quantity_on_hand, i.minimum_threshold, s.name
                FROM solicitudes_logistica sl
                JOIN items i ON sl.item_id = i.id
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                WHERE sl.status = 'pending'
                ORDER BY sl.priority DESC, sl.created_at ASC
            """)
            
            requests = []
            for row in cur.fetchall():
                requests.append({
                    "id": row[0],
                    "item_id": row[1],
                    "requested_quantity": row[2],
                    "reason": row[3],
                    "priority": row[4],
                    "item_sku": row[5],
                    "item_name": row[6],
                    "current_quantity": row[7],
                    "minimum_threshold": row[8],
                    "supplier_name": row[9],
                })
            
            return requests

@app.get("/solicitudes/in-progress")
def get_in_progress_requests(user_name: str = Header(None)):
    """Get approved logistics requests waiting for fulfillment"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sl.id, sl.item_id, sl.requested_quantity, sl.reason, sl.approved_by,
                       sl.approved_at, i.sku, i.name, s.name
                FROM solicitudes_logistica sl
                JOIN items i ON sl.item_id = i.id
                LEFT JOIN suppliers s ON i.supplier_id = s.id
                WHERE sl.status = 'approved'
                ORDER BY sl.approved_at ASC
            """)
            
            requests = []
            for row in cur.fetchall():
                days_waiting = (datetime.now() - row[5]).days if row[5] else 0
                requests.append({
                    "id": row[0],
                    "item_id": row[1],
                    "requested_quantity": row[2],
                    "reason": row[3],
                    "approved_by": row[4],
                    "approved_at": row[5].isoformat() if row[5] else None,
                    "item_sku": row[6],
                    "item_name": row[7],
                    "supplier_name": row[8],
                    "days_waiting": days_waiting,
                })
            
            return requests

@app.get("/solicitudes/completed")
def get_completed_requests(
    user_name: str = Header(None),
    days: int = Query(7)
):
    """Get recently completed logistics requests"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    cutoff_date = datetime.now() - timedelta(days=days)
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT sl.id, sl.item_id, sl.requested_quantity, sl.reason,
                       sl.fulfilled_at, i.sku, i.name
                FROM solicitudes_logistica sl
                JOIN items i ON sl.item_id = i.id
                WHERE sl.status = 'fulfilled' AND sl.fulfilled_at >= %s
                ORDER BY sl.fulfilled_at DESC
            """, (cutoff_date,))
            
            requests = []
            for row in cur.fetchall():
                requests.append({
                    "id": row[0],
                    "item_id": row[1],
                    "requested_quantity": row[2],
                    "reason": row[3],
                    "fulfilled_at": row[4].isoformat() if row[4] else None,
                    "item_sku": row[5],
                    "item_name": row[6],
                })
            
            return requests

# ============ AUTO-ALERTING ENDPOINTS ============

@app.post("/monitor/check-and-alert")
def check_and_create_alerts(user_name: str = Header(None)):
    """
    Check all items and create alerts for those below minimum.
    This would typically be called periodically (cron job).
    Returns count of new alerts created.
    """
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Find items below minimum threshold
            cur.execute("""
                SELECT id, quantity_on_hand, minimum_threshold, reorder_quantity
                FROM items
                WHERE quantity_on_hand < minimum_threshold AND active = TRUE
            """)
            
            alerts_created = 0
            
            for row in cur.fetchall():
                item_id = row[0]
                current_qty = row[1]
                minimum = row[2]
                reorder_qty = row[3]
                
                # Check if alert already exists (unresolved)
                cur.execute("""
                    SELECT id FROM stock_alerts
                    WHERE item_id = %s AND resolved = FALSE
                    AND alert_type = 'below_minimum'
                """, (item_id,))
                
                if not cur.fetchone():
                    # Create new alert
                    cur.execute("""
                        INSERT INTO stock_alerts 
                        (item_id, alert_type, current_quantity, threshold, severity)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (item_id, 'below_minimum', current_qty, minimum, 'warning'))
                    
                    # Also create a logistica request if none pending/approved
                    cur.execute("""
                        SELECT id FROM solicitudes_logistica
                        WHERE item_id = %s AND (status = 'pending' OR status = 'approved')
                    """, (item_id,))
                    
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO solicitudes_logistica 
                            (item_id, requested_quantity, reason, priority)
                            VALUES (%s, %s, %s, %s)
                        """, (item_id, reorder_qty, 'restock', 'high'))
                    
                    alerts_created += 1
                
                # Check for stockout (critical)
                if current_qty == 0:
                    cur.execute("""
                        SELECT id FROM stock_alerts
                        WHERE item_id = %s AND resolved = FALSE
                        AND alert_type = 'stockout'
                    """, (item_id,))
                    
                    if not cur.fetchone():
                        cur.execute("""
                            INSERT INTO stock_alerts 
                            (item_id, alert_type, current_quantity, threshold, severity)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (item_id, 'stockout', 0, minimum, 'critical'))
                        
                        alerts_created += 1
            
        conn.commit()
    
    return {
        "alerts_created": alerts_created,
        "timestamp": datetime.now().isoformat(),
        "message": f"Created {alerts_created} new stock alerts"
    }

# ============ PURCHASE ORDERS MONITORING ============

@app.get("/purchase-orders/pending")
def get_pending_purchase_orders(user_name: str = Header(None)):
    """Get pending purchase orders"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT po.id, po.item_id, po.quantity, po.unit_price, po.total_amount,
                       po.status, po.expected_delivery_date, i.sku, i.name, s.name
                FROM purchase_orders po
                JOIN items i ON po.item_id = i.id
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.status IN ('pending', 'confirmed', 'shipped')
                ORDER BY po.expected_delivery_date ASC
            """)
            
            orders = []
            for row in cur.fetchall():
                orders.append({
                    "id": row[0],
                    "item_id": row[1],
                    "quantity": row[2],
                    "unit_price": float(row[3]),
                    "total_amount": float(row[4]) if row[4] else None,
                    "status": row[5],
                    "expected_delivery": row[6].isoformat() if row[6] else None,
                    "item_sku": row[7],
                    "item_name": row[8],
                    "supplier_name": row[9],
                })
            
            return orders

@app.get("/purchase-orders/overdue")
def get_overdue_purchase_orders(user_name: str = Header(None)):
    """Get purchase orders that are overdue"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT po.id, po.item_id, po.quantity, po.expected_delivery_date,
                       po.created_at, i.sku, i.name, s.name
                FROM purchase_orders po
                JOIN items i ON po.item_id = i.id
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.status IN ('pending', 'confirmed', 'shipped')
                AND po.expected_delivery_date < CURRENT_DATE
                ORDER BY po.expected_delivery_date ASC
            """)
            
            orders = []
            for row in cur.fetchall():
                days_overdue = (datetime.now().date() - row[3]).days
                orders.append({
                    "id": row[0],
                    "item_id": row[1],
                    "quantity": row[2],
                    "expected_delivery": row[3].isoformat(),
                    "days_overdue": days_overdue,
                    "item_sku": row[5],
                    "item_name": row[6],
                    "supplier_name": row[7],
                })
            
            return orders
# ============ DELIVERIES (ENTREGAS) ============


@app.post("/deliveries")
def create_delivery(payload: dict, user_name: str = Header(None)):
    """Create a delivery record for an order"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    order_id = payload.get("order_id")
    delivery_address = payload.get("delivery_address")
    assigned_to = payload.get("assigned_to")
    vehicle = payload.get("vehicle")

    if not order_id or not delivery_address:
        raise HTTPException(status_code=400, detail="order_id and delivery_address required")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deliveries (order_id, delivery_address, assigned_to, vehicle, status, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW()) RETURNING id, status, created_at
                """,
                (order_id, delivery_address, assigned_to, vehicle, "pending", user_name),
            )
            row = cur.fetchone()
        conn.commit()

    return {"id": row[0], "status": row[1], "created_at": row[2].isoformat() if row[2] else None}


@app.patch("/deliveries/{delivery_id}/assign")
def assign_delivery(delivery_id: int, payload: dict, user_name: str = Header(None)):
    """Assign a driver and vehicle to a delivery"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    assigned_to = payload.get("assigned_to")
    vehicle = payload.get("vehicle")

    if not assigned_to and not vehicle:
        raise HTTPException(status_code=400, detail="assigned_to or vehicle required")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE deliveries SET assigned_to = %s, vehicle = %s, assigned_at = NOW() WHERE id = %s RETURNING id, assigned_to, vehicle",
                (assigned_to, vehicle, delivery_id),
            )
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return {"id": row[0], "assigned_to": row[1], "vehicle": row[2]}


@app.patch("/deliveries/{delivery_id}/status")
def update_delivery_status(delivery_id: int, payload: dict, user_name: str = Header(None)):
    """Update the status of a delivery (pending, in_transit, delivered)"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    new_status = payload.get("status")
    if new_status not in ("pending", "in_transit", "delivered"):
        raise HTTPException(status_code=400, detail="invalid status")

    with get_db() as conn:
        with conn.cursor() as cur:
            if new_status == "delivered":
                cur.execute(
                    "UPDATE deliveries SET status = %s, delivered_at = NOW() WHERE id = %s RETURNING id, status, delivered_at",
                    (new_status, delivery_id),
                )
            else:
                cur.execute(
                    "UPDATE deliveries SET status = %s WHERE id = %s RETURNING id, status",
                    (new_status, delivery_id),
                )
            row = cur.fetchone()
        conn.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Delivery not found")

    result = {"id": row[0], "status": row[1]}
    if len(row) >= 3 and row[2]:
        result["delivered_at"] = row[2].isoformat()
    return result


@app.get("/deliveries/{delivery_id}")
def get_delivery(delivery_id: int, user_name: str = Header(None)):
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, order_id, delivery_address, assigned_to, vehicle, status, created_by, created_at, assigned_at, delivered_at FROM deliveries WHERE id = %s", (delivery_id,))
            row = cur.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Delivery not found")

    return {
        "id": row[0],
        "order_id": row[1],
        "delivery_address": row[2],
        "assigned_to": row[3],
        "vehicle": row[4],
        "status": row[5],
        "created_by": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
        "assigned_at": row[8].isoformat() if row[8] else None,
        "delivered_at": row[9].isoformat() if row[9] else None,
    }


@app.get("/deliveries")
def list_deliveries(user_name: str = Header(None)):
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, order_id, delivery_address, assigned_to, vehicle, status FROM deliveries ORDER BY created_at DESC")
            rows = cur.fetchall()

    deliveries = []
    for row in rows:
        deliveries.append({
            "id": row[0],
            "order_id": row[1],
            "delivery_address": row[2],
            "assigned_to": row[3],
            "vehicle": row[4],
            "status": row[5],
        })

    return deliveries
