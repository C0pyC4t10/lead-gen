"""Unified auth storage layer.

Routes user CRUD to:
  - MongoDB (mongo_db.py) when MONGODB_URI env is set and reachable
  - SQLite (auth.db) otherwise (local dev fallback)

Sessions are stateless JWTs in this app, so no session storage here.
The users table is the only thing persisted.
"""
import os
import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone

AUTH_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')


def _use_mongo():
    """Runtime check: MongoDB configured AND connected.

    Uses is_ready() — never triggers a connect from a request thread.
    Mongo init is owned by the background thread in server.py.
    """
    if not os.environ.get('MONGODB_URI', '').strip():
        return False
    try:
        import mongo_db
        return mongo_db.is_ready()
    except Exception:
        return False


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _sqlite_conn():
    conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    return conn


def _user_row_to_dict(row):
    """Normalize a sqlite Row to dict with id/name/email/role/email_verified/leads_used/subscription_tier/avatar_url."""
    if not row:
        return None
    d = dict(row)
    if 'email_verified' in d:
        d['email_verified'] = bool(d.get('email_verified') or 0)
    if 'leads_used' in d:
        try:
            d['leads_used'] = int(d.get('leads_used') or 0)
        except Exception:
            d['leads_used'] = 0
    return d


# ─── User lookups ───────────────────────────────────────────────────────

def get_user_by_id(uid):
    if _use_mongo():
        import mongo_db
        u = mongo_db.get_user_by_id(uid)
        if not u:
            return None
        d = mongo_db.serialize(u)
        d.setdefault('id', str(u.get('_id')))
        d.setdefault('leads_used', 0)
        d.setdefault('email_verified', False)
        d.setdefault('subscription_tier', 'free')
        return d
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('SELECT id, name, email, role, COALESCE(email_verified, 0) AS email_verified, COALESCE(leads_used, 0) AS leads_used, COALESCE(subscription_tier, "free") AS subscription_tier, telegram_notifications, avatar_url, password_hash, password_salt, verification_code, verification_expires, password_reset_token, password_reset_expires FROM users WHERE id = ?', (uid,))
        return _user_row_to_dict(c.fetchone())
    finally:
        conn.close()


def get_user_by_email(email):
    """Returns FULL dict incl. password_hash/password_salt (login use only)."""
    if _use_mongo():
        import mongo_db
        u = mongo_db.get_user_by_email(email)
        if not u:
            return None
        d = mongo_db.serialize(u)
        d.setdefault('id', str(u.get('_id')))
        d.setdefault('leads_used', 0)
        d.setdefault('email_verified', False)
        d.setdefault('subscription_tier', 'free')
        return d
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('SELECT id, name, email, role, COALESCE(email_verified, 0) AS email_verified, COALESCE(leads_used, 0) AS leads_used, COALESCE(subscription_tier, "free") AS subscription_tier, password_hash, password_salt, telegram_notifications, avatar_url FROM users WHERE email = ?', (email,))
        return _user_row_to_dict(c.fetchone())
    finally:
        conn.close()


def get_user_public_by_id(uid):
    """Same as get_user_by_id but strips password fields."""
    u = get_user_by_id(uid)
    if u:
        u.pop('password_hash', None)
        u.pop('password_salt', None)
    return u


def get_user_role(uid):
    u = get_user_by_id(uid)
    return u.get('role') if u else None


def email_exists(email, exclude_uid=None):
    if _use_mongo():
        import mongo_db
        u = mongo_db.get_user_by_email(email)
        if not u:
            return False
        return exclude_uid is None or str(u.get('_id')) != str(exclude_uid)
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        if exclude_uid is not None:
            c.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, exclude_uid))
        else:
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
        return c.fetchone() is not None
    finally:
        conn.close()


# ─── User creation ──────────────────────────────────────────────────────

