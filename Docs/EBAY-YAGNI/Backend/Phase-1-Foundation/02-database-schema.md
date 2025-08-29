# Database Schema Design - PostgreSQL with SOLID Principles

## Overview
Complete PostgreSQL database schema for eBay Management System following SOLID/YAGNI principles. Optimized for 30-account scale with clean relationships and essential data structures only.

## SOLID Principles Applied
- **Single Responsibility**: Each table has one clear business purpose
- **Open/Closed**: Schema allows extension without modifying existing structures
- **Liskov Substitution**: Consistent data types and constraints across similar tables
- **Interface Segregation**: Clean foreign key relationships, no unnecessary dependencies
- **Dependency Inversion**: Business logic depends on stable data abstractions

## YAGNI Compliance  
✅ **Essential Tables Only**: Core business entities for 30-account eBay management  
✅ **Simple Relationships**: Direct foreign keys, no complex many-to-many mappings  
✅ **Appropriate Indexing**: Performance indexes only where proven beneficial  
✅ **Standard Data Types**: PostgreSQL native types, no custom complex types  
❌ **Eliminated**: Audit trails, soft deletes, complex permissions, multi-tenancy

---

## Database Architecture Overview

### Entity Relationship Diagram
```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          EBAY MANAGER DATABASE SCHEMA                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │    Users    │    │  Accounts   │    │   Orders    │    │  Listings   │     │
│  │             │    │             │    │             │    │             │     │
│  │ • id (PK)   │───▶│ • id (PK)   │───▶│ • id (PK)   │    │ • id (PK)   │     │
│  │ • username  │    │ • user_id   │    │ • account_id│    │ • account_id│     │
│  │ • email     │    │ • ebay_name │    │ • ebay_order│    │ • ebay_id   │     │
│  │ • role      │    │ • status    │    │ • status    │    │ • status    │     │
│  └─────────────┘    │ • created_at│    │ • total     │    │ • title     │     │
│                     └─────────────┘    │ • created_at│    │ • price     │     │
│                                        └─────────────┘    │ • created_at│     │
│                                                           └─────────────┘     │
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Products   │    │  Suppliers  │    │  Customers  │    │  Messages   │     │
│  │             │    │             │    │             │    │             │     │
│  │ • id (PK)   │───▶│ • id (PK)   │    │ • id (PK)   │───▶│ • id (PK)   │     │
│  │ • account_id│    │ • account_id│    │ • account_id│    │ • account_id│     │
│  │ • supplier_id│   │ • name      │    │ • ebay_id   │    │ • customer_id│    │
│  │ • sku       │    │ • contact   │    │ • username  │    │ • subject   │     │
│  │ • name      │    │ • status    │    │ • email     │    │ • content   │     │
│  │ • cost_price│    │ • created_at│    │ • segment   │    │ • type      │     │
│  │ • sell_price│    └─────────────┘    │ • created_at│    │ • created_at│     │
│  │ • stock_qty │                       └─────────────┘    └─────────────┘     │
│  │ • created_at│                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Order Items │    │   Uploads   │    │  Templates  │    │  Settings   │     │
│  │             │    │             │    │             │    │             │     │
│  │ • id (PK)   │    │ • id (PK)   │    │ • id (PK)   │    │ • id (PK)   │     │
│  │ • order_id  │    │ • account_id│    │ • account_id│    │ • account_id│     │
│  │ • product_id│    │ • filename  │    │ • name      │    │ • key       │     │
│  │ • quantity  │    │ • file_type │    │ • subject   │    │ • value     │     │
│  │ • unit_price│    │ • status    │    │ • content   │    │ • type      │     │
│  │ • created_at│    │ • created_at│    │ • variables │    │ • created_at│     │
│  └─────────────┘    └─────────────┘    │ • created_at│    └─────────────┘     │
│                                        └─────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Core Relationships
```
Users (1) ──→ (N) Accounts ──→ (N) Orders
                      │           └─→ (N) OrderItems ──→ (1) Products
                      ├──→ (N) Listings  
                      ├──→ (N) Products ──→ (1) Suppliers
                      ├──→ (N) Customers ──→ (N) Messages
                      ├──→ (N) Templates
                      ├──→ (N) Uploads
                      └──→ (N) Settings
