-- Migration: Create SURVEY_SESSIONS table
-- Tracks entire survey sessions with agent contexts and final results

DROP TABLE IF EXISTS survey_sessions CASCADE;

CREATE TABLE survey_sessions (
    session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_id VARCHAR(20) NOT NULL REFERENCES products(item_id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(transaction_id) ON DELETE CASCADE,

    -- Session lifecycle
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN DEFAULT FALSE,

    -- Agent outputs (JSONB)
    product_context JSONB,        -- ProductContext agent output
    customer_context JSONB,       -- CustomerContext agent output
    questions_and_answers JSONB,  -- Final Q&A pairs when completed

    -- Temporary state storage (JSONB)
    session_context JSONB,        -- Temporary state during survey (current_state, form_data)

    -- Performance metrics
    average_confidence_score DECIMAL(3, 2),
    sentiment_prediction_accuracy DECIMAL(3, 2),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_survey_sessions_user_id ON survey_sessions(user_id);
CREATE INDEX idx_survey_sessions_item_id ON survey_sessions(item_id);
CREATE INDEX idx_survey_sessions_transaction_id ON survey_sessions(transaction_id);
CREATE INDEX idx_survey_sessions_completed ON survey_sessions(is_completed);

-- Comments
COMMENT ON TABLE survey_sessions IS 'Tracks survey sessions with agent contexts and final results';
COMMENT ON COLUMN survey_sessions.product_context IS 'ProductContextAgent output (JSONB)';
COMMENT ON COLUMN survey_sessions.customer_context IS 'CustomerContextAgent output (JSONB)';
COMMENT ON COLUMN survey_sessions.questions_and_answers IS 'Final aggregated Q&A pairs (populated when is_completed=TRUE)';
