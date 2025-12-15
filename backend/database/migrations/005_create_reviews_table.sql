-- Migration: Create REVIEWS table
-- Stores user reviews with embeddings for sentiment analysis

CREATE TABLE IF NOT EXISTS reviews (
    review_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id VARCHAR(20) NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,

    -- Review content
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    review_title VARCHAR(500),
    review_text TEXT NOT NULL,
    review_stars INTEGER NOT NULL, -- 1-5

    -- Source tracking
    source VARCHAR(20) NOT NULL DEFAULT 'agent_generated', -- 'rapidapi', 'agent_generated', 'user_survey'
    manual_or_agent_generated VARCHAR(20) NOT NULL DEFAULT 'agent', -- 'manual' (human-written), 'agent' (AI-generated)

    -- GenAI features
    embeddings vector(1536), -- Review embeddings for semantic analysis (reserved for future survey framework)

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT check_review_stars CHECK (review_stars >= 1 AND review_stars <= 5),
    CONSTRAINT check_source CHECK (source IN ('rapidapi', 'agent_generated', 'user_survey')),
    CONSTRAINT check_manual_or_agent CHECK (manual_or_agent_generated IN ('manual', 'agent')),
    CONSTRAINT unique_review_per_transaction UNIQUE(transaction_id)
);

-- Indexes for reviews
CREATE INDEX IF NOT EXISTS idx_reviews_item_id ON reviews(item_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_transaction_id ON reviews(transaction_id);
CREATE INDEX IF NOT EXISTS idx_reviews_stars ON reviews(review_stars);
CREATE INDEX IF NOT EXISTS idx_reviews_embeddings ON reviews USING ivfflat(embeddings vector_cosine_ops) WITH (lists = 100);
CREATE INDEX IF NOT EXISTS idx_reviews_source ON reviews(source);
CREATE INDEX IF NOT EXISTS idx_reviews_manual_or_agent ON reviews(manual_or_agent_generated);

-- Comments
COMMENT ON TABLE reviews IS 'User-generated reviews with AI-generated embeddings and sentiment';
COMMENT ON COLUMN reviews.embeddings IS 'Review text embeddings for semantic analysis (reserved for future survey framework enhancements)';
COMMENT ON COLUMN reviews.source IS 'Provenance: rapidapi (scraped from Amazon), agent_generated (by MOCK_RVW_MINI_AGENT), user_survey (submitted via survey flow)';
COMMENT ON COLUMN reviews.manual_or_agent_generated IS 'Content authorship: manual (human-written text), agent (AI-generated text)';