```

---

## Complete Table Schemas

### 1. Users Table (Authentication & User Management)
```sql
-- Users table: System users with role-based access
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

-- Users table indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email); 
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

-- Update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 2. Accounts Table (eBay Account Management)
```sql  
-- Accounts table: eBay accounts managed by users
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
```

### 3. Orders Table (eBay Order Management)
```sql
-- Orders table: eBay orders from CSV imports
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

-- Orders table indexes for performance
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
```

### 4. Suppliers Table (Supplier Management)
```sql
-- Suppliers table: Product suppliers and vendors
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
```

### 5. Products Table (Product Catalog)
```sql
-- Products table: Product catalog with supplier relationships
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
```

### 6. Listings Table (eBay Listing Management)
```sql
-- Listings table: eBay listings from CSV imports
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
```

### 7. Order Items Table (Order Line Items)
```sql
-- Order items table: Individual items within orders (many-to-many resolution)
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
```

### 8. Customers Table (Customer Management)
```sql
-- Customers table: eBay customer information and segmentation
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
    CONSTRAINT customers_ebay_username_length CHECK (length(ebay_username) >= 3),
    CONSTRAINT customers_account_username_unique UNIQUE (account_id, ebay_username),
    CONSTRAINT customers_total_orders_non_negative CHECK (total_orders >= 0),
    CONSTRAINT customers_total_spent_non_negative CHECK (total_spent >= 0),
    CONSTRAINT customers_email_format CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Customers table indexes
CREATE INDEX idx_customers_account_id ON customers(account_id);
CREATE INDEX idx_customers_ebay_username ON customers(ebay_username);
CREATE INDEX idx_customers_customer_segment ON customers(customer_segment);
CREATE INDEX idx_customers_total_orders ON customers(total_orders);
CREATE INDEX idx_customers_total_spent ON customers(total_spent);
CREATE INDEX idx_customers_last_order_date ON customers(last_order_date);
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_is_repeat ON customers(is_repeat_customer);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Composite indexes for customer analysis
CREATE INDEX idx_customers_account_segment ON customers(account_id, customer_segment);
CREATE INDEX idx_customers_account_repeat ON customers(account_id, is_repeat_customer);

-- Update trigger for customers
CREATE TRIGGER customers_updated_at BEFORE UPDATE ON customers 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 9. Messages Table (Customer Communication)
```sql
-- Messages table: Customer communication history
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    
    -- Account & Customer Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    customer_id INTEGER REFERENCES customers(id) ON DELETE SET NULL,
    
    -- Message Information
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    
    -- Message Type & Direction
    message_type VARCHAR(20) DEFAULT 'customer_service' CHECK (
        message_type IN ('customer_service', 'order_inquiry', 'shipping_update', 'return_request', 'general')
    ),
    
    direction VARCHAR(10) DEFAULT 'inbound' CHECK (
        direction IN ('inbound', 'outbound')
    ),
    
    -- eBay Message Information
    ebay_message_id VARCHAR(50),
    ebay_thread_id VARCHAR(50),
    
    -- Message Status
    status VARCHAR(20) DEFAULT 'unread' CHECK (
        status IN ('unread', 'read', 'replied', 'resolved', 'archived')
    ),
    
    priority VARCHAR(10) DEFAULT 'normal' CHECK (
        priority IN ('low', 'normal', 'high', 'urgent')
    ),
    
    -- Response Information
    requires_response BOOLEAN DEFAULT true,
    response_due_date TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    
    -- Associated Data
    order_reference VARCHAR(50), -- Related order if applicable
    item_reference VARCHAR(50), -- Related item if applicable
    
    -- CSV Import Metadata
    import_batch_id UUID,
    import_filename VARCHAR(255),
    
    -- Additional Information
    tags VARCHAR(500), -- Comma-separated tags
    notes TEXT, -- Internal notes
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT messages_subject_length CHECK (length(subject) >= 5),
    CONSTRAINT messages_content_length CHECK (length(content) >= 10),
    CONSTRAINT messages_response_logic CHECK (
        (requires_response = false) OR 
        (requires_response = true AND response_due_date IS NOT NULL)
    )
);