def create_user(name, email, password_hash, password_salt, role='user'):
    """Insert and return new user id (str/int)."""
    if _use_mongo():
        import mongo_db
        u = mongo_db.create_user(name, email, password_hash, password_salt, role=role)
        return str(u['_id']) if u else None
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        now = _now_iso()
        c.execute('''INSERT INTO users (name, email, password_hash, password_salt, role,
                     email_verified, created_at, updated_at, telegram_notifications)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (name, email, password_hash, password_salt, role, 0, now, now, 1))
        uid = c.lastrowid
        c.execute('INSERT OR IGNORE INTO settings (user_id) VALUES (?)', (uid,))
        conn.commit()
        return uid
    finally:
        conn.close()


# ─── User updates ───────────────────────────────────────────────────────

def update_user_fields(uid, **fields):
    """Generic field update. e.g. update_user_fields(uid, name='X', avatar_url='y')."""
    if not fields:
        return True
    if _use_mongo():
        import mongo_db
        return bool(mongo_db.update_user(uid, fields))
    allowed = {'name', 'email', 'role', 'email_verified', 'verification_code',
               'verification_expires', 'leads_used', 'subscription_tier',
               'telegram_notifications', 'avatar_url', 'password_hash',
               'password_salt', 'password_reset_token', 'password_reset_expires'}
    safe = {k: v for k, v in fields.items() if k in allowed}
    if not safe:
        return True
    safe['updated_at'] = _now_iso()
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        sets = ', '.join(f'{k} = ?' for k in safe)
        vals = list(safe.values()) + [uid]
        c.execute(f'UPDATE users SET {sets} WHERE id = ?', vals)
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()


def increment_leads_used(uid):
    if _use_mongo():
        import mongo_db
        u = mongo_db.get_user_by_id(uid)
        if not u:
            return False
        new_count = (u.get('leads_used') or 0) + 1
        return bool(mongo_db.update_user(uid, {'leads_used': new_count}))
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('UPDATE users SET leads_used = COALESCE(leads_used, 0) + 1, updated_at = ? WHERE id = ?', (_now_iso(), uid))
        conn.commit()
        return c.rowcount > 0
    finally:
        conn.close()


def get_verification_code(uid):
    u = get_user_by_id(uid)
    if not u:
        return None
    return u.get('verification_code'), u.get('verification_expires')


def set_verification_code(uid, code, expires):
    return update_user_fields(uid, verification_code=code, verification_expires=expires, email_verified=0)


def get_user_by_reset_token(token):
    if _use_mongo():
        import mongo_db
        db = mongo_db.get_db()
        u = db.users.find_one({'password_reset_token': token})
        if not u:
            return None
        d = mongo_db.serialize(u)
        d.setdefault('id', str(u.get('_id')))
        return d
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('SELECT id, name, email, role, password_reset_expires FROM users WHERE password_reset_token = ?', (token,))
        return _user_row_to_dict(c.fetchone())
    finally:
        conn.close()


def update_password(uid, password_hash, password_salt):
    return update_user_fields(uid, password_hash=password_hash, password_salt=password_salt, password_reset_token=None, password_reset_expires=None)


# ─── Admin / listings ───────────────────────────────────────────────────

def list_users_for_admin():
    if _use_mongo():
        import mongo_db
        users = mongo_db.list_users()
        out = []
        for u in users:
            d = mongo_db.serialize(u)
            d.setdefault('id', str(u.get('_id')))
            d.pop('password_hash', None)
            d.pop('password_salt', None)
            out.append(d)
        return out
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('SELECT id, name, email, role, COALESCE(email_verified, 0) AS email_verified, COALESCE(leads_used, 0) AS leads_used, COALESCE(subscription_tier, "free") AS subscription_tier, created_at, COALESCE(telegram_notifications, 1) AS telegram_notifications FROM users ORDER BY id')
        return [_user_row_to_dict(r) for r in c.fetchall()]
    finally:
        conn.close()


def count_users_by_role():
    if _use_mongo():
        import mongo_db
        return mongo_db.count_users_grouped_by_role()
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
        return {r[0]: r[1] for r in c.fetchall()}
    finally:
        conn.close()


def get_telegram_notifications(uid):
    u = get_user_by_id(uid)
    if not u:
        return True
    val = u.get('telegram_notifications')
    return val is None or bool(int(val))


# ─── Init / schema ─────────────────────────────────────────────────────

def init_auth_db():
    """Create SQLite tables if using SQLite. Mongo doesn't need this (mongo_db._ensure_indexes runs on connect)."""
    if _use_mongo():
        return
    conn = _sqlite_conn()
    try:
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
        for col, default in (
            ('email_verified', '0'),
            ('verification_code', None),
            ('verification_expires', None),
            ('leads_used', '0'),
            ('subscription_tier', '"free"'),
            ('password_reset_token', None),
            ('password_reset_expires', None),
            ('telegram_notifications', '1'),
            ('avatar_url', None),
        ):
            try:
                c.execute(f'ALTER TABLE users ADD COLUMN {col} TEXT')
            except sqlite3.OperationalError:
                pass
        c.execute('UPDATE users SET telegram_notifications = 1 WHERE telegram_notifications IS NULL')
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            theme TEXT DEFAULT 'dark',
            notifications INTEGER DEFAULT 1
        )''')
        conn.commit()
    finally:
        conn.close()


def count_users():
    """Total user count (any storage)."""
    if _use_mongo():
        import mongo_db
        db = mongo_db.get_db()
        return db.users.count_documents({}) if db else 0
    conn = _sqlite_conn()
    try:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM users')
        return c.fetchone()[0]
    finally:
        conn.close()
