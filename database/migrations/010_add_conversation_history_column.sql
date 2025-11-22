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
