#!/usr/bin/env python3
"""
Complete test and integration suite for microservicios project
Initializes database, runs tests, and validates cross-service flows
"""

import psycopg
import sys
import os
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# Test configuration
BASE_DIR = Path(__file__).resolve().parent
DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://user:password@localhost:5432/transactions_db")
SQL_INIT_FILE = BASE_DIR / "docker" / "ERP" / "init-all-microservices.sql"

@contextmanager
def get_db():
    conn = psycopg.connect(DB_URL)
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database with all necessary tables"""
    print("\n" + "=" * 70)
    print("STEP 1: INITIALIZING DATABASE SCHEMA")
    print("=" * 70)
    
    sql_file = SQL_INIT_FILE
    if not sql_file.exists():
        print(f"✗ Error: SQL file not found at {sql_file}")
        return False
    
    try:
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        
        print("✓ Database schema initialized successfully")
        return True
    
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False

def test_delivery_flow():
    """Test delivery CRUD operations"""
    print("\n" + "=" * 70)
    print("STEP 2: TESTING DELIVERY WORKFLOW")
    print("=" * 70)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Test 1: Create delivery
                print("\n[Test 1] Creating delivery...")
                cur.execute("""
                    INSERT INTO deliveries (order_id, delivery_address, status, created_by)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, status
                """, (10, "Calle Principal 123", "pending", "test_user"))
                d_id, status = cur.fetchone()
                assert status == "pending", f"Expected pending, got {status}"
                print(f"  ✓ Created delivery ID {d_id} with status {status}")
                
                # Test 2: Assign delivery
                print("[Test 2] Assigning driver and vehicle...")
                cur.execute("""
                    UPDATE deliveries 
                    SET assigned_to = %s, vehicle = %s, assigned_at = NOW()
                    WHERE id = %s
                    RETURNING assigned_to, vehicle
                """, ("Juan Pérez", "Van-01", d_id))
                assigned, vehicle = cur.fetchone()
                assert assigned == "Juan Pérez", f"Expected Juan Pérez, got {assigned}"
                print(f"  ✓ Assigned to {assigned}, vehicle {vehicle}")
                
                # Test 3: Update status to in_transit
                print("[Test 3] Updating status to in_transit...")
                cur.execute("""
                    UPDATE deliveries 
                    SET status = %s
                    WHERE id = %s
                    RETURNING status
                """, ("in_transit", d_id))
                status = cur.fetchone()[0]
                assert status == "in_transit"
                print(f"  ✓ Updated to {status}")
                
                # Test 4: Mark as delivered
                print("[Test 4] Marking delivery as completed...")
                cur.execute("""
                    UPDATE deliveries 
                    SET status = %s, delivered_at = NOW()
                    WHERE id = %s
                    RETURNING status, delivered_at
                """, ("delivered", d_id))
                status, delivered_at = cur.fetchone()
                assert status == "delivered"
                print(f"  ✓ Delivery completed at {delivered_at}")
                
                # Test 5: Retrieve full delivery record
                print("[Test 5] Retrieving delivery details...")
                cur.execute("""
                    SELECT id, order_id, delivery_address, assigned_to, vehicle, status
                    FROM deliveries WHERE id = %s
                """, (d_id,))
                row = cur.fetchone()
                assert row is not None
                print(f"  ✓ Retrieved: Order {row[1]} → {row[2]} | Driver: {row[3]} | Vehicle: {row[4]} | Status: {row[5]}")
            
            conn.commit()
        
        print("\n✓ All delivery tests passed!")
        return True
    
    except Exception as e:
        print(f"\n✗ Delivery test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_inventory_integration():
    """Test inventory-related operations"""
    print("\n" + "=" * 70)
    print("STEP 3: TESTING INVENTORY INTEGRATION")
    print("=" * 70)
    
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                # Create test supplier
                print("\n[Test 1] Creating supplier...")
                cur.execute("""
                    INSERT INTO suppliers (name, contact_email, phone)
                    VALUES (%s, %s, %s)
                    RETURNING id, name
                """, ("TechSupply Inc", "sales@techsupply.com", "+34-555-0123"))
                supplier_id, supplier_name = cur.fetchone()
                print(f"  ✓ Created supplier '{supplier_name}' (ID: {supplier_id})")
                
                # Create test item
                print("[Test 2] Creating inventory item...")
                cur.execute("""
                    INSERT INTO items (sku, name, quantity_on_hand, minimum_threshold, 
                                      reorder_quantity, unit_cost, unit_price, supplier_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, sku, name
                """, ("SKU-001", "Laptop Dell XPS", 15, 10, 50, 1200.0, 1500.0, supplier_id))
                item_id, sku, item_name = cur.fetchone()
                print(f"  ✓ Created item '{item_name}' (SKU: {sku}, Qty: 15)")
                
                # Create purchase order
                print("[Test 3] Creating purchase order...")
                cur.execute("""
                    INSERT INTO purchase_orders (item_id, supplier_id, quantity, unit_price, total_amount, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id, status
                """, (item_id, supplier_id, 10, 1200.0, 12000.0, "pending"))
                po_id, po_status = cur.fetchone()
                print(f"  ✓ Created PO ID {po_id} with status '{po_status}'")
                
                # Verify items below minimum
                print("[Test 4] Checking items below minimum threshold...")
                cur.execute("""
                    SELECT COUNT(*) FROM items 
                    WHERE quantity_on_hand < minimum_threshold AND active = TRUE
                """)
                below_min_count = cur.fetchone()[0]
                print(f"  ✓ Items below minimum threshold: {below_min_count}")
            
            conn.commit()
        
        print("\n✓ All inventory tests passed!")
        return True
    
    except Exception as e:
        print(f"\n✗ Inventory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_summary(init_ok, delivery_ok, inventory_ok):
    """Print test summary"""
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    tests = [
        ("Database Initialization", init_ok),
        ("Delivery Workflow", delivery_ok),
        ("Inventory Integration", inventory_ok),
    ]
    
    for test_name, passed in tests:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status:8} {test_name}")
    
    all_ok = all([init_ok, delivery_ok, inventory_ok])
    print("\n" + "=" * 70)
    
    if all_ok:
        print("✓ ALL TESTS PASSED!")
        print("=" * 70)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        return 1

def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  MICROSERVICIOS TEST SUITE - Database & Integration Tests".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    # Run all tests
    init_ok = init_database()
    delivery_ok = test_delivery_flow() if init_ok else False
    inventory_ok = test_inventory_integration() if init_ok else False
    
    # Print summary and exit
    return print_summary(init_ok, delivery_ok, inventory_ok)

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n✗ Test suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
