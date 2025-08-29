-- eBay Manager Database Schema
-- Following SOLID/YAGNI principles for 30-account scale
-- Complete PostgreSQL schema with relationships and constraints

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Set timezone
SET timezone = 'UTC';

-- ================================================
-- UTILITY FUNCTIONS
-- ================================================

-- Update trigger function for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ================================================
-- CORE TABLES
-- ================================================

-- 1. Users Table (Authentication & User Management)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    
    -- Authentication Fields
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL, 
    password_hash VARCHAR(255) NOT NULL,
    
    -- User Information  
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    
    -- Account Status
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    last_login TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT users_username_length CHECK (length(username) >= 3),
    CONSTRAINT users_email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Users table indexes
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email); 
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Update trigger for users
CREATE TRIGGER users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2. Accounts Table (eBay Account Management)
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    
    -- User Association
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- eBay Account Information
    ebay_account_name VARCHAR(100) NOT NULL,
    ebay_store_name VARCHAR(100),
    ebay_user_id VARCHAR(50) UNIQUE, -- eBay internal user ID
    
    -- Account Configuration
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Business Information
    business_name VARCHAR(100),
    contact_email VARCHAR(100),
    phone_number VARCHAR(20),
    
    -- Account Settings
    auto_sync BOOLEAN DEFAULT true,
    sync_frequency INTEGER DEFAULT 30, -- minutes
    last_sync TIMESTAMPTZ,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT accounts_ebay_name_length CHECK (length(ebay_account_name) >= 3),
    CONSTRAINT accounts_currency_format CHECK (currency ~* '^[A-Z]{3}$'),
    CONSTRAINT accounts_sync_frequency_positive CHECK (sync_frequency > 0)
);

-- Accounts table indexes
CREATE INDEX idx_accounts_user_id ON accounts(user_id);
CREATE INDEX idx_accounts_ebay_account_name ON accounts(ebay_account_name);
CREATE INDEX idx_accounts_status ON accounts(status);
CREATE INDEX idx_accounts_last_sync ON accounts(last_sync);
CREATE INDEX idx_accounts_created_at ON accounts(created_at);

-- Update trigger for accounts
CREATE TRIGGER accounts_updated_at BEFORE UPDATE ON accounts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 3. Suppliers Table (Supplier Management)
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    
    -- Account Association  
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Supplier Information
    name VARCHAR(100) NOT NULL,
    company_name VARCHAR(100),
    
    -- Contact Information
    contact_person VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    website VARCHAR(200),
    
    -- Address Information
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    postal_code VARCHAR(20),
    country VARCHAR(50),
    
    -- Business Information
    tax_id VARCHAR(50),
    currency VARCHAR(3) DEFAULT 'USD',
    payment_terms VARCHAR(100), -- "Net 30", "COD", etc.
    minimum_order DECIMAL(10, 2) DEFAULT 0,
    
    -- Supplier Performance
    reliability_rating INTEGER CHECK (reliability_rating >= 1 AND reliability_rating <= 5),
    quality_rating INTEGER CHECK (quality_rating >= 1 AND quality_rating <= 5),
    
    -- Status & Configuration
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'suspended')),
    is_preferred BOOLEAN DEFAULT false,
    
    -- Notes & Additional Info
    notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT suppliers_name_length CHECK (length(name) >= 2),
    CONSTRAINT suppliers_account_name_unique UNIQUE (account_id, name),
    CONSTRAINT suppliers_email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT suppliers_minimum_order_positive CHECK (minimum_order >= 0)
);

-- Suppliers table indexes
CREATE INDEX idx_suppliers_account_id ON suppliers(account_id);
CREATE INDEX idx_suppliers_name ON suppliers(name);
CREATE INDEX idx_suppliers_status ON suppliers(status);
CREATE INDEX idx_suppliers_is_preferred ON suppliers(is_preferred);
CREATE INDEX idx_suppliers_reliability ON suppliers(reliability_rating);
CREATE INDEX idx_suppliers_created_at ON suppliers(created_at);