-- Messages table indexes
CREATE INDEX idx_messages_account_id ON messages(account_id);
CREATE INDEX idx_messages_customer_id ON messages(customer_id);
CREATE INDEX idx_messages_message_type ON messages(message_type);
CREATE INDEX idx_messages_direction ON messages(direction);
CREATE INDEX idx_messages_status ON messages(status);
CREATE INDEX idx_messages_priority ON messages(priority);
CREATE INDEX idx_messages_requires_response ON messages(requires_response);
CREATE INDEX idx_messages_response_due_date ON messages(response_due_date);
CREATE INDEX idx_messages_ebay_message_id ON messages(ebay_message_id);
CREATE INDEX idx_messages_order_reference ON messages(order_reference);
CREATE INDEX idx_messages_import_batch ON messages(import_batch_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Composite indexes for common queries
CREATE INDEX idx_messages_account_status ON messages(account_id, status);
CREATE INDEX idx_messages_account_priority ON messages(account_id, priority);
CREATE INDEX idx_messages_unread_urgent ON messages(status, priority) WHERE status = 'unread' AND priority IN ('high', 'urgent');

-- Update trigger for messages
CREATE TRIGGER messages_updated_at BEFORE UPDATE ON messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 10. Templates Table (Message Templates)
```sql
-- Templates table: Message templates for customer communication
CREATE TABLE templates (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Template Information
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'general',
    
    -- Template Content
    subject VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    
    -- Template Variables (JSON format for substitution)
    variables JSONB DEFAULT '[]',
    
    -- Template Configuration
    is_active BOOLEAN DEFAULT true,
    is_default BOOLEAN DEFAULT false,
    
    -- Usage Statistics
    usage_count INTEGER DEFAULT 0,
    last_used TIMESTAMPTZ,
    
    -- Template Type
    template_type VARCHAR(20) DEFAULT 'email' CHECK (
        template_type IN ('email', 'ebay_message', 'both')
    ),
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT templates_name_length CHECK (length(name) >= 3),
    CONSTRAINT templates_account_name_unique UNIQUE (account_id, name),
    CONSTRAINT templates_subject_length CHECK (length(subject) >= 5),
    CONSTRAINT templates_content_length CHECK (length(content) >= 10),
    CONSTRAINT templates_usage_non_negative CHECK (usage_count >= 0)
);

-- Templates table indexes
CREATE INDEX idx_templates_account_id ON templates(account_id);
CREATE INDEX idx_templates_name ON templates(name);
CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_is_active ON templates(is_active);
CREATE INDEX idx_templates_is_default ON templates(is_default);
CREATE INDEX idx_templates_template_type ON templates(template_type);
CREATE INDEX idx_templates_usage_count ON templates(usage_count);
CREATE INDEX idx_templates_created_at ON templates(created_at);

-- Update trigger for templates
CREATE TRIGGER templates_updated_at BEFORE UPDATE ON templates 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 11. Uploads Table (File Upload Management)
```sql
-- Uploads table: CSV file uploads and processing status
CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    
    -- Account Association
    account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- File Information
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_type VARCHAR(10) NOT NULL CHECK (file_type IN ('csv', 'xlsx', 'xls')),
    mime_type VARCHAR(100),
    
    -- Upload Metadata
    upload_type VARCHAR(20) NOT NULL CHECK (
        upload_type IN ('orders', 'listings', 'products', 'messages', 'customers')
    ),
    
    -- Processing Status
    processing_status VARCHAR(20) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'processing', 'completed', 'failed', 'cancelled')
    ),
    
    -- Processing Results
    total_rows INTEGER,
    processed_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    warning_rows INTEGER DEFAULT 0,
    
    -- Error Information
    error_message TEXT,
    error_details JSONB,
    validation_errors JSONB,
    
    -- Processing Timing
    processing_started_at TIMESTAMPTZ,
    processing_completed_at TIMESTAMPTZ,
    processing_duration_seconds INTEGER GENERATED ALWAYS AS (
        CASE 
            WHEN processing_started_at IS NOT NULL AND processing_completed_at IS NOT NULL 
            THEN EXTRACT(EPOCH FROM processing_completed_at - processing_started_at)
            ELSE NULL
        END
    ) STORED,
    
    -- Batch Information
    batch_id UUID DEFAULT gen_random_uuid(),
    
    -- Additional Information
    notes TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT uploads_file_size_positive CHECK (file_size > 0),
    CONSTRAINT uploads_original_filename_length CHECK (length(original_filename) >= 5),
    CONSTRAINT uploads_rows_non_negative CHECK (
        total_rows IS NULL OR (
            total_rows >= 0 AND 
            processed_rows >= 0 AND 
            success_rows >= 0 AND 
            error_rows >= 0 AND 
            warning_rows >= 0
        )
    ),
    CONSTRAINT uploads_processing_logic CHECK (
        (processing_status = 'pending' AND processing_started_at IS NULL) OR
        (processing_status IN ('processing', 'completed', 'failed') AND processing_started_at IS NOT NULL)
    )
);

