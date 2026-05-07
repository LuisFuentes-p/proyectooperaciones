#!/usr/bin/env python3
"""
Database reset utility - Drop all tables and reinitialize
Useful for testing or cleaning up after failed migrations
"""

import psycopg
import sys
from pathlib import Path

DB_URL = "postgresql://user:password@localhost:5432/transactions_db"
SQL_INIT_FILE = "docker/ERP/init-all-microservices.sql"

def reset_database():
    """Drop all tables and reinitialize database"""
    print("\n" + "=" * 70)
    print("DATABASE RESET & REINITIALIZATION")
    print("=" * 70)
    print("\n⚠️  WARNING: This will DROP all existing tables and data!")
    print("This is useful for testing or cleaning up after failed migrations.\n")
    
    response = input("Continue? (type 'yes' to confirm): ")
    if response.lower() != 'yes':
        print("✗ Reset cancelled")
        return False
    
    sql_file = Path(SQL_INIT_FILE)
    if not sql_file.exists():
        print(f"✗ Error: SQL file not found at {sql_file}")
        return False
    
    try:
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                # Drop all tables in reverse order of dependencies
                print("\nDropping existing tables...")
                tables = [
                    "payroll_records", "attendance", "employees",
                    "app_users", "report_files",
                    "deliveries", "solicitudes_logistica", "stock_alerts", "stock_movements",
                    "payment_records", "sales_orders", "purchase_orders",
                    "items", "customers", "suppliers",
                    "auth_users"
                ]
                
                for table in tables:
                    cur.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    print(f"  ✓ Dropped {table}")
                
                conn.commit()
        
        print("\nReinitializing database...")
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        with psycopg.connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        
        print("  ✓ All tables recreated successfully")
        print("\n✓ Database reset and reinitialized!")
        return True
    
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = reset_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Reset cancelled by user")
        sys.exit(1)
