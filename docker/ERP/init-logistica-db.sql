-- Initialize database schema for logistica deliveries

CREATE TABLE IF NOT EXISTS deliveries (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL,
    delivery_address TEXT NOT NULL,
    assigned_to VARCHAR(255),
    vehicle VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    created_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    assigned_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ
);

-- Additional logistica tables for comprehensive testing
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
    supplier_id INTEGER,
    category VARCHAR(100),
    active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

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

CREATE TABLE IF NOT EXISTS stock_alerts (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    alert_type VARCHAR(50),
    current_quantity INTEGER,
    threshold INTEGER,
    severity VARCHAR(50),
    acknowledged BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS solicitudes_logistica (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id),
    requested_quantity INTEGER,
    reason VARCHAR(255),
    priority VARCHAR(50) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'pending',
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    fulfilled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deliveries_order_id ON deliveries(order_id);
CREATE INDEX IF NOT EXISTS idx_deliveries_status ON deliveries(status);
CREATE INDEX IF NOT EXISTS idx_items_sku ON items(sku);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_stock_alerts_item_id ON stock_alerts(item_id);