-- Uploads table indexes
CREATE INDEX idx_uploads_account_id ON uploads(account_id);
CREATE INDEX idx_uploads_upload_type ON uploads(upload_type);
CREATE INDEX idx_uploads_processing_status ON uploads(processing_status);
CREATE INDEX idx_uploads_batch_id ON uploads(batch_id);
CREATE INDEX idx_uploads_processing_started_at ON uploads(processing_started_at);
CREATE INDEX idx_uploads_created_at ON uploads(created_at);

-- Update trigger for uploads
CREATE TRIGGER uploads_updated_at BEFORE UPDATE ON uploads 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### 12. Settings Table (System Configuration)
```sql
-- Settings table: System and account-level configuration
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    
    -- Account Association (NULL for global settings)
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Setting Information
    setting_key VARCHAR(100) NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(20) DEFAULT 'string' CHECK (
        setting_type IN ('string', 'integer', 'decimal', 'boolean', 'json', 'date')
    ),
    
    -- Setting Metadata
    category VARCHAR(50) DEFAULT 'general',
    description TEXT,
    is_public BOOLEAN DEFAULT false,
    is_required BOOLEAN DEFAULT false,
    
    -- Validation Rules
    validation_rules JSONB, -- JSON schema for value validation
    default_value TEXT,
    
    -- Audit Fields
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT settings_key_length CHECK (length(setting_key) >= 3),
    CONSTRAINT settings_scope_key_unique UNIQUE (COALESCE(account_id, 0), setting_key),
    CONSTRAINT settings_boolean_values CHECK (
        setting_type != 'boolean' OR setting_value IN ('true', 'false', '1', '0')
    )
);

-- Settings table indexes
CREATE INDEX idx_settings_account_id ON settings(account_id);
CREATE INDEX idx_settings_setting_key ON settings(setting_key);
CREATE INDEX idx_settings_category ON settings(category);
CREATE INDEX idx_settings_is_public ON settings(is_public);
CREATE INDEX idx_settings_created_at ON settings(created_at);

-- Update trigger for settings
CREATE TRIGGER settings_updated_at BEFORE UPDATE ON settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Database Views for Common Queries

### 1. Account Dashboard Metrics View
```sql
-- View: Account dashboard with key metrics
CREATE OR REPLACE VIEW account_dashboard_metrics AS
SELECT 
    a.id as account_id,
    a.ebay_account_name,
    
    -- Order Metrics
    COUNT(o.id) as total_orders,
    COUNT(CASE WHEN o.order_status = 'pending' THEN 1 END) as pending_orders,
    COUNT(CASE WHEN o.order_status = 'processing' THEN 1 END) as processing_orders,
    COUNT(CASE WHEN o.order_status = 'shipped' THEN 1 END) as shipped_orders,
    COUNT(CASE WHEN o.order_status = 'delivered' THEN 1 END) as delivered_orders,
    
    -- Financial Metrics
    COALESCE(SUM(o.total_amount), 0) as total_revenue,
    COALESCE(AVG(o.total_amount), 0) as average_order_value,
    COALESCE(SUM(CASE WHEN o.order_date >= CURRENT_DATE THEN o.total_amount END), 0) as revenue_today,
    COALESCE(SUM(CASE WHEN o.order_date >= CURRENT_DATE - INTERVAL '7 days' THEN o.total_amount END), 0) as revenue_week,
    COALESCE(SUM(CASE WHEN o.order_date >= CURRENT_DATE - INTERVAL '30 days' THEN o.total_amount END), 0) as revenue_month,
    
    -- Listing Metrics
    (SELECT COUNT(*) FROM listings l WHERE l.account_id = a.id AND l.listing_status = 'active') as active_listings,
    (SELECT COUNT(*) FROM listings l WHERE l.account_id = a.id AND l.listing_status = 'draft') as draft_listings,
    
    -- Customer Metrics
    (SELECT COUNT(*) FROM customers c WHERE c.account_id = a.id) as total_customers,
    (SELECT COUNT(*) FROM customers c WHERE c.account_id = a.id AND c.customer_segment = 'VIP') as vip_customers,
    
    -- Message Metrics
    (SELECT COUNT(*) FROM messages m WHERE m.account_id = a.id AND m.status = 'unread') as unread_messages,
    (SELECT COUNT(*) FROM messages m WHERE m.account_id = a.id AND m.requires_response = true) as pending_responses,
    
    -- Product Metrics
    (SELECT COUNT(*) FROM products p WHERE p.account_id = a.id AND p.available_quantity <= p.reorder_point) as low_stock_products
    
