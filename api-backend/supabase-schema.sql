-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    email_verified INTEGER DEFAULT 1,
    leads_used INTEGER DEFAULT 0,
    subscription_tier TEXT DEFAULT 'free',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    platform TEXT DEFAULT '',
    business_name TEXT DEFAULT '',
    page_url TEXT DEFAULT '',
    category TEXT DEFAULT '',
    followers TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    website TEXT DEFAULT '',
    has_website TEXT DEFAULT '',
    address TEXT DEFAULT '',
    last_post_date TEXT DEFAULT '',
    qualification_score TEXT DEFAULT '',
    status TEXT DEFAULT 'new',
    notes TEXT DEFAULT '',
    follow_up_date TEXT DEFAULT '',
    open_state TEXT DEFAULT '',
    hours_text TEXT DEFAULT '',
    deleted_at TEXT DEFAULT NULL,
    saved_by_user_id INTEGER DEFAULT 0,
    saved_by_user_name TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_user ON leads(saved_by_user_id);
CREATE INDEX IF NOT EXISTS idx_leads_page_url ON leads(page_url);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