-- Update trigger for suppliers
CREATE TRIGGER suppliers_updated_at BEFORE UPDATE ON suppliers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4. Products Table (Product Catalog)
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    
    -- Account & Supplier Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
    
    -- Product Identification
    sku VARCHAR(50) NOT NULL, -- Internal SKU
    supplier_sku VARCHAR(50), -- Supplier's SKU
    upc VARCHAR(20),
    ean VARCHAR(20),
    
    -- Product Information
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    brand VARCHAR(100),
    model VARCHAR(100),
    
    -- Physical Properties
    weight_oz DECIMAL(8, 2),
    dimensions_length DECIMAL(8, 2),
    dimensions_width DECIMAL(8, 2), 
    dimensions_height DECIMAL(8, 2),
    color VARCHAR(50),
    size VARCHAR(50),
    
    -- Financial Information
    cost_price DECIMAL(10, 2) NOT NULL,
    wholesale_price DECIMAL(10, 2),
    retail_price DECIMAL(10, 2),
    ebay_price DECIMAL(10, 2),
    
    -- Inventory Management
    stock_quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (stock_quantity - reserved_quantity) STORED,
    reorder_point INTEGER DEFAULT 5,
    reorder_quantity INTEGER DEFAULT 20,
    
    -- Product Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'discontinued')),
    is_fragile BOOLEAN DEFAULT false,
    requires_adult_signature BOOLEAN DEFAULT false,
    
    -- Additional Information
    notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT products_sku_length CHECK (length(sku) >= 3),
    CONSTRAINT products_account_sku_unique UNIQUE (account_id, sku),
    CONSTRAINT products_name_length CHECK (length(name) >= 3),
    CONSTRAINT products_cost_price_positive CHECK (cost_price > 0),
    CONSTRAINT products_stock_non_negative CHECK (stock_quantity >= 0),
    CONSTRAINT products_reserved_non_negative CHECK (reserved_quantity >= 0),
    CONSTRAINT products_reorder_positive CHECK (reorder_point >= 0 AND reorder_quantity > 0)
);

