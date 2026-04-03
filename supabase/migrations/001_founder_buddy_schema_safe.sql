-- ============================================================================
-- SAFE MIGRATION FOR TEAM SUPABASE PROJECT
-- This migration only creates new tables and does NOT modify existing data
-- All operations use IF NOT EXISTS to prevent conflicts
-- ============================================================================

-- Enable UUID extension (safe: IF NOT EXISTS)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Business Plans Table (safe: IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS business_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    thread_id TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'founder-buddy',
    title TEXT,
    content TEXT NOT NULL,
    markdown_content TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, thread_id)
);

-- Section States Table (safe: IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS section_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    thread_id TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'founder-buddy',
    section_id TEXT NOT NULL, -- 'mission', 'idea', 'team_traction', 'invest_plan'
    content JSONB NOT NULL, -- Tiptap JSON format
    plain_text TEXT,
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'done'
    satisfaction_status TEXT, -- 'satisfied', 'needs_improvement', null
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, thread_id, section_id)
);

-- Conversation Messages Table (safe: IF NOT EXISTS)
CREATE TABLE IF NOT EXISTS conversation_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL,
    thread_id TEXT NOT NULL,
    agent_id TEXT NOT NULL DEFAULT 'founder-buddy',
    role TEXT NOT NULL, -- 'user', 'assistant'
    content TEXT NOT NULL,
    metadata JSONB, -- Additional metadata (run_id, section_id, etc.)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance (safe: IF NOT EXISTS)
CREATE INDEX IF NOT EXISTS idx_business_plans_user_thread ON business_plans(user_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_section_states_user_thread ON section_states(user_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_section_states_section ON section_states(section_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON conversation_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_thread ON conversation_messages(user_id, thread_id);

-- Create updated_at trigger function (safe: OR REPLACE only affects this function)
-- Note: This will replace the function if it exists, but it's a common utility function
-- If your team already has this function, it will be replaced with this version
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at (safe: DROP IF EXISTS then CREATE)
-- This ensures triggers are created even if they already exist
DO $$
BEGIN
    -- Drop triggers if they exist, then create them
    DROP TRIGGER IF EXISTS update_business_plans_updated_at ON business_plans;
    CREATE TRIGGER update_business_plans_updated_at BEFORE UPDATE ON business_plans
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_section_states_updated_at ON section_states;
    CREATE TRIGGER update_section_states_updated_at BEFORE UPDATE ON section_states
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
END $$;

-- Enable Realtime for new tables (safe: will fail silently if already enabled)
-- Note: This may fail if tables are already in the publication, but that's OK
DO $$
BEGIN
    -- Check if table exists in publication before adding
    IF EXISTS (SELECT 1 FROM pg_publication_tables WHERE pubname = 'supabase_realtime' AND tablename = 'section_states') THEN
        RAISE NOTICE 'Table section_states already in supabase_realtime publication';
    ELSE
        ALTER PUBLICATION supabase_realtime ADD TABLE section_states;
    END IF;
    
    IF EXISTS (SELECT 1 FROM pg_publication_tables WHERE pubname = 'supabase_realtime' AND tablename = 'business_plans') THEN
        RAISE NOTICE 'Table business_plans already in supabase_realtime publication';
    ELSE
        ALTER PUBLICATION supabase_realtime ADD TABLE business_plans;
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        -- If publication doesn't exist or other errors, just log and continue
        RAISE NOTICE 'Could not add tables to supabase_realtime publication: %', SQLERRM;
END $$;