FROM accounts a
LEFT JOIN orders o ON a.id = o.account_id
WHERE a.status = 'active'
GROUP BY a.id, a.ebay_account_name;
```

### 2. Order Summary with Items View
```sql
-- View: Order summary with item details
CREATE OR REPLACE VIEW order_summary AS
SELECT 
    o.id as order_id,
    o.account_id,
    o.ebay_order_id,
    o.buyer_username,
    o.order_status,
    o.total_amount,
    o.order_date,
    
    -- Order Items Summary
    COUNT(oi.id) as item_count,
    SUM(oi.quantity) as total_quantity,
    SUM(oi.total_cost) as total_cost,
    SUM(oi.profit_amount) as total_profit,
    
    -- Profit Margin
    CASE 
        WHEN SUM(oi.total_price) > 0 
        THEN ROUND((SUM(oi.profit_amount) / SUM(oi.total_price)) * 100, 2)
        ELSE 0 
    END as profit_margin_percent,
    
    -- Shipping Information
    o.shipping_method,
    o.tracking_number,
    o.shipped_date,
    o.delivered_date
    
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id, o.account_id, o.ebay_order_id, o.buyer_username, o.order_status, 
         o.total_amount, o.order_date, o.shipping_method, o.tracking_number, 
         o.shipped_date, o.delivered_date;
```

### 3. Product Performance View
```sql
-- View: Product performance with sales data
CREATE OR REPLACE VIEW product_performance AS
SELECT 
    p.id as product_id,
    p.account_id,
    p.sku,
    p.name,
    p.category,
    p.cost_price,
    p.retail_price,
    p.stock_quantity,
    p.available_quantity,
    
    -- Sales Performance
    COUNT(oi.id) as total_sales,
    COALESCE(SUM(oi.quantity), 0) as units_sold,
    COALESCE(SUM(oi.total_price), 0) as revenue,
    COALESCE(SUM(oi.total_cost), 0) as cost_of_goods,
    COALESCE(SUM(oi.profit_amount), 0) as total_profit,
    
    -- Profit Calculations
    CASE 
        WHEN SUM(oi.total_price) > 0 
        THEN ROUND((SUM(oi.profit_amount) / SUM(oi.total_price)) * 100, 2)
        ELSE 0 
    END as profit_margin_percent,
    
    -- Recent Performance
    COUNT(CASE WHEN oi.created_at >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as sales_last_30_days,
    COALESCE(SUM(CASE WHEN oi.created_at >= CURRENT_DATE - INTERVAL '30 days' THEN oi.quantity END), 0) as units_sold_last_30_days,
    
    -- Inventory Status
    CASE 
        WHEN p.available_quantity <= 0 THEN 'Out of Stock'
        WHEN p.available_quantity <= p.reorder_point THEN 'Low Stock'
        ELSE 'In Stock'
    END as inventory_status
    
FROM products p
LEFT JOIN order_items oi ON p.id = oi.product_id
WHERE p.status = 'active'
GROUP BY p.id, p.account_id, p.sku, p.name, p.category, p.cost_price, 
         p.retail_price, p.stock_quantity, p.available_quantity, p.reorder_point;
```

---

## Database Initialization Script

### Complete Database Setup
```sql
-- Database initialization script
-- Execute in order for proper setup

-- 1. Create database and user (run as PostgreSQL superuser)
CREATE DATABASE ebay_manager 
    WITH ENCODING = 'UTF8'
         LC_COLLATE = 'en_US.UTF-8'  
         LC_CTYPE = 'en_US.UTF-8'
         TEMPLATE = template0;

CREATE USER ebay_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE ebay_manager TO ebay_user;

-- 2. Connect to ebay_manager database
\c ebay_manager

-- 3. Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- 4. Grant permissions to user
GRANT ALL ON SCHEMA public TO ebay_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ebay_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ebay_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ebay_user;

-- 5. Create all tables in order (execute table creation scripts above)
-- Tables must be created in dependency order:
-- users -> accounts -> suppliers -> products -> orders -> order_items 
--       -> customers -> messages -> listings -> templates -> uploads -> settings

-- 6. Create views (execute view creation scripts above)

-- 7. Insert default data
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, email_verified) 
VALUES 
('admin', 'admin@ebaymanager.local', '$2b$12$encrypted_password_hash_here', 'System', 'Administrator', 'admin', true, true),
('demo_user', 'demo@ebaymanager.local', '$2b$12$encrypted_password_hash_here', 'Demo', 'User', 'user', true, true);

