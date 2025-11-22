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
