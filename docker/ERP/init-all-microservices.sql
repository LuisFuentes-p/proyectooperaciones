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
-- SAMPLE DATA (OPTIONAL - uncomment to populate test data)
-- ============================================================================

-- INSERT INTO suppliers (name, contact_email, phone) VALUES 
-- ('TechSupply Inc', 'sales@techsupply.com', '+34-555-0001'),
-- ('Global Parts Co', 'info@globalparts.com', '+34-555-0002'),
-- ('LocalVendor Ltd', 'contact@localvendor.com', '+34-555-0003');

-- INSERT INTO customers (name, contact_email, phone, customer_type) VALUES 
-- ('ABC Retail Store', 'manager@abc.com', '+34-555-1001', 'retail'),
-- ('Tech Solutions LLC', 'orders@techsolutions.com', '+34-555-1002', 'wholesale'),
-- ('Direct Customer Inc', 'buyer@directcustomer.com', '+34-555-1003', 'retail');

-- INSERT INTO auth_users (username, password_hash) VALUES
-- ('admin', '$2b$12$...hashed_password...'),
-- ('user1', '$2b$12$...hashed_password...'),
-- ('logistica', '$2b$12$...hashed_password...');

-- ============================================================================
-- DONE
-- ============================================================================
