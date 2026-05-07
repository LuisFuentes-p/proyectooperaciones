#!/usr/bin/env python3
"""
Test runner: Initialize DB and run integration tests
"""
import psycopg
import subprocess
import sys
from pathlib import Path

def init_db():
    """Initialize database schema"""
    print("=" * 60)
    print("Initializing database schema...")
    print("=" * 60)
    
    sql_file = Path("docker/ERP/init-logistica-db.sql")
    if not sql_file.exists():
        print(f"✗ SQL file not found: {sql_file}")
        return False
    
    try:
        with open(sql_file, 'r') as f:
            sql = f.read()
        
        conn = psycopg.connect("postgresql://user:password@localhost:5432/transactions_db")
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        conn.close()
        print("✓ Database schema initialized successfully\n")
        return True
    except Exception as e:
        print(f"✗ Error initializing database: {e}\n")
        return False

def run_tests():
    """Run pytest suite"""
    print("=" * 60)
    print("Running test suite...")
    print("=" * 60 + "\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", 
         "microservicios/logistica/tests/test_main.py",
         "microservicios/compras/tests/test_main.py",
        ],
        cwd=str(Path.cwd())
    )
    
    return result.returncode == 0

if __name__ == "__main__":
    if not init_db():
        sys.exit(1)
    
    if not run_tests():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ All tasks completed successfully!")
    print("=" * 60)