-- Products table indexes
CREATE INDEX idx_products_account_id ON products(account_id);
CREATE INDEX idx_products_supplier_id ON products(supplier_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_available_quantity ON products(available_quantity);
CREATE INDEX idx_products_reorder_point ON products(reorder_point);
CREATE INDEX idx_products_created_at ON products(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_products_account_status ON products(account_id, status);
CREATE INDEX idx_products_account_category ON products(account_id, category);
CREATE INDEX idx_products_low_stock ON products(account_id, available_quantity) WHERE available_quantity <= reorder_point;

-- Update trigger for products
CREATE TRIGGER products_updated_at BEFORE UPDATE ON products 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. Orders Table (eBay Order Management)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- eBay Order Information
    ebay_order_id VARCHAR(50) NOT NULL, -- eBay internal order ID
    ebay_transaction_id VARCHAR(50),
    
    -- Order Details
    buyer_username VARCHAR(100),
    buyer_email VARCHAR(100),
    
    -- Financial Information
    total_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    payment_status VARCHAR(20) DEFAULT 'pending',
    
    -- Order Status & Workflow
    order_status VARCHAR(20) DEFAULT 'pending' CHECK (
        order_status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded')
    ),
    
    -- Shipping Information
    shipping_address_line1 VARCHAR(200),
    shipping_address_line2 VARCHAR(200),
    shipping_city VARCHAR(100),
    shipping_state VARCHAR(50),
    shipping_postal_code VARCHAR(20),
    shipping_country VARCHAR(50),
    shipping_method VARCHAR(50),
    tracking_number VARCHAR(100),
    
    -- Important Dates
    order_date TIMESTAMPTZ NOT NULL,
    payment_date TIMESTAMPTZ,
    shipped_date TIMESTAMPTZ,
    delivered_date TIMESTAMPTZ,
    
    -- Additional Information
    buyer_notes TEXT,
    seller_notes TEXT,
    
    -- CSV Import Metadata
    import_batch_id UUID,
    import_filename VARCHAR(255),
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT orders_total_positive CHECK (total_amount > 0),
    CONSTRAINT orders_ebay_order_account_unique UNIQUE (account_id, ebay_order_id),
    CONSTRAINT orders_currency_format CHECK (currency ~* '^[A-Z]{3}$'),
    CONSTRAINT orders_order_date_reasonable CHECK (order_date >= '2020-01-01' AND order_date <= CURRENT_TIMESTAMP + INTERVAL '1 day')
);

-- Orders table indexes
CREATE INDEX idx_orders_account_id ON orders(account_id);
CREATE INDEX idx_orders_ebay_order_id ON orders(ebay_order_id);
CREATE INDEX idx_orders_buyer_username ON orders(buyer_username);
CREATE INDEX idx_orders_order_status ON orders(order_status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_order_date ON orders(order_date);
CREATE INDEX idx_orders_tracking_number ON orders(tracking_number);
CREATE INDEX idx_orders_import_batch ON orders(import_batch_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_orders_account_status ON orders(account_id, order_status);
CREATE INDEX idx_orders_account_date ON orders(account_id, order_date);

-- Update trigger for orders
CREATE TRIGGER orders_updated_at BEFORE UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6. Order Items Table (Order Line Items)
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    
    -- Order Association
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    
    -- Product Information (may be NULL if product deleted)
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    
    -- eBay Item Information
    ebay_item_id VARCHAR(50), -- eBay item ID at time of sale
    ebay_transaction_id VARCHAR(50),
    
    -- Item Details (captured at time of sale)
    item_title VARCHAR(200) NOT NULL,
    item_sku VARCHAR(50),
    item_condition VARCHAR(50),
    
    -- Quantity & Pricing
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
    
    -- Cost Information (for profit calculation)
    unit_cost DECIMAL(10, 2), -- Cost at time of sale
    total_cost DECIMAL(10, 2) GENERATED ALWAYS AS (quantity * COALESCE(unit_cost, 0)) STORED,
    profit_amount DECIMAL(10, 2) GENERATED ALWAYS AS (total_price - total_cost) STORED,
    
    -- Item Status
    item_status VARCHAR(20) DEFAULT 'pending' CHECK (
        item_status IN ('pending', 'processing', 'shipped', 'delivered', 'returned', 'refunded')
    ),
    
    -- Shipping Information (item-level)
    tracking_number VARCHAR(100),
    shipped_date TIMESTAMPTZ,
    delivered_date TIMESTAMPTZ,
    
    -- Notes
    notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT order_items_unit_price_positive CHECK (unit_price > 0),
    CONSTRAINT order_items_unit_cost_non_negative CHECK (unit_cost IS NULL OR unit_cost >= 0),
    CONSTRAINT order_items_title_length CHECK (length(item_title) >= 5)
);

-- Order items indexes
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_ebay_item_id ON order_items(ebay_item_id);
CREATE INDEX idx_order_items_item_sku ON order_items(item_sku);
CREATE INDEX idx_order_items_item_status ON order_items(item_status);
CREATE INDEX idx_order_items_tracking_number ON order_items(tracking_number);
CREATE INDEX idx_order_items_shipped_date ON order_items(shipped_date);
CREATE INDEX idx_order_items_created_at ON order_items(created_at);

-- Update trigger for order items
CREATE TRIGGER order_items_updated_at BEFORE UPDATE ON order_items 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 7. Listings Table (eBay Listing Management)
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- eBay Listing Information
    ebay_item_id VARCHAR(50) NOT NULL, -- eBay item ID
    ebay_listing_id VARCHAR(50), -- eBay listing ID
    
    -- Listing Details
    title VARCHAR(80) NOT NULL, -- eBay title limit
    subtitle VARCHAR(55), -- eBay subtitle limit
    description TEXT,
    category_id INTEGER,
    category_name VARCHAR(100),
    
    -- Listing Configuration  
    listing_format VARCHAR(20) DEFAULT 'FixedPrice' CHECK (
        listing_format IN ('FixedPrice', 'Auction', 'StoreInventory')
    ),
    
    -- Pricing Information
    start_price DECIMAL(10, 2),
    buy_it_now_price DECIMAL(10, 2),
    current_price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Quantity & Inventory
    quantity_total INTEGER DEFAULT 1,
    quantity_available INTEGER DEFAULT 1,
    quantity_sold INTEGER DEFAULT 0,
    
    -- Listing Status
    listing_status VARCHAR(20) DEFAULT 'draft' CHECK (
        listing_status IN ('draft', 'active', 'ended', 'sold', 'cancelled')
    ),
    
    -- Important Dates & Duration
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    listing_duration INTEGER, -- days
    
    -- Listing Performance
    view_count INTEGER DEFAULT 0,
    watch_count INTEGER DEFAULT 0,
    question_count INTEGER DEFAULT 0,
    
    -- Shipping Information
    shipping_cost DECIMAL(8, 2) DEFAULT 0,
    free_shipping BOOLEAN DEFAULT false,
    returns_accepted BOOLEAN DEFAULT true,
    return_period INTEGER DEFAULT 30, -- days
    
    -- Additional Information
    condition_name VARCHAR(50) DEFAULT 'New',
    location VARCHAR(100),
    
    -- CSV Import Metadata
    import_batch_id UUID,
    import_filename VARCHAR(255),
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT listings_ebay_item_account_unique UNIQUE (account_id, ebay_item_id),
    CONSTRAINT listings_title_length CHECK (length(title) >= 10 AND length(title) <= 80),
    CONSTRAINT listings_start_price_positive CHECK (start_price IS NULL OR start_price > 0),
    CONSTRAINT listings_quantity_non_negative CHECK (quantity_total >= 0 AND quantity_available >= 0),
    CONSTRAINT listings_shipping_non_negative CHECK (shipping_cost >= 0),
    CONSTRAINT listings_return_period_valid CHECK (return_period >= 0 AND return_period <= 365)
);

-- Listings table indexes
CREATE INDEX idx_listings_account_id ON listings(account_id);
CREATE INDEX idx_listings_ebay_item_id ON listings(ebay_item_id);
CREATE INDEX idx_listings_title ON listings(title);
CREATE INDEX idx_listings_category_name ON listings(category_name);
CREATE INDEX idx_listings_listing_format ON listings(listing_format);
CREATE INDEX idx_listings_listing_status ON listings(listing_status);
CREATE INDEX idx_listings_start_date ON listings(start_date);
CREATE INDEX idx_listings_end_date ON listings(end_date);
CREATE INDEX idx_listings_current_price ON listings(current_price);
CREATE INDEX idx_listings_view_count ON listings(view_count);
CREATE INDEX idx_listings_import_batch ON listings(import_batch_id);
CREATE INDEX idx_listings_created_at ON listings(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_listings_account_status ON listings(account_id, listing_status);
CREATE INDEX idx_listings_account_date ON listings(account_id, start_date);

-- Update trigger for listings
CREATE TRIGGER listings_updated_at BEFORE UPDATE ON listings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. Customers Table (Customer Management)
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- eBay Customer Information
    ebay_username VARCHAR(100) NOT NULL,
    ebay_user_id VARCHAR(50), -- eBay internal user ID
    
    -- Contact Information
    email VARCHAR(100),
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    
    -- Customer Segmentation
    customer_segment VARCHAR(20) DEFAULT 'NEW' CHECK (
        customer_segment IN ('NEW', 'REGULAR', 'VIP')
    ),
    
    -- Purchase Statistics
    total_orders INTEGER DEFAULT 0,
    total_spent DECIMAL(10, 2) DEFAULT 0,
    average_order_value DECIMAL(10, 2) DEFAULT 0,
    
    -- Customer Behavior
    first_order_date TIMESTAMPTZ,
    last_order_date TIMESTAMPTZ,
    days_since_last_order INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN last_order_date IS NULL THEN NULL
            ELSE EXTRACT(DAY FROM CURRENT_TIMESTAMP - last_order_date)
        END
    ) STORED,
    
    -- Communication Preferences
    communication_preference VARCHAR(20) DEFAULT 'email' CHECK (
        communication_preference IN ('email', 'ebay_messages', 'both', 'none')
    ),
    
    -- Customer Status
    status VARCHAR(20) DEFAULT 'active' CHECK (
        status IN ('active', 'inactive', 'blocked')
    ),
    
    is_repeat_customer BOOLEAN GENERATED ALWAYS AS (total_orders > 1) STORED,
    
    -- Additional Information
    notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT customers_ebay_username_length CHECK (length(ebay_username) >= 1),
    CONSTRAINT customers_account_username_unique UNIQUE (account_id, ebay_username),
    CONSTRAINT customers_email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT customers_total_orders_non_negative CHECK (total_orders >= 0),
    CONSTRAINT customers_total_spent_non_negative CHECK (total_spent >= 0)
);

