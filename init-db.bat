@echo off
REM Initialize postgres with logistica schema
psql -U user -h localhost -d transactions_db -f docker\ERP\init-logistica-db.sql
pause
