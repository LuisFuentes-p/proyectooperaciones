#!/usr/bin/env python3
import psycopg
import sys

sql_file = "docker/ERP/init-logistica-db.sql"

try:
    with open(sql_file, 'r') as f:
        sql = f.read()
    
    conn = psycopg.connect("postgresql://user:password@localhost:5432/transactions_db")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")
    sys.exit(0)
except FileNotFoundError:
    print(f"✗ SQL file not found: {sql_file}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
