-- Migration: Create SURVEY_DETAILS table
-- Event log for tracking all survey interactions and updates

DROP TABLE IF EXISTS survey_details CASCADE;

CREATE TABLE survey_details (
    session_id UUID NOT NULL REFERENCES survey_sessions(session_id) ON DELETE CASCADE,
    detail_id UUID DEFAULT uuid_generate_v4(),

    -- Event metadata
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'question_generated',
        'answer_submitted',
        'answer_updated',
        'answer_skipped',
        'question_updated',
        'survey_incomplete',
        'survey_aborted',
        'survey_completed'
    )),

    -- Flexible event data (JSONB)
    -- Can be empty/null for survey_incomplete and survey_aborted events
    event_detail JSONB,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Composite primary key
    PRIMARY KEY (session_id, detail_id)
);

-- Indexes
CREATE INDEX idx_survey_details_session_id ON survey_details(session_id);
CREATE INDEX idx_survey_details_event_type ON survey_details(event_type);
CREATE INDEX idx_survey_details_created_at ON survey_details(created_at);

-- Comments
COMMENT ON TABLE survey_details IS 'Event log of all survey interactions for analytics and reconstruction';
COMMENT ON COLUMN survey_details.event_type IS 'Type of event: question_generated, answer_submitted, answer_updated, answer_skipped, question_updated, survey_incomplete, survey_aborted, survey_completed';
COMMENT ON COLUMN survey_details.event_detail IS 'Flexible JSONB field containing event-specific data (question, answer, metadata). Can be empty for survey_incomplete/survey_aborted events';
