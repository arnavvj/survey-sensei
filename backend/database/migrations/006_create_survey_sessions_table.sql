-- Migration: Create SURVEY_SESSIONS table
-- Tracks entire survey sessions with agent contexts and final results

DROP TABLE IF EXISTS survey_sessions CASCADE;

CREATE TABLE survey_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(20) NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,

    -- Agent outputs (JSONB)
    product_context JSONB,        -- ProductContext agent output
    customer_context JSONB,       -- CustomerContext agent output

    -- Survey state at completion/abortion (JSONB)
    session_context JSONB,        -- Complete survey agent state + review generation inputs - populated at end and when reviews generated

    -- Final results (JSONB)
    questions_and_answers JSONB,  -- Final Q&A pairs when completed
    review_options JSONB,         -- Generated review options (3 options with titles, text, stars, tone, highlights, sentiment_band)

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_survey_sessions_user_id ON survey_sessions(user_id);
CREATE INDEX idx_survey_sessions_item_id ON survey_sessions(item_id);
CREATE INDEX idx_survey_sessions_transaction_id ON survey_sessions(transaction_id);

-- Comments
COMMENT ON TABLE survey_sessions IS 'Tracks survey sessions with agent contexts and final results';
COMMENT ON COLUMN survey_sessions.product_context IS 'ProductContextAgent output (JSONB) - populated at session start';
COMMENT ON COLUMN survey_sessions.customer_context IS 'CustomerContextAgent output (JSONB) - populated at session start';
COMMENT ON COLUMN survey_sessions.session_context IS 'Complete survey agent state + review generation inputs (survey_responses, product_context, customer_context, user_reviews, timestamps)';
COMMENT ON COLUMN survey_sessions.questions_and_answers IS 'Final aggregated Q&A pairs (populated when survey is completed)';
COMMENT ON COLUMN survey_sessions.review_options IS 'Generated review options with sentiment_band (populated when reviews are generated)';
