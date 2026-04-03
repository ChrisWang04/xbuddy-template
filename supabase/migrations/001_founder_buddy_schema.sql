-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Business Plans Table
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

-- Section States Table
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

-- Conversation Messages Table (for full history)
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

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_business_plans_user_thread ON business_plans(user_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_section_states_user_thread ON section_states(user_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_section_states_section ON section_states(section_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON conversation_messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_thread ON conversation_messages(user_id, thread_id);

-- Enable Row Level Security (RLS) - Optional, can be disabled if using service role key
-- ALTER TABLE business_plans ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE section_states ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_messages ENABLE ROW LEVEL SECURITY;

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at
CREATE TRIGGER update_business_plans_updated_at BEFORE UPDATE ON business_plans
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_section_states_updated_at BEFORE UPDATE ON section_states
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Enable Realtime for section_states (for frontend editing)
ALTER PUBLICATION supabase_realtime ADD TABLE section_states;
ALTER PUBLICATION supabase_realtime ADD TABLE business_plans;




