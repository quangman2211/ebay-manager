-- Initial Database Setup for eBay Manager
-- Following SOLID/YAGNI principles

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Create health check function
CREATE OR REPLACE FUNCTION health_check()
RETURNS TABLE(status text, timestamp timestamptz) AS $$
BEGIN
    RETURN QUERY SELECT 'healthy'::text, now();
END;
$$ LANGUAGE plpgsql;

-- Log initialization
INSERT INTO pg_stat_statements_reset() VALUES (DEFAULT) ON CONFLICT DO NOTHING;

-- Basic database info logging
DO $$
BEGIN
    RAISE NOTICE 'eBay Manager Database initialized successfully';
    RAISE NOTICE 'PostgreSQL version: %', version();
    RAISE NOTICE 'Extensions loaded: uuid-ossp, pg_trgm, btree_gin';
END $$;