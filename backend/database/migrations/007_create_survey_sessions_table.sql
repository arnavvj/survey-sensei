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
