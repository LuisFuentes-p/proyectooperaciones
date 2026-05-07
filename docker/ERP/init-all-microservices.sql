-- ============================================================================
-- COMPLETE DATABASE INITIALIZATION SCRIPT
-- All tables for all microservices (autenticacion, compras, inventario, 
-- logistica, finanzas, nomina)
-- ============================================================================

-- ============================================================================
-- AUTHENTICATION & USERS
-- ============================================================================

CREATE TABLE IF NOT EXISTS auth_users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- SUPPLIERS & CUSTOMERS
-- ============================================================================

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
);

CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    customer_type VARCHAR(50) DEFAULT 'retail',
    credit_limit DECIMAL(15, 2) DEFAULT 0.0,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INVENTORY ITEMS
-- ============================================================================

CREATE TABLE IF NOT EXISTS items (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    quantity_on_hand INTEGER DEFAULT 0,
    minimum_threshold INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 50,
    unit_cost DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2),
    unit_of_measure VARCHAR(50) DEFAULT 'unidad',
    supplier_id INTEGER REFERENCES suppliers(id),
    category VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PURCHASE ORDERS (COMPRAS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS purchase_orders (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'pending',
    expected_delivery_date DATE,
    requested_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_at TIMESTAMP,
    pdf_content BYTEA,
    pdf_filename VARCHAR(255)
);

-- ============================================================================
-- SALES ORDERS (COMPRAS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS sales_orders (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    total_amount DECIMAL(15, 2),
    status VARCHAR(50) DEFAULT 'pending',
    expected_delivery_date DATE,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fulfilled_at TIMESTAMP,
    invoice_content BYTEA,
    invoice_filename VARCHAR(255)
);

-- ============================================================================
-- PAYMENTS & TRANSACTIONS (COMPRAS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS payment_records (
    id SERIAL PRIMARY KEY,
    order_type VARCHAR(50),  -- 'purchase' or 'sale'
    order_id INTEGER,
    counterparty_type VARCHAR(50),  -- 'supplier' or 'customer'
    counterparty_name VARCHAR(255),
    amount DECIMAL(15, 2),
    payment_method VARCHAR(50),
    notes TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- STOCK MOVEMENTS (INVENTARIO)
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_movements (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    movement_type VARCHAR(50),  -- 'in', 'out', 'adjustment'
    quantity INTEGER NOT NULL,
    reason VARCHAR(255),
    reference_id INTEGER,  -- PO or SO id
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LOGISTICS: STOCK ALERTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS stock_alerts (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    alert_type VARCHAR(50),  -- 'below_minimum', 'stockout'
    current_quantity INTEGER,
    threshold INTEGER,
    severity VARCHAR(50),  -- 'warning', 'critical'
    acknowledged BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LOGISTICS: LOGISTICS REQUESTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS solicitudes_logistica (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    requested_quantity INTEGER,
    reason VARCHAR(255),
    priority VARCHAR(50) DEFAULT 'medium',  -- 'low', 'medium', 'high'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'fulfilled'
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    fulfilled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- LOGISTICS: DELIVERIES (ENTREGAS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,  -- Reference to sales_order or purchase_order
    delivery_address TEXT NOT NULL,
    assigned_to VARCHAR(255),  -- Driver name
    vehicle VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_transit', 'delivered'
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- ============================================================================
-- FINANCES: REPORT FILES
-- ============================================================================

CREATE TABLE IF NOT EXISTS report_files (
    id BIGSERIAL PRIMARY KEY,
    report_key TEXT NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_bytes BYTEA NOT NULL,
    file_size INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS app_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    role VARCHAR(100) DEFAULT 'viewer',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- PAYROLL (NÓMINA)
-- ============================================================================

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    role VARCHAR(100),
    salary DECIMAL(12, 2),
    hire_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attendance (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    attendance_date DATE NOT NULL,
    hours_worked DECIMAL(5, 2),
    status VARCHAR(50),  -- 'present', 'absent', 'late'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payroll_records (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    gross_salary DECIMAL(12, 2),
    deductions DECIMAL(12, 2) DEFAULT 0.0,
    net_salary DECIMAL(12, 2),
    payment_date DATE,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'paid'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_items_sku ON items(sku);
CREATE INDEX IF NOT EXISTS idx_items_supplier_id ON items(supplier_id);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier_id ON purchase_orders(supplier_id);
CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status);
CREATE INDEX IF NOT EXISTS idx_sales_orders_customer_id ON sales_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_deliveries_order_id ON deliveries(order_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_item_id ON stock_alerts(item_id);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_resolved ON stock_alerts(resolved);
CREATE INDEX IF NOT EXISTS idx_stock_movements_item_id ON stock_movements(item_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_logistica_item_id ON solicitudes_logistica(item_id);
CREATE INDEX IF NOT EXISTS idx_solicitudes_logistica_status ON solicitudes_logistica(status);
CREATE INDEX IF NOT EXISTS idx_payroll_records_employee_id ON payroll_records(employee_id);
CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username);

-- ============================================================================
-- SAMPLE DATA (IDEMPOTENT)
-- Seeds at least one example row for every table.
-- ============================================================================

INSERT INTO auth_users (id, username, password_hash)
VALUES
    (1, 'admin', 'demo-hash-admin'),
    (2, 'compras', 'demo-hash-compras'),
    (3, 'logistica', 'demo-hash-logistica')
ON CONFLICT (username) DO NOTHING;

INSERT INTO suppliers (id, name, contact_email, phone, city, country)
VALUES
    (1, 'TechSupply Inc', 'sales@techsupply.com', '+34-555-0001', 'Madrid', 'Spain'),
    (2, 'Global Parts Co', 'info@globalparts.com', '+34-555-0002', 'Barcelona', 'Spain')
ON CONFLICT (id) DO NOTHING;

INSERT INTO customers (id, name, contact_email, phone, city, country, customer_type, credit_limit)
VALUES
    (1, 'ABC Retail Store', 'manager@abc.com', '+34-555-1001', 'Madrid', 'Spain', 'retail', 5000.00),
    (2, 'Tech Solutions LLC', 'orders@techsolutions.com', '+34-555-1002', 'Valencia', 'Spain', 'wholesale', 25000.00)
ON CONFLICT (id) DO NOTHING;

INSERT INTO items (id, sku, name, description, quantity_on_hand, minimum_threshold, reorder_quantity, unit_cost, unit_price, unit_of_measure, supplier_id, category, active)
VALUES
    (1, 'SKU-001', 'Laptop Dell XPS', 'Business laptop', 15, 10, 20, 1200.00, 1500.00, 'unidad', 1, 'electronics', TRUE),
    (2, 'SKU-002', 'Wireless Mouse', 'Ergonomic wireless mouse', 50, 15, 30, 15.00, 25.00, 'unidad', 2, 'accessories', TRUE)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO purchase_orders (id, item_id, supplier_id, quantity, unit_price, total_amount, status, expected_delivery_date, requested_by, pdf_filename)
VALUES
    (1, 1, 1, 5, 1200.00, 6000.00, 'pending', CURRENT_DATE + INTERVAL '3 days', 'compras', 'po-1.pdf')
ON CONFLICT (id) DO NOTHING;

INSERT INTO sales_orders (id, item_id, customer_id, quantity, unit_price, total_amount, status, expected_delivery_date, created_by, invoice_filename)
VALUES
    (1, 1, 1, 2, 1500.00, 3000.00, 'confirmed', CURRENT_DATE + INTERVAL '2 days', 'ventas', 'invoice-1.pdf')
ON CONFLICT (id) DO NOTHING;

INSERT INTO payment_records (id, order_type, order_id, counterparty_type, counterparty_name, amount, payment_method, notes, created_by)
SELECT 1, 'sale', 1, 'customer', 'ABC Retail Store', 1500.00, 'transfer', 'partial payment', 'finanzas'
WHERE NOT EXISTS (SELECT 1 FROM payment_records WHERE id = 1);

INSERT INTO stock_movements (id, item_id, movement_type, quantity, reason, reference_id, created_by)
SELECT 1, 1, 'in', 5, 'purchase_received', 1, 'inventario'
WHERE NOT EXISTS (SELECT 1 FROM stock_movements WHERE id = 1);

INSERT INTO stock_alerts (id, item_id, alert_type, current_quantity, threshold, severity, acknowledged, resolved)
SELECT 1, 1, 'below_minimum', 8, 10, 'warning', FALSE, FALSE
WHERE NOT EXISTS (SELECT 1 FROM stock_alerts WHERE id = 1);

INSERT INTO solicitudes_logistica (id, item_id, requested_quantity, reason, priority, status, approved_by)
SELECT 1, 1, 20, 'restock', 'high', 'approved', 'logistica'
WHERE NOT EXISTS (SELECT 1 FROM solicitudes_logistica WHERE id = 1);

INSERT INTO deliveries (id, order_id, delivery_address, assigned_to, vehicle, status, created_by)
SELECT 1, 1, 'Calle Principal 123, Madrid', 'Juan Perez', 'Van-01', 'in_transit', 'logistica'
WHERE NOT EXISTS (SELECT 1 FROM deliveries WHERE id = 1);

INSERT INTO report_files (id, report_key, title, filename, content_type, file_bytes, file_size)
SELECT
    1,
    'ingresos_totales',
    'Reporte de Ingresos Totales',
    'ingresos_totales_demo.pdf',
    'application/pdf',
    convert_to('demo pdf content', 'UTF8'),
    octet_length(convert_to('demo pdf content', 'UTF8'))
WHERE NOT EXISTS (SELECT 1 FROM report_files WHERE id = 1);

INSERT INTO app_users (id, username, display_name, role)
VALUES
    (1, 'admin', 'Administrador', 'admin'),
    (2, 'viewer', 'Consulta General', 'viewer')
ON CONFLICT (username) DO NOTHING;

INSERT INTO employees (id, name, email, role, salary, hire_date, active)
VALUES
    (1, 'Maria Lopez', 'maria.lopez@empresa.com', 'analyst', 2200.00, CURRENT_DATE - INTERVAL '180 days', TRUE)
ON CONFLICT (id) DO NOTHING;

INSERT INTO attendance (id, employee_id, attendance_date, hours_worked, status)
SELECT 1, 1, CURRENT_DATE - INTERVAL '1 day', 8.0, 'present'
WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE id = 1);

INSERT INTO payroll_records (id, employee_id, period_start, period_end, gross_salary, deductions, net_salary, payment_date, status)
SELECT 1, 1, date_trunc('month', CURRENT_DATE)::date, (date_trunc('month', CURRENT_DATE) + INTERVAL '29 days')::date, 2200.00, 200.00, 2000.00, CURRENT_DATE, 'paid'
WHERE NOT EXISTS (SELECT 1 FROM payroll_records WHERE id = 1);

-- keep sequences aligned after explicit IDs
SELECT setval(pg_get_serial_sequence('auth_users', 'id'), COALESCE((SELECT MAX(id) FROM auth_users), 1), true);
SELECT setval(pg_get_serial_sequence('suppliers', 'id'), COALESCE((SELECT MAX(id) FROM suppliers), 1), true);
SELECT setval(pg_get_serial_sequence('customers', 'id'), COALESCE((SELECT MAX(id) FROM customers), 1), true);
SELECT setval(pg_get_serial_sequence('items', 'id'), COALESCE((SELECT MAX(id) FROM items), 1), true);
SELECT setval(pg_get_serial_sequence('purchase_orders', 'id'), COALESCE((SELECT MAX(id) FROM purchase_orders), 1), true);
SELECT setval(pg_get_serial_sequence('sales_orders', 'id'), COALESCE((SELECT MAX(id) FROM sales_orders), 1), true);
SELECT setval(pg_get_serial_sequence('payment_records', 'id'), COALESCE((SELECT MAX(id) FROM payment_records), 1), true);
SELECT setval(pg_get_serial_sequence('stock_movements', 'id'), COALESCE((SELECT MAX(id) FROM stock_movements), 1), true);
SELECT setval(pg_get_serial_sequence('stock_alerts', 'id'), COALESCE((SELECT MAX(id) FROM stock_alerts), 1), true);
SELECT setval(pg_get_serial_sequence('solicitudes_logistica', 'id'), COALESCE((SELECT MAX(id) FROM solicitudes_logistica), 1), true);
SELECT setval(pg_get_serial_sequence('deliveries', 'id'), COALESCE((SELECT MAX(id) FROM deliveries), 1), true);
SELECT setval(pg_get_serial_sequence('report_files', 'id'), COALESCE((SELECT MAX(id) FROM report_files), 1), true);
SELECT setval(pg_get_serial_sequence('app_users', 'id'), COALESCE((SELECT MAX(id) FROM app_users), 1), true);
SELECT setval(pg_get_serial_sequence('employees', 'id'), COALESCE((SELECT MAX(id) FROM employees), 1), true);
SELECT setval(pg_get_serial_sequence('attendance', 'id'), COALESCE((SELECT MAX(id) FROM attendance), 1), true);
SELECT setval(pg_get_serial_sequence('payroll_records', 'id'), COALESCE((SELECT MAX(id) FROM payroll_records), 1), true);

-- ============================================================================
-- DONE
-- ============================================================================
