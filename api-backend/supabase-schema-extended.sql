-- Run this in Supabase SQL Editor (after the original schema)

-- Add missing columns to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_code TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS verification_expires TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_notifications INTEGER DEFAULT 1;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- Qualified leads table
CREATE TABLE IF NOT EXISTS qualified_leads (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER,
    page_url TEXT,
    business_name TEXT,
    phone TEXT,
    email TEXT,
    category TEXT,
    qualification_score TEXT,
    qualified_at TEXT NOT NULL,
    qualified_by INTEGER,
    qualified_by_name TEXT,
    saved_by_user_id INTEGER DEFAULT 0,
    notes TEXT
);
ALTER TABLE qualified_leads DISABLE ROW LEVEL SECURITY;

-- F-commerce leads
CREATE TABLE IF NOT EXISTS fcommerce_leads (
    id SERIAL PRIMARY KEY,
    date TEXT,
    source TEXT,
    business_name TEXT,
    page_url TEXT,
    followers_int TEXT,
    has_website TEXT,
    order_method TEXT,
    last_post_date TEXT,
    product_categories TEXT,
    discovery_source TEXT,
    qualification_score TEXT,
    priority TEXT,
    opportunity_flags TEXT,
    email TEXT,
    phone TEXT,
    address TEXT,
    status TEXT DEFAULT 'new',
    notes TEXT,
    created_at TEXT NOT NULL
);
ALTER TABLE fcommerce_leads DISABLE ROW LEVEL SECURITY;

-- LinkedIn leads
CREATE TABLE IF NOT EXISTS linkedin_leads (
    id SERIAL PRIMARY KEY,
    date TEXT,
    name TEXT,
    headline TEXT,
    company TEXT,
    location TEXT,
    url TEXT,
    kb_score TEXT,
    kb_category TEXT,
    matched_products TEXT,
    status TEXT DEFAULT 'new',
    source TEXT
);
ALTER TABLE linkedin_leads DISABLE ROW LEVEL SECURITY;

-- Maps leads (legacy)
CREATE TABLE IF NOT EXISTS maps_leads (
    id SERIAL PRIMARY KEY,
    date TEXT,
    business_name TEXT,
    page_url TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    category TEXT,
    notes TEXT,
    status TEXT DEFAULT 'new',
    created_at TEXT NOT NULL
);
ALTER TABLE maps_leads DISABLE ROW LEVEL SECURITY;

-- Lead action log (audit trail)
CREATE TABLE IF NOT EXISTS lead_actions (
    id SERIAL PRIMARY KEY,
    lead_id INTEGER,
    user_id INTEGER,
    action TEXT,
    payload TEXT,
    created_at TEXT NOT NULL
);
ALTER TABLE lead_actions DISABLE ROW LEVEL SECURITY;

-- Login attempt rate limit
CREATE TABLE IF NOT EXISTS login_attempts (
    id SERIAL PRIMARY KEY,
    ip TEXT NOT NULL,
    attempted_at TEXT NOT NULL
);
ALTER TABLE login_attempts DISABLE ROW LEVEL SECURITY;

-- Outreach history
CREATE TABLE IF NOT EXISTS outreach_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    business_name TEXT,
    page_url TEXT,
    netlify_url TEXT,
    build_time TEXT,
    created_at TEXT NOT NULL
);
ALTER TABLE outreach_history DISABLE ROW LEVEL SECURITY;

-- Create Storage bucket for avatars (run separately if needed)
-- INSERT INTO storage.buckets (id, name, public) VALUES ('avatars', 'avatars', true) ON CONFLICT DO NOTHING;