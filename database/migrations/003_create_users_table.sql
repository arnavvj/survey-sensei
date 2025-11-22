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
