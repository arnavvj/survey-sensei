-- Migration: Create PRODUCTS table
-- Stores product/item information from various platforms

CREATE TABLE IF NOT EXISTS products (
    item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_platform VARCHAR(50) NOT NULL, -- amazon, shopify, walmart, etc.
    product_url TEXT,
    version_number INTEGER DEFAULT 1,
    title TEXT NOT NULL,
    brand VARCHAR(255),
    description TEXT,
    pictures JSONB, -- Array of image URLs stored as JSON
    review_count INTEGER DEFAULT 0,
    returns_count INTEGER DEFAULT 0,
    tags TEXT[], -- PostgreSQL array for better querying
    embeddings vector(1536), -- OpenAI ada-002 dimension

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_review_count CHECK (review_count >= 0),
    CONSTRAINT check_returns_count CHECK (returns_count >= 0)
);

-- Indexes for products
CREATE INDEX IF NOT EXISTS idx_products_source_platform ON products(source_platform);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_tags ON products USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_products_embeddings ON products USING ivfflat(embeddings vector_cosine_ops) WITH (lists = 100);

-- Comments
COMMENT ON TABLE products IS 'Stores product information from various e-commerce platforms';
COMMENT ON COLUMN products.embeddings IS 'Vector embeddings for semantic product search';