-- Customers table indexes
CREATE INDEX idx_customers_account_id ON customers(account_id);
CREATE INDEX idx_customers_ebay_username ON customers(ebay_username);
CREATE INDEX idx_customers_customer_segment ON customers(customer_segment);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_total_orders ON customers(total_orders);
CREATE INDEX idx_customers_total_spent ON customers(total_spent);
CREATE INDEX idx_customers_last_order_date ON customers(last_order_date);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Update trigger for customers
CREATE TRIGGER customers_updated_at BEFORE UPDATE ON customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 9. Messages Table (Communication Management)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Customer Association (optional)
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    
    -- Message Information
    message_type VARCHAR(20) DEFAULT 'email' CHECK (
        message_type IN ('email', 'ebay_message', 'support_ticket')
    ),
    
    -- Message Details
    subject VARCHAR(200),
    content TEXT NOT NULL,
    direction VARCHAR(10) DEFAULT 'inbound' CHECK (direction IN ('inbound', 'outbound')),
    
    -- Message Status
    status VARCHAR(20) DEFAULT 'unread' CHECK (
        status IN ('unread', 'read', 'replied', 'archived')
    ),
    
    -- Thread Information
    thread_id UUID DEFAULT uuid_generate_v4(),
    parent_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Import Information
    external_id VARCHAR(100), -- Original message ID from source
    import_batch_id UUID,
    import_filename VARCHAR(255),
    
    -- Audit Fields
    received_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT messages_content_length CHECK (length(content) >= 1),
    CONSTRAINT messages_subject_length CHECK (subject IS NULL OR length(subject) >= 1)
);

-- Messages table indexes
CREATE INDEX idx_messages_account_id ON messages(account_id);
CREATE INDEX idx_messages_customer_id ON messages(customer_id);
CREATE INDEX idx_messages_message_type ON messages(message_type);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_direction ON messages(direction);
CREATE INDEX idx_messages_thread_id ON messages(thread_id);
CREATE INDEX idx_messages_parent_message_id ON messages(parent_message_id);
CREATE INDEX idx_messages_received_at ON messages(received_at);
CREATE INDEX idx_messages_import_batch ON messages(import_batch_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_messages_account_status ON messages(account_id, status);
CREATE INDEX idx_messages_customer_status ON messages(customer_id, status) WHERE customer_id IS NOT NULL;

-- Update trigger for messages
CREATE TRIGGER messages_updated_at BEFORE UPDATE ON messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 10. Templates Table (Response Templates)
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Template Information
    name VARCHAR(100) NOT NULL,
    subject VARCHAR(200),
    content TEXT NOT NULL,
    
    -- Template Configuration
    template_type VARCHAR(20) DEFAULT 'email' CHECK (
        template_type IN ('email', 'ebay_message', 'auto_response')
    ),
    
    category VARCHAR(50), -- 'order_inquiry', 'shipping_update', etc.
    
    -- Usage Statistics
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMPTZ,
    
    -- Template Status
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    
    -- Variables & Personalization
    variables JSONB, -- Available variables for template
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT templates_name_length CHECK (length(name) >= 3),
    CONSTRAINT templates_content_length CHECK (length(content) >= 10),
    CONSTRAINT templates_account_name_unique UNIQUE (account_id, name)
);

-- Templates table indexes
CREATE INDEX idx_templates_account_id ON templates(account_id);
CREATE INDEX idx_templates_name ON templates(name);
CREATE INDEX idx_templates_template_type ON templates(template_type);
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_is_active ON templates(is_active);
CREATE INDEX idx_templates_is_default ON templates(is_default);
CREATE INDEX idx_templates_usage_count ON templates(usage_count);
CREATE INDEX idx_templates_created_at ON templates(created_at);

-- Update trigger for templates
CREATE TRIGGER templates_updated_at BEFORE UPDATE ON templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 11. Uploads Table (File Upload Management)
CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- File Information
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    mime_type VARCHAR(100),
    
    -- Processing Information
    status VARCHAR(20) DEFAULT 'uploaded' CHECK (
        status IN ('uploaded', 'processing', 'completed', 'failed')
    ),
    
    -- Processing Results
    rows_total INTEGER,
    rows_processed INTEGER DEFAULT 0,
    rows_success INTEGER DEFAULT 0,
    rows_failed INTEGER DEFAULT 0,
    error_summary TEXT,
    
    -- Import Batch Information
    batch_id UUID DEFAULT uuid_generate_v4(),
    import_type VARCHAR(50), -- 'orders', 'listings', 'products', etc.
    
    -- Processing Times
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_duration_ms INTEGER,
    
    -- Audit Fields
    uploaded_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT uploads_filename_length CHECK (length(filename) >= 1),
    CONSTRAINT uploads_file_size_positive CHECK (file_size > 0),
    CONSTRAINT uploads_rows_non_negative CHECK (
        rows_total IS NULL OR rows_total >= 0
    ),
    CONSTRAINT uploads_processing_consistent CHECK (
        rows_processed <= COALESCE(rows_total, rows_processed)
    )
);

-- Uploads table indexes
CREATE INDEX idx_uploads_account_id ON uploads(account_id);
CREATE INDEX idx_uploads_status ON uploads(status);
CREATE INDEX idx_uploads_batch_id ON uploads(batch_id);
CREATE INDEX idx_uploads_import_type ON uploads(import_type);
CREATE INDEX idx_uploads_uploaded_at ON uploads(uploaded_at);
CREATE INDEX idx_uploads_created_at ON uploads(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_uploads_account_status ON uploads(account_id, status);
CREATE INDEX idx_uploads_account_type ON uploads(account_id, import_type);

-- Update trigger for uploads
CREATE TRIGGER uploads_updated_at BEFORE UPDATE ON uploads 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 12. Settings Table (Account Settings)
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Setting Information
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (
        setting_type IN ('string', 'number', 'boolean', 'json')
    ),
    
    -- Setting Metadata
    description TEXT,
    is_system BOOLEAN DEFAULT false,
    is_encrypted BOOLEAN DEFAULT false,
    
    -- Validation
    allowed_values TEXT, -- JSON array of allowed values
    default_value TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT settings_key_length CHECK (length(setting_key) >= 1),
    CONSTRAINT settings_account_key_unique UNIQUE (account_id, setting_key)
);

-- Settings table indexes
CREATE INDEX idx_settings_account_id ON settings(account_id);
CREATE INDEX idx_settings_setting_key ON settings(setting_key);
CREATE INDEX idx_settings_setting_type ON settings(setting_type);
CREATE INDEX idx_settings_is_system ON settings(is_system);
CREATE INDEX idx_settings_created_at ON settings(created_at);

-- Update trigger for settings
CREATE TRIGGER settings_updated_at BEFORE UPDATE ON settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================
-- VIEWS FOR COMMON QUERIES
-- ================================================

-- View for account summary
CREATE VIEW account_summary AS
SELECT 
    a.id,
    a.ebay_account_name,
    a.status,
    a.user_id,
    u.username,
    COUNT(DISTINCT o.id) as total_orders,
    COUNT(DISTINCT l.id) as total_listings,
    COUNT(DISTINCT p.id) as total_products,
    COUNT(DISTINCT c.id) as total_customers,
    COALESCE(SUM(o.total_amount), 0) as total_revenue,
    a.last_sync,
    a.created_at
FROM accounts a
LEFT JOIN users u ON a.user_id = u.id
LEFT JOIN orders o ON a.id = o.account_id
LEFT JOIN listings l ON a.id = l.account_id
LEFT JOIN products p ON a.id = p.account_id
LEFT JOIN customers c ON a.id = c.account_id
GROUP BY a.id, u.username;

-- View for order summary
CREATE VIEW order_summary AS
SELECT 
    o.id,
    o.account_id,
    a.ebay_account_name,
    o.ebay_order_id,
    o.buyer_username,
    o.total_amount,
    o.order_status,
    o.order_date,
    o.tracking_number,
    COUNT(oi.id) as item_count,
    SUM(oi.profit_amount) as total_profit
FROM orders o
LEFT JOIN accounts a ON o.account_id = a.id
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, a.ebay_account_name;

-- View for product inventory summary
CREATE VIEW product_inventory AS
SELECT 
    p.id,
    p.account_id,
    a.ebay_account_name,
    p.sku,
    p.name,
    p.available_quantity,
    p.reorder_point,
    CASE 
        WHEN p.available_quantity <= p.reorder_point THEN true
        ELSE false
    END as needs_reorder,
    p.cost_price,
    p.ebay_price,
    (p.ebay_price - p.cost_price) as profit_per_unit,
    p.status
FROM products p
LEFT JOIN accounts a ON p.account_id = a.id;

-- ================================================
-- INITIAL DATA
-- ================================================

-- Create default admin user (password: 'admin123' - change in production!)
INSERT INTO users (username, email, password_hash, role, first_name, last_name) 
VALUES (
    'admin', 
    'admin@ebaymanager.local', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3hp0NDvF/i', -- 'admin123'
    'admin',
    'System',
    'Administrator'
);

-- Health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status text, timestamp timestamptz, table_count integer) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        'healthy'::text, 
        now(),
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public')::integer;
END;
$$ LANGUAGE plpgsql;

-- Log successful schema creation
DO $$
BEGIN
    RAISE NOTICE 'eBay Manager Database Schema created successfully';
    RAISE NOTICE 'Tables created: %, Views: %, Functions: %', 
        (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
        (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public'),
        (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public');
    RAISE NOTICE 'SOLID/YAGNI principles enforced throughout schema design';
    RAISE NOTICE 'Database ready for 30-account eBay management system';
END $$;