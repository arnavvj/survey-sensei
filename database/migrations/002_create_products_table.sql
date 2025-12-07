-- Migration: Create PRODUCTS table
-- Stores product/item information from Amazon (via RapidAPI)
-- Schema aligned with RapidAPI "Real-Time Amazon Data" API response

CREATE TABLE IF NOT EXISTS products (
    -- Primary Key: ASIN (Amazon Standard Identification Number)
    item_id VARCHAR(20) PRIMARY KEY, -- 10-character ASIN from Amazon (e.g., 'B09YW8BZDP')

    -- Product Details (from RapidAPI product-details endpoint)
    product_url TEXT NOT NULL, -- Direct Amazon product page URL
    title TEXT NOT NULL, -- Product title/name
    brand VARCHAR(255), -- Manufacturer/brand name
    description TEXT, -- Product description
    photos JSONB, -- Array of product image URLs (from product_photos field)
    price DECIMAL(12, 2), -- Current product price
    star_rating DECIMAL(3, 2), -- Average star rating (e.g., 4.7)
    num_ratings INTEGER DEFAULT 0, -- Total number of ratings/reviews

    -- Vector embeddings for semantic search
    embeddings vector(1536), -- OpenAI ada-002 dimension for product similarity

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_price CHECK (price >= 0),
    CONSTRAINT check_star_rating CHECK (star_rating >= 0 AND star_rating <= 5),
    CONSTRAINT check_num_ratings CHECK (num_ratings >= 0)
);

-- Indexes for products
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_products_star_rating ON products(star_rating);
CREATE INDEX IF NOT EXISTS idx_products_embeddings ON products USING ivfflat(embeddings vector_cosine_ops) WITH (lists = 100);

-- Comments
COMMENT ON TABLE products IS 'Amazon product catalog fetched via RapidAPI Real-Time Amazon Data API';
COMMENT ON COLUMN products.item_id IS 'ASIN - Amazon Standard Identification Number (10 alphanumeric characters)';
COMMENT ON COLUMN products.product_url IS 'Direct link to Amazon product page (from product_url field)';
COMMENT ON COLUMN products.title IS 'Product title/name (from product_title field)';
COMMENT ON COLUMN products.brand IS 'Manufacturer/brand name (from brand field)';
COMMENT ON COLUMN products.description IS 'Product description (from product_description field)';
COMMENT ON COLUMN products.photos IS 'Array of image URLs (from product_photos field)';
COMMENT ON COLUMN products.price IS 'Current product price in USD (from product_price field)';
COMMENT ON COLUMN products.star_rating IS 'Average star rating 1-5 (from product_star_rating field)';
COMMENT ON COLUMN products.num_ratings IS 'Total number of ratings/reviews (from product_num_ratings field)';
COMMENT ON COLUMN products.embeddings IS 'Vector embeddings for semantic product similarity search';
