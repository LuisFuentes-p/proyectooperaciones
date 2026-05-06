"""
Compras Microservice
- Creates and manages purchase orders
- Generates PDF purchase orders for suppliers
- Tracks order status (pending, confirmed, shipped, received)
- Integrates with inventario service to update stock
- Handles supplier management
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
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
except ImportError:
    pass

app = FastAPI(title="Compras Service", version="1.0.0")

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

def generate_purchase_order_pdf(po_id: int, item_sku: str, item_name: str, 
                                quantity: int, unit_price: float, supplier_name: str,
                                supplier_email: str, expected_delivery: str):
    """Generate PDF for purchase order using ReportLab"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
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
    
    # PO Header Info
    info_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=6
    )
    
    elements.append(Paragraph(f"<b>Purchase Order #:</b> {po_id}", info_style))
    elements.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}", info_style))
    elements.append(Paragraph(f"<b>Expected Delivery:</b> {expected_delivery}", info_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Supplier Info
    elements.append(Paragraph("<b>Supplier Information:</b>", styles['Heading3']))
    elements.append(Paragraph(f"{supplier_name}", info_style))
    elements.append(Paragraph(f"Email: {supplier_email}", info_style))
    elements.append(Spacer(1, 0.3*inch))
    
    # Items Table
    elements.append(Paragraph("<b>Order Items:</b>", styles['Heading3']))
    
    table_data = [
        ['SKU', 'Item Name', 'Quantity', 'Unit Price', 'Total'],
        [item_sku, item_name, str(quantity), f'${unit_price:.2f}', f'${quantity * unit_price:.2f}']
    ]
    
    table = Table(table_data, colWidths=[1.2*inch, 2.5*inch, 1*inch, 1.2*inch, 1.1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    elements.append(Paragraph(f"<b>Total Amount:</b> ${quantity * unit_price:.2f}", 
                             ParagraphStyle('Summary', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor('#e74c3c'))))
    
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Thank you for your business!", ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER)))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# Health check
@app.get("/health")
def health_check():
    """Service health check"""
    return {"status": "ok", "service": "compras"}

# ============ PURCHASE ORDERS ENDPOINTS ============

@app.get("/purchase-orders")
def list_purchase_orders(
    user_name: str = Header(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """List purchase orders with optional status filter"""
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
    """Create a new purchase order"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Verify item and supplier exist
            cur.execute("SELECT sku, name FROM items WHERE id = %s", (item_id,))
            item_row = cur.fetchone()
            if not item_row:
                raise HTTPException(status_code=404, detail="Item not found")
            
            cur.execute("SELECT name, contact_email FROM suppliers WHERE id = %s", (supplier_id,))
            supplier_row = cur.fetchone()
            if not supplier_row:
                raise HTTPException(status_code=404, detail="Supplier not found")
            
            # Calculate total and expected delivery date
            total_amount = quantity * unit_price
            expected_delivery = (datetime.now() + timedelta(days=expected_delivery_days)).date()
            
            # Create purchase order
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
            created_at = result[1]
            
            # Generate PDF
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
                
                # Save PDF to database
                pdf_filename = f"PO-{po_id}-{item_row[0]}.pdf"
                cur.execute("""
                    UPDATE purchase_orders
                    SET pdf_content = %s, pdf_filename = %s
                    WHERE id = %s
                """, (pdf_content, pdf_filename, po_id))
            except Exception as e:
                print(f"Error generating PDF: {str(e)}")
                # Continue without PDF if generation fails
            
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
                "created_at": created_at.isoformat(),
                "requested_by": user_name,
            }

@app.get("/purchase-orders/{po_id}")
def get_purchase_order(po_id: int, user_name: str = Header(None)):
    """Get details of a single purchase order"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT po.id, po.item_id, po.supplier_id, po.quantity, po.unit_price,
                       po.total_amount, po.status, po.created_at, po.expected_delivery_date,
                       po.requested_by, i.sku, i.name, s.name, s.contact_email
                FROM purchase_orders po
                JOIN items i ON po.item_id = i.id
                JOIN suppliers s ON po.supplier_id = s.id
                WHERE po.id = %s
            """, (po_id,))
            
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
            
            pdf_content = row[0]
            pdf_filename = row[1] or f"purchase-order-{po_id}.pdf"
            
            return FileResponse(
                BytesIO(pdf_content),
                media_type="application/pdf",
                filename=pdf_filename
            )

@app.patch("/purchase-orders/{po_id}/status")
def update_purchase_order_status(
    po_id: int,
    new_status: str,
    user_name: str = Header(None)
):
    """Update purchase order status (pending, confirmed, shipped, received, cancelled)"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    valid_statuses = ['pending', 'confirmed', 'shipped', 'received', 'cancelled']
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            # Get purchase order details
            cur.execute("""
                SELECT item_id, quantity, status
                FROM purchase_orders
                WHERE id = %s
            """, (po_id,))
            
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Purchase order not found")
            
            item_id, quantity, old_status = row
            
            # Update PO status
            cur.execute("""
                UPDATE purchase_orders
                SET status = %s
                WHERE id = %s
                RETURNING status
            """, (new_status, po_id))
            
            # If status is "received", update inventory stock
            if new_status == 'received' and old_status != 'received':
                cur.execute("""
                    UPDATE items
                    SET quantity_on_hand = quantity_on_hand + %s, last_updated = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (quantity, item_id))
                
                # Log stock movement
                cur.execute("""
                    INSERT INTO stock_movements (item_id, movement_type, quantity, reason, reference_id, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (item_id, 'in', quantity, 'purchase_order_received', f'PO-{po_id}', user_name))
            
            conn.commit()
            
            return {
                "id": po_id,
                "status": new_status,
                "updated_at": datetime.now().isoformat(),
                "stock_updated": new_status == 'received' and old_status != 'received'
            }

# ============ STATISTICS ENDPOINTS ============

@app.get("/stats/order-summary")
def get_order_summary(user_name: str = Header(None)):
    """Get purchase order summary statistics"""
    if not user_name:
        raise HTTPException(status_code=403, detail="User not identified")
    
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    status,
                    COUNT(*) as count,
                    COALESCE(SUM(total_amount), 0) as total_value
                FROM purchase_orders
                GROUP BY status
            """)
            
            summary = {}
            for row in cur.fetchall():
                status = row[0]
                count = row[1]
                total_value = float(row[2])
                summary[status] = {
                    "count": count,
                    "total_value": total_value
                }
            
            return summary
