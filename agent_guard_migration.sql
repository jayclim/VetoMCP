-- Agent Guard Rails Migration (UUID version)
-- Run this in the Supabase SQL Editor AFTER running supabase_migration.sql

-- ══════════════════════════════════════════════════════════════════════════════
-- Agent Settings: User-configurable spending limits for autonomous agents
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS veto_agent_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES veto_users (id) ON DELETE CASCADE,
    
    -- Spending limits
    single_transaction_limit FLOAT8 NOT NULL DEFAULT 50.0,
    daily_limit FLOAT8 NOT NULL DEFAULT 100.0,
    weekly_limit FLOAT8 NOT NULL DEFAULT 500.0,
    monthly_limit FLOAT8 NOT NULL DEFAULT 2000.0,
    require_approval_above FLOAT8 NOT NULL DEFAULT 100.0,
    
    -- Category restrictions (JSON arrays stored as TEXT)
    allowed_categories TEXT,  -- null = all allowed
    blocked_categories TEXT DEFAULT '[]',
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- One settings row per user
    UNIQUE (user_id)
);

CREATE INDEX IF NOT EXISTS idx_veto_agent_settings_user_id ON veto_agent_settings (user_id);

-- ══════════════════════════════════════════════════════════════════════════════
-- Agent Authorization Log: Audit trail for all agent authorization attempts
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS veto_agent_authorization_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES veto_users (id) ON DELETE CASCADE,
    
    -- Request details
    agent_id TEXT,  -- Optional identifier for the requesting agent
    action_type TEXT NOT NULL,  -- 'purchase', 'transfer', 'subscription', 'recurring_payment'
    amount FLOAT8 NOT NULL,
    category TEXT,
    merchant TEXT,
    description TEXT,
    
    -- Authorization result
    status TEXT NOT NULL,  -- 'APPROVED', 'DENIED', 'CAUTION', 'REQUIRES_HUMAN_APPROVAL', 'ERROR'
    reason TEXT,
    risk_score INT,
    
    -- Token for tracking
    authorization_token TEXT UNIQUE,
    
    -- Whether the action was actually executed after authorization
    was_executed BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_veto_agent_auth_user_id ON veto_agent_authorization_log (user_id);
CREATE INDEX IF NOT EXISTS idx_veto_agent_auth_created_at ON veto_agent_authorization_log (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_veto_agent_auth_token ON veto_agent_authorization_log (authorization_token);

-- ══════════════════════════════════════════════════════════════════════════════
-- Row Level Security
-- ══════════════════════════════════════════════════════════════════════════════
ALTER TABLE veto_agent_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE veto_agent_authorization_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access" ON veto_agent_settings
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role full access" ON veto_agent_authorization_log
    FOR ALL USING (true) WITH CHECK (true);
