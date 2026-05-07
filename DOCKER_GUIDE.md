# Docker Compose Setup Guide

## Auto-Initialization

The PostgreSQL service now automatically initializes the database with all microservice tables on first run.

**Initialization script:** `docker/ERP/init-all-microservices.sql`

This script creates tables for:
- ✓ Authentication (`auth_users`)
- ✓ Commercial (`suppliers`, `customers`, `purchase_orders`, `sales_orders`, `payment_records`)
- ✓ Inventory (`items`, `stock_movements`)
- ✓ Logistics (`deliveries`, `solicitudes_logistica`, `stock_alerts`)
- ✓ Finances (`report_files`, `app_users`)
- ✓ Payroll (`employees`, `attendance`, `payroll_records`)

---

## Common Operations

### 1. Start Only Database (for testing)
```bash
docker compose -f docker/ERP/docker-compose.yml up -d postgres
```

**Expected Output:**
```
postgres_1  | LOG: database system is ready to accept connections
```

Tables are created automatically on first run.

### 2. Start All Microservices
```bash
docker compose -f docker/ERP/docker-compose.yml up -d
```

Services will wait for postgres to be ready (via health check) before starting.

### 3. View Logs
```bash
docker compose -f docker/ERP/docker-compose.yml logs -f postgres
docker compose -f docker/ERP/docker-compose.yml logs -f logistica
```

### 4. Stop Services
```bash
docker compose -f docker/ERP/docker-compose.yml down
```

**Note:** Data persists in `postgres_data` volume

### 5. Clean Start (Delete All Data)
```bash
docker compose -f docker/ERP/docker-compose.yml down -v
```

**Then restart:**
```bash
docker compose -f docker/ERP/docker-compose.yml up -d postgres
```

---

## Database Reset (Python Script)

If you need to reset the database while postgres is running:

```bash
python reset_db.py
```

This will:
1. Drop all existing tables (after confirmation)
2. Recreate them from the init script
3. Preserve the postgres container

---

## Environment Variables

**Docker Compose uses values from `docker/ERP/.env`:**

```
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=transactions_db
POSTGRES_URL=postgresql://user:password@postgres:5432/transactions_db
DATABASE_URL=postgresql://user:password@postgres:5432/transactions_db
```

For local development (running tests outside docker), update connection strings to:
```
POSTGRES_URL=postgresql://user:password@localhost:5432/transactions_db
DATABASE_URL=postgresql://user:password@localhost:5432/transactions_db
```

---

## Troubleshooting

### "database already exists" error
This is normal on second run. The initialization script uses `CREATE TABLE IF NOT EXISTS`.

### Postgres takes too long to start
Postgres health check waits up to 5 attempts (50 seconds total). First startup can be slow.

Check logs:
```bash
docker compose -f docker/ERP/docker-compose.yml logs postgres
```

### "permission denied" on Windows volumes
Use absolute paths in docker-compose.yml volumes instead of relative paths if issues occur.

### Microservices fail to connect to postgres
1. Verify postgres is healthy: `docker compose ps postgres`
2. Check postgres logs: `docker compose logs postgres`
3. Verify POSTGRES_URL in `.env` matches docker network (use `postgres` hostname in docker-compose, `localhost` for local testing)

---

## File Structure

```
docker/ERP/
├── docker-compose.yml              # Main orchestration file
├── .env                            # Environment variables
├── .env.example                    # Template for new setups
├── init-all-microservices.sql      # Database initialization script
├── init-kafka-topics.sh            # Kafka topic setup (if used)
└── (other service files)
```

---

## Monitoring Database

### Connect directly to postgres:
```bash
psql -U user -h localhost -d transactions_db -c "SELECT version();"
```

### List all tables:
```bash
psql -U user -h localhost -d transactions_db -c "\dt"
```

### Check table contents:
```bash
psql -U user -h localhost -d transactions_db -c "SELECT * FROM deliveries LIMIT 10;"
```

---

## Next Steps

1. **Run integration tests:** `python run_integration_tests.py`
2. **Deploy full stack:** `docker compose -f docker/ERP/docker-compose.yml up -d`
3. **Access services:**
   - Finanzas: http://localhost:8000
   - Inventario: http://localhost:8001
   - Logística: http://localhost:8002
   - Compras: http://localhost:8003
   - Autenticación: http://localhost:8004
   - Nómina: http://localhost:8006

---

**Last Updated:** 2026-05-06  
**Status:** Auto-initialization enabled ✓
