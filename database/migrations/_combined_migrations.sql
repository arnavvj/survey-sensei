-- Migration: Enable PostgreSQL Extensions
-- Required extensions for Survey Sensei

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Vector embeddings (pgvector)
CREATE EXTENSION IF NOT EXISTS "vector";


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


-- Migration: Create USERS table
-- Stores user demographic and profile information

CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_name VARCHAR(255) NOT NULL,
    email_id VARCHAR(255) UNIQUE NOT NULL,
    age INTEGER,
    base_location VARCHAR(255),
    base_zip VARCHAR(20),
    gender VARCHAR(50),
    credit_score INTEGER,
    avg_monthly_expenses DECIMAL(12, 2),
    embeddings vector(1536), -- User profile embeddings for personalization

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_active TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT check_age CHECK (age > 0 AND age < 150),
    CONSTRAINT check_credit_score CHECK (credit_score >= 300 AND credit_score <= 850),
    CONSTRAINT check_avg_monthly_expenses CHECK (avg_monthly_expenses >= 0)
);

-- Indexes for users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email_id);
CREATE INDEX IF NOT EXISTS idx_users_base_zip ON users(base_zip);
CREATE INDEX IF NOT EXISTS idx_users_embeddings ON users USING ivfflat(embeddings vector_cosine_ops) WITH (lists = 100);

-- Comments
COMMENT ON TABLE users IS 'User profiles with demographics for personalized survey generation';
COMMENT ON COLUMN users.embeddings IS 'User profile embeddings for personalization';


-- Migration: Create TRANSACTIONS table
-- Stores purchase and delivery information

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Transaction details
    order_date TIMESTAMP WITH TIME ZONE NOT NULL,
    delivery_date TIMESTAMP WITH TIME ZONE,
    expected_delivery_date TIMESTAMP WITH TIME ZONE,
    return_date TIMESTAMP WITH TIME ZONE,

    -- Pricing
    original_price DECIMAL(12, 2) NOT NULL,
    retail_price DECIMAL(12, 2) NOT NULL,
    discount_percentage DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE
            WHEN original_price > 0 THEN ((original_price - retail_price) / original_price * 100)
            ELSE 0
        END
    ) STORED,

    -- Status tracking
    transaction_status VARCHAR(50) DEFAULT 'pending', -- pending, delivered, returned, cancelled

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_delivery_date CHECK (delivery_date IS NULL OR delivery_date >= order_date),
    CONSTRAINT check_return_date CHECK (return_date IS NULL OR return_date >= delivery_date),
    CONSTRAINT check_prices CHECK (original_price >= 0 AND retail_price >= 0)
);

-- Indexes for transactions
CREATE INDEX IF NOT EXISTS idx_transactions_item_id ON transactions(item_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_order_date ON transactions(order_date);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(transaction_status);

-- Comments
COMMENT ON TABLE transactions IS 'Purchase and delivery tracking';


-- Migration: Create REVIEWS table
-- Stores user reviews with embeddings for sentiment analysis

CREATE TABLE IF NOT EXISTS reviews (
    review_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,

    -- Review content
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    review_title VARCHAR(500),
    review_text TEXT NOT NULL,
    review_stars INTEGER NOT NULL,
    manual_or_agent_generated VARCHAR(20) NOT NULL DEFAULT 'manual', -- 'manual' or 'agent'

    -- GenAI features
    embeddings vector(1536), -- Review embeddings for semantic search

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_review_stars CHECK (review_stars >= 1 AND review_stars <= 5),
    CONSTRAINT check_manual_or_agent CHECK (manual_or_agent_generated IN ('manual', 'agent')),
    CONSTRAINT unique_review_per_transaction UNIQUE(transaction_id)
);

-- Indexes for reviews
CREATE INDEX IF NOT EXISTS idx_reviews_item_id ON reviews(item_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_transaction_id ON reviews(transaction_id);
CREATE INDEX IF NOT EXISTS idx_reviews_stars ON reviews(review_stars);
CREATE INDEX IF NOT EXISTS idx_reviews_embeddings ON reviews USING ivfflat(embeddings vector_cosine_ops) WITH (lists = 100);

-- Comments
COMMENT ON TABLE reviews IS 'User-generated reviews with AI-generated embeddings and sentiment';
COMMENT ON COLUMN reviews.embeddings IS 'Review text embeddings for sentiment analysis';
COMMENT ON COLUMN reviews.manual_or_agent_generated IS 'Indicates if review was written manually by user or generated by AI agent';


-- Migration: Create SURVEY table
-- Core table for the agentic GenAI survey system

CREATE TABLE IF NOT EXISTS survey (
    scenario_id UUID DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,
    survey_id UUID REFERENCES reviews(review_id) ON DELETE CASCADE,
    question_id UUID DEFAULT uuid_generate_v4(),

    -- Question details
    question_number INTEGER NOT NULL,
    question TEXT NOT NULL,
    options_object JSONB, -- Flexible JSON structure for different question types
    selected_option TEXT, -- User's selected answer/option

    -- GenAI validation
    correctly_anticipates_user_sentiment BOOLEAN,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Composite primary key
    PRIMARY KEY (scenario_id, question_id),

    -- Constraints
    CONSTRAINT check_question_number CHECK (question_number > 0)
);

-- Indexes for survey
CREATE INDEX IF NOT EXISTS idx_survey_item_id ON survey(item_id);
CREATE INDEX IF NOT EXISTS idx_survey_user_id ON survey(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_transaction_id ON survey(transaction_id);
CREATE INDEX IF NOT EXISTS idx_survey_survey_id ON survey(survey_id);
CREATE INDEX IF NOT EXISTS idx_survey_scenario_id ON survey(scenario_id);

-- Comments
COMMENT ON TABLE survey IS 'Core agentic survey system - dynamically generated questions';
COMMENT ON COLUMN survey.correctly_anticipates_user_sentiment IS 'Ground truth for training/fine-tuning the agent';


-- Migration: Create SURVEY_SESSIONS table
-- Tracks entire survey sessions for analytics and agent improvement

CREATE TABLE IF NOT EXISTS survey_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,

    -- Session metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,
    total_questions INTEGER DEFAULT 0,
    answered_questions INTEGER DEFAULT 0,

    -- Agent performance metrics
    average_confidence_score DECIMAL(3, 2),
    sentiment_prediction_accuracy DECIMAL(3, 2),

    -- Session context (for agent to maintain state)
    session_context JSONB, -- Stores conversation history, user preferences, etc.

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_survey_sessions_user_id ON survey_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_survey_sessions_transaction_id ON survey_sessions(transaction_id);
CREATE INDEX IF NOT EXISTS idx_survey_sessions_completed ON survey_sessions(is_completed);

-- Comments
COMMENT ON TABLE survey_sessions IS 'Tracks survey sessions for analytics and agent learning';


-- Migration: Create Triggers
-- Auto-update timestamps and derived fields

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_transactions_updated_at ON transactions;
CREATE TRIGGER update_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_reviews_updated_at ON reviews;
CREATE TRIGGER update_reviews_updated_at BEFORE UPDATE ON reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_survey_updated_at ON survey;
CREATE TRIGGER update_survey_updated_at BEFORE UPDATE ON survey
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_survey_sessions_updated_at ON survey_sessions;
CREATE TRIGGER update_survey_sessions_updated_at BEFORE UPDATE ON survey_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update review_count on products
CREATE OR REPLACE FUNCTION update_product_review_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE products
        SET review_count = review_count + 1
        WHERE item_id = NEW.item_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE products
        SET review_count = review_count - 1
        WHERE item_id = OLD.item_id;
    END IF
;
    RETURN NULL;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS trigger_update_review_count ON reviews;
CREATE TRIGGER trigger_update_review_count
AFTER INSERT OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION update_product_review_count();


-- Migration: Enable Row Level Security (RLS)
-- Basic policies - adjust based on your auth strategy

-- Enable RLS on all tables
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey ENABLE ROW LEVEL SECURITY;
ALTER TABLE survey_sessions ENABLE ROW LEVEL SECURITY;

-- Allow anonymous read access to products (public catalog)
DROP POLICY IF EXISTS "Allow public read access to products" ON products;
CREATE POLICY "Allow public read access to products"
ON products FOR SELECT
TO anon
USING (true);

-- Users can only view their own data
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
CREATE POLICY "Users can view their own profile"
ON users FOR SELECT
TO authenticated
USING (auth.uid()::uuid = user_id);

-- Users can only view their own transactions
DROP POLICY IF EXISTS "Users can view their own transactions" ON transactions;
CREATE POLICY "Users can view their own transactions"
ON transactions FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);

-- Users can view and create their own reviews
DROP POLICY IF EXISTS "Users can view their own reviews" ON reviews;
CREATE POLICY "Users can view their own reviews"
ON reviews FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);

DROP POLICY IF EXISTS "Users can create their own reviews" ON reviews;
CREATE POLICY "Users can create their own reviews"
ON reviews FOR INSERT
TO authenticated
WITH CHECK (user_id = auth.uid()::uuid);

-- Users can view their own survey questions
DROP POLICY IF EXISTS "Users can view their own survey questions" ON survey;
CREATE POLICY "Users can view their own survey questions"
ON survey FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);

-- Users can view their own survey sessions
DROP POLICY IF EXISTS "Users can view their own survey sessions" ON survey_sessions;
CREATE POLICY "Users can view their own survey sessions"
ON survey_sessions FOR SELECT
TO authenticated
USING (user_id = auth.uid()::uuid);


-- Migration: Add conversation_history column to existing survey_sessions table
-- This handles the case where the table exists but is missing this column

DO $$
BEGIN
    -- Check if conversation_history column exists
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'survey_sessions'
        AND column_name = 'conversation_history'
    ) THEN
        -- Add the column
        ALTER TABLE survey_sessions
        ADD COLUMN conversation_history JSONB DEFAULT '[]'::jsonb;

        RAISE NOTICE 'Added conversation_history column to survey_sessions table';
    ELSE
        RAISE NOTICE 'conversation_history column already exists in survey_sessions table';
    END IF;
END $$;

-- Add comment
COMMENT ON COLUMN survey_sessions.conversation_history IS 'Stores conversation messages between agent and user during survey';
