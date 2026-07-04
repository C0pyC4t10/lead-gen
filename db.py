"""Database abstraction layer.

Uses Supabase Postgres if DATABASE_URL is set, otherwise falls back to local SQLite.
This lets the same code run on Render (Postgres) and locally (SQLite) without changes.

Schema is created lazily on first connection. Migrations are idempotent.
"""
import os
import sqlite3
import threading
from contextlib import contextmanager

_local_lock = threading.Lock()

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()
USE_POSTGRES = bool(DATABASE_URL)

AUTH_DB_PATH = os.environ.get(
    'AUTH_DB_PATH',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')
)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
    _conn_str = DATABASE_URL
    if _conn_str.startswith('postgres://'):
        _conn_str = _conn_str.replace('postgres://', 'postgresql://', 1)

    def _connect():
        conn = psycopg2.connect(_conn_str, connect_timeout=10)
        conn.autocommit = False
        return conn

    @contextmanager
    def auth_conn():
        conn = _connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_auth_db():
        with auth_conn() as conn:
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'user',
                    email_verified INTEGER DEFAULT 0,
                    verification_code TEXT,
                    verification_expires TEXT,
                    leads_used INTEGER DEFAULT 0,
                    subscription_tier TEXT DEFAULT 'free',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    telegram_notifications INTEGER DEFAULT 1
                )
            ''')
            c.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_token TEXT')
            c.execute('ALTER TABLE users ADD COLUMN IF NOT EXISTS password_reset_expires TEXT')
            c.execute('CREATE TABLE IF NOT EXISTS sessions (id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, token TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS settings (id SERIAL PRIMARY KEY, user_id INTEGER UNIQUE NOT NULL, theme TEXT DEFAULT \'dark\', notifications INTEGER DEFAULT 1)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')

    def _q(sql, params=None):
        """Convert sqlite ? placeholders to psycopg2 %s."""
        return sql.replace('?', '%s')

else:
    @contextmanager
    def auth_conn():
        conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _q(sql, params=None):
        return sql

    def init_auth_db():
        with auth_conn() as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                email_verified INTEGER DEFAULT 0,
                verification_code TEXT,
                verification_expires TEXT,
                leads_used INTEGER DEFAULT 0,
                subscription_tier TEXT DEFAULT 'free',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                telegram_notifications INTEGER DEFAULT 1
            )''')
            for col in ('email_verified', 'verification_code', 'verification_expires', 'leads_used', 'subscription_tier', 'password_reset_token', 'password_reset_expires', 'telegram_notifications'):
                try:
                    c.execute(f'ALTER TABLE users ADD COLUMN {col} TEXT')
                except sqlite3.OperationalError:
                    pass
            c.execute("UPDATE users SET telegram_notifications = 1 WHERE telegram_notifications IS NULL")
            c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')
            c.execute('''CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                theme TEXT DEFAULT 'dark',
                notifications INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )''')


def fetchone(sql, params=()):
    with auth_conn() as conn:
        c = conn.cursor()
        c.execute(_q(sql), params)
        row = c.fetchone()
        if row is None:
            return None
        if USE_POSTGRES:
            cols = [d[0] for d in c.description]
            return dict(zip(cols, row))
        return dict(row)


def fetchall(sql, params=()):
    with auth_conn() as conn:
        c = conn.cursor()
        c.execute(_q(sql), params)
        rows = c.fetchall()
        if USE_POSTGRES:
            cols = [d[0] for d in c.description]
            return [dict(zip(cols, r)) for r in rows]
        return [dict(r) for r in rows]


def execute(sql, params=()):
    with auth_conn() as conn:
        c = conn.cursor()
        c.execute(_q(sql), params)
        if USE_POSTGRES:
            try:
                return c.fetchone()[0]
            except (psycopg2.ProgrammingError, TypeError):
                return None
        return c.lastrowid