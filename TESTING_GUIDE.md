# Testing Guide - Microservicios Project

## Quick Start

### 1. Prerequisites
- Docker & Docker Compose installed
- PostgreSQL running via docker-compose (automatic initialization)
- Python 3.10+ with psycopg installed

### 2. Start Services

**Start postgres (database auto-initializes with all tables)**
```bash
docker compose -f docker/ERP/docker-compose.yml up -d postgres
```

The initialization script (`init-all-microservices.sql`) runs automatically and creates:
- ✓ All tables for autenticacion, compras, inventario, logistica, finanzas, nomina
- ✓ Foreign key relationships
- ✓ Performance indexes

**Start all microservices** (optional, requires all dependencies)
```bash
docker compose -f docker/ERP/docker-compose.yml up -d
```

### 3. Run Integration Tests

**Option A: Using batch file (Windows)**
```bash
run_tests.bat
```

**Option B: Direct Python execution**
```bash
python run_integration_tests.py
```

This will:
1. Verify postgres is running
2. Test delivery workflow (create → assign → update status → retrieve)
3. Test inventory integration (suppliers → items → purchase orders)
4. Print detailed results for each test

---

## What Was Implemented

### A. Delivery Endpoints (Logística Microservice)

New endpoints added to `microservicios/logistica/app/main.py`:

```python
POST   /deliveries              # Create new delivery
PATCH  /deliveries/{id}/assign  # Assign driver & vehicle
PATCH  /deliveries/{id}/status  # Update delivery status (pending|in_transit|delivered)
GET    /deliveries/{id}         # Get delivery details
GET    /deliveries              # List all deliveries
```

**Covers HU-LOG-01, HU-LOG-02, HU-LOG-03:**
- Create órdenes de entrega (HU-LOG-01)
- Assign conductores y vehículos (HU-LOG-02)
- Update estados de entrega (HU-LOG-03)

### B. Database Schema

Created `docker/ERP/init-logistica-db.sql` with:
- `deliveries` table (order_id, delivery_address, assigned_to, vehicle, status)
- `items`, `suppliers`, `purchase_orders`, `stock_alerts`, `solicitudes_logistica` tables
- Proper indexes for performance

### C. Integration Tests

Created `run_integration_tests.py` that tests:

**Delivery Workflow:**
- ✓ Create delivery with order_id and address
- ✓ Assign driver and vehicle
- ✓ Update status progression (pending → in_transit → delivered)
- ✓ Retrieve delivery details

**Inventory Integration:**
- ✓ Create suppliers
- ✓ Create inventory items
- ✓ Create purchase orders
- ✓ Check items below minimum threshold

### D. Connection String Standardization

Updated all microservices to use `POSTGRES_URL` with fallback:

```python
DATABASE_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/transactions_db"))
```

Applied to:
- ✓ autenticacion
- ✓ compras
- ✓ inventario
- ✓ logistica
- ✓ finanzas

---

## Running Individual Service Tests

### Test Logística Endpoints
```bash
python -m pytest microservicios/logistica/tests/test_main.py -v
```

### Test Compras (Sales/Purchases)
```bash
python -m pytest microservicios/compras/tests/test_main.py -v
```

### Test All Microservices
```bash
python -m pytest microservicios/ -v
```

---

## Database Connection

**Connection String Format:**
```
postgresql://user:password@localhost:5432/transactions_db
```

**Environment Variables (in docker/ERP/.env):**
```
DB_USER=user
DB_PASSWORD=password
DB_NAME=transactions_db
POSTGRES_URL=postgresql://user:password@localhost:5432/transactions_db  # NEW
DATABASE_URL=postgresql://user:password@localhost:5432/transactions_db  # LEGACY
```

---

## Troubleshooting

### PostgreSQL Connection Failed
```
Error: Cannot connect to PostgreSQL at localhost:5432
```
**Solution:** Ensure postgres is running:
```bash
docker compose -f docker/ERP/docker-compose.yml ps postgres
```

### Module Not Found
```
ModuleNotFoundError: No module named 'psycopg'
```
**Solution:** Install dependencies:
```bash
pip install psycopg[binary] fastapi httpx
```

### Syntax Errors in Tests
If you encounter syntax errors, ensure you're using Python 3.10+:
```bash
python --version
```

---

## Next Steps

1. **Run the integration test suite** using `run_tests.bat` or `python run_integration_tests.py`
2. **Update docker-compose.yml** to add `POSTGRES_URL` environment variable
3. **Update GitHub Actions workflow** if needed (`.github/workflows/microservices-tests.yml`)
4. **Deploy to Docker** using docker-compose for full stack testing

---

## Files Modified/Created

**Modified:**
- `microservicios/*/app/main.py` (5 files) — DB connection standardization
- `microservicios/logistica/app/main.py` — Added delivery endpoints

**Created:**
- `docker/ERP/init-logistica-db.sql` — Database schema initialization
- `run_integration_tests.py` — Comprehensive test suite
- `run_tests.bat` — Windows batch runner
- `microservicios/logistica/tests/test_deliveries.py` — Unit tests for deliveries

---

Generated: 2026-05-06 | Status: Ready for Testing