-- 8. Insert default settings (global settings)
INSERT INTO settings (setting_key, setting_value, setting_type, category, description, is_public, is_required, default_value) 
VALUES 
('system_name', 'eBay Manager Pro', 'string', 'system', 'System display name', true, true, 'eBay Manager Pro'),
('default_currency', 'USD', 'string', 'system', 'Default system currency', true, true, 'USD'),
('max_upload_size_mb', '100', 'integer', 'files', 'Maximum file upload size in MB', true, true, '100'),
('session_timeout_minutes', '30', 'integer', 'auth', 'Session timeout in minutes', false, true, '30'),
('auto_sync_interval_minutes', '30', 'integer', 'sync', 'Automatic sync interval in minutes', false, true, '30'),
('backup_retention_days', '30', 'integer', 'backup', 'Backup file retention in days', false, true, '30'),
('log_level', 'INFO', 'string', 'logging', 'System log level', false, true, 'INFO'),
('enable_email_notifications', 'true', 'boolean', 'notifications', 'Enable email notifications', false, true, 'true'),
('default_timezone', 'UTC', 'string', 'system', 'Default system timezone', true, true, 'UTC'),
('maintenance_mode', 'false', 'boolean', 'system', 'System maintenance mode', false, false, 'false');

-- 9. Verify installation
SELECT 'Database setup complete. Tables created: ' || count(*) as status 
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

SELECT 'Views created: ' || count(*) as status
FROM information_schema.views 
WHERE table_schema = 'public';

-- 10. Display table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Success Criteria & Validation

### Database Requirements ✅
- [ ] All 12 tables created successfully with proper constraints
- [ ] Foreign key relationships established correctly
- [ ] Indexes created for performance optimization  
- [ ] Update triggers working for all tables with updated_at columns
- [ ] Views created and returning expected data
- [ ] Database extensions installed and functioning
- [ ] Default data inserted successfully
- [ ] User permissions configured correctly

### Data Integrity ✅
- [ ] All CHECK constraints enforced properly
- [ ] UNIQUE constraints preventing duplicate data
- [ ] Foreign key constraints maintaining referential integrity
- [ ] Generated columns calculating correctly (profit_amount, available_quantity, etc.)
- [ ] Email format validation working
- [ ] Positive numeric constraints enforced
- [ ] Date range constraints working properly

### SOLID/YAGNI Compliance ✅  
- [ ] **Single Responsibility**: Each table serves one clear business purpose
- [ ] **Open/Closed**: Schema extensible without modifying existing structures
- [ ] **Liskov Substitution**: Consistent data types and patterns across similar tables
- [ ] **Interface Segregation**: Clean foreign key relationships, no circular dependencies
- [ ] **Dependency Inversion**: Business logic layer will depend on these stable data contracts
- [ ] **YAGNI Applied**: Only essential tables and columns, no speculative features
- [ ] No over-normalization or under-normalization - appropriate for 30-account scale

### Performance Requirements ✅
- [ ] Query performance < 100ms for dashboard views
- [ ] Index usage verified for common queries
- [ ] Connection pooling configured appropriately
- [ ] Database size projections reasonable for 30-account scale
- [ ] Backup and recovery procedures tested

**Next Step**: Proceed to [03-authentication-system.md](./03-authentication-system.md) for JWT authentication implementation.