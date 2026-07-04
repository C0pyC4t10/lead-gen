import os, hashlib, secrets, json, sys
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://', 1)

def get_db():
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    conn.autocommit = False
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''
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
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    c.execute('''
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
        )
    ''')
    conn.commit()
    conn.close()

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, h

def require_auth():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth[7:]
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT u.* FROM sessions s JOIN users u ON s.user_id = u.id WHERE s.token = %s', (token,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e), 'type': type(e).__name__}), 500

# ── Health ──
@app.route('/api/health')
def health():
    try:
        conn = get_db()
        conn.close()
        return jsonify({'status': 'ok', 'db': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'db': str(e)}), 500

# ── Auth ──
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({'error': 'name, email, password required'}), 400
    name = data['name'].strip()
    email = data['email'].strip().lower()
    password = data['password']
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE email = %s', (email,))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Email already registered'}), 409
    salt, pw_hash = hash_password(password)
    now = datetime.now(timezone.utc).isoformat()
    c.execute('INSERT INTO users (name, email, password_hash, password_salt, created_at, updated_at) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id',
              (name, email, pw_hash, salt, now, now))
    uid = c.fetchone()[0]
    conn.commit()
    token = secrets.token_hex(32)
    c.execute('INSERT INTO sessions (user_id, token, created_at) VALUES (%s,%s,%s)', (uid, token, now))
    conn.commit()
    conn.close()
    return jsonify({'token': token, 'user': {'id': uid, 'name': name, 'email': email, 'role': 'user', 'subscription_tier': 'free'}}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'email and password required'}), 400
    email = data['email'].strip().lower()
    password = data['password']
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = c.fetchone()
    if not user:
        conn.close()
        return jsonify({'error': 'Invalid email or password'}), 401
    _, expected_hash = hash_password(password, user['password_salt'])
    if expected_hash != user['password_hash']:
        conn.close()
        return jsonify({'error': 'Invalid email or password'}), 401
    now = datetime.now(timezone.utc).isoformat()
    token = secrets.token_hex(32)
    c.execute('INSERT INTO sessions (user_id, token, created_at) VALUES (%s,%s,%s)', (user['id'], token, now))
    conn.commit()
    conn.close()
    return jsonify({'token': token, 'user': {'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role'], 'subscription_tier': user['subscription_tier']}})

@app.route('/api/auth/me')
def me():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'id': user['id'], 'name': user['name'], 'email': user['email'], 'role': user['role'], 'subscription_tier': user['subscription_tier'], 'email_verified': user.get('email_verified', 1)})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'ok': True})
    token = auth[7:]
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM sessions WHERE token = %s', (token,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/api/auth/leads-remaining')
def leads_remaining():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    limit = 999999 if user['subscription_tier'] in ('pro', 'admin') else 20
    return jsonify({'leads_used': user.get('leads_used', 0), 'leads_limit': limit})

# ── Leads ──
@app.route('/api/leads')
def list_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    status_filter = request.args.get('status')
    is_admin = user['role'] in ('admin', 'super_admin')
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if is_admin:
        if status_filter:
            c.execute("SELECT * FROM leads WHERE status = %s AND (deleted_at IS NULL OR deleted_at = '') ORDER BY created_at DESC", (status_filter,))
        else:
            c.execute("SELECT * FROM leads WHERE (deleted_at IS NULL OR deleted_at = '') ORDER BY created_at DESC")
    else:
        if status_filter:
            c.execute("SELECT * FROM leads WHERE saved_by_user_id = %s AND status = %s AND (deleted_at IS NULL OR deleted_at = '') ORDER BY created_at DESC", (user['id'], status_filter))
        else:
            c.execute("SELECT * FROM leads WHERE saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '') ORDER BY created_at DESC", (user['id'],))
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/leads/trash')
def trash_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user['role'] in ('admin', 'super_admin')
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if is_admin:
        c.execute("SELECT * FROM leads WHERE deleted_at IS NOT NULL AND deleted_at != '' ORDER BY deleted_at DESC")
    else:
        c.execute("SELECT * FROM leads WHERE saved_by_user_id = %s AND deleted_at IS NOT NULL AND deleted_at != '' ORDER BY deleted_at DESC", (user['id'],))
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/trash/stats')
def trash_stats():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user['role'] in ('admin', 'super_admin')
    conn = get_db()
    c = conn.cursor()
    if is_admin:
        c.execute("SELECT COUNT(*) FROM leads WHERE deleted_at IS NOT NULL AND deleted_at != ''")
    else:
        c.execute("SELECT COUNT(*) FROM leads WHERE saved_by_user_id = %s AND deleted_at IS NOT NULL AND deleted_at != ''", (user['id'],))
    count = c.fetchone()[0]
    conn.close()
    return jsonify({'trashed_count': count})

@app.route('/api/lead', methods=['POST'])
def save_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM leads WHERE page_url = %s AND saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '')", (page_url, user['id']))
    existing = c.fetchone()
    if existing:
        conn.close()
        return jsonify({'status': 'duplicate', 'message': 'Lead already exists, skipped'})
    limit = 999999 if user['subscription_tier'] in ('pro', 'admin') else 20
    if user.get('leads_used', 0) >= limit:
        conn.close()
        return jsonify({'error': 'Lead limit reached', 'limit_reached': True}), 403
    c.execute('''
        INSERT INTO leads (date, platform, business_name, page_url, category, followers, email, phone, website, has_website, address, last_post_date, qualification_score, status, notes, follow_up_date, open_state, hours_text, saved_by_user_id, saved_by_user_name, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    ''', (
        data.get('date', now[:10]), data.get('platform', ''), data.get('business_name', ''),
        page_url, data.get('category', ''), data.get('followers', ''),
        data.get('email', ''), data.get('phone', ''), data.get('website', ''),
        data.get('has_website', ''), data.get('address', ''), data.get('last_post_date', ''),
        data.get('qualification_score', ''), data.get('status', 'new'),
        data.get('notes', ''), data.get('follow_up_date', ''), data.get('open_state', ''),
        data.get('hours_text', ''), user['id'], user.get('name', ''), now
    ))
    c.execute('UPDATE users SET leads_used = leads_used + 1 WHERE id = %s', (user['id'],))
    conn.commit()
    conn.close()
    remaining = limit - user.get('leads_used', 0) - 1
    return jsonify({'status': 'saved', 'message': 'Lead saved', 'leads_remaining': max(0, remaining)}), 201

@app.route('/api/lead', methods=['GET'])
def get_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    url_param = request.args.get('url', '')
    is_admin = user['role'] in ('admin', 'super_admin')
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if is_admin:
        c.execute("SELECT * FROM leads WHERE page_url = %s AND (deleted_at IS NULL OR deleted_at = '')", (url_param,))
    else:
        c.execute("SELECT * FROM leads WHERE page_url = %s AND saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '')", (url_param, user['id']))
    lead = c.fetchone()
    conn.close()
    if lead:
        return jsonify(dict(lead))
    return jsonify({'error': 'Lead not found'}), 404

@app.route('/api/lead/status', methods=['POST'])
def update_lead_status():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    page_url = (data.get('page_url') or '').strip()
    new_status = (data.get('status') or '').strip().lower()
    follow_up = (data.get('follow_up_date') or '').strip()
    if not page_url or not new_status:
        return jsonify({'error': 'page_url and status required'}), 400
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE leads SET status = %s, follow_up_date = COALESCE(NULLIF(%s, ''), follow_up_date) WHERE page_url = %s AND saved_by_user_id = %s",
              (new_status, follow_up, page_url, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'updated', 'message': 'Status updated'})

@app.route('/api/lead/delete', methods=['POST'])
def delete_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE leads SET deleted_at = %s WHERE page_url = %s AND saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '')", (now, page_url, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'deleted'})

@app.route('/api/lead/bulk-trash', methods=['POST'])
def bulk_trash():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    urls = data.get('urls', [])
    if not urls:
        return jsonify({'error': 'urls required'}), 400
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    c = conn.cursor()
    for url in urls:
        c.execute("UPDATE leads SET deleted_at = %s WHERE page_url = %s AND saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '')", (now, url, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'trashed', 'count': len(urls)})

@app.route('/api/lead/bulk-restore', methods=['POST'])
def bulk_restore():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    urls = data.get('urls', [])
    conn = get_db()
    c = conn.cursor()
    for url in urls:
        c.execute("UPDATE leads SET deleted_at = NULL WHERE page_url = %s AND saved_by_user_id = %s", (url, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'restored', 'count': len(urls)})

@app.route('/api/lead/bulk-purge', methods=['POST'])
def bulk_purge():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    urls = data.get('urls', [])
    conn = get_db()
    c = conn.cursor()
    for url in urls:
        c.execute("DELETE FROM leads WHERE page_url = %s AND saved_by_user_id = %s AND deleted_at IS NOT NULL AND deleted_at != ''", (url, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'status': 'purged', 'count': len(urls)})

@app.route('/api/lead/action', methods=['POST'])
def lead_action():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    action = data.get('action')
    page_url = data.get('page_url', '').strip()
    if not action or not page_url:
        return jsonify({'error': 'action and page_url required'}), 400
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    c = conn.cursor()
    if action == 'qualified':
        c.execute("UPDATE leads SET status = 'qualified', qualification_score = '90' WHERE page_url = %s AND saved_by_user_id = %s", (page_url, user['id']))
    elif action == 'contacted':
        c.execute("UPDATE leads SET status = 'contacted' WHERE page_url = %s AND saved_by_user_id = %s", (page_url, user['id']))
    elif action == 'reset':
        c.execute("UPDATE leads SET status = 'new', qualification_score = '' WHERE page_url = %s AND saved_by_user_id = %s", (page_url, user['id']))
    else:
        conn.close()
        return jsonify({'error': 'Unknown action'}), 400
    conn.commit()
    conn.close()
    return jsonify({'status': 'ok', 'action': action})

# ── Funnel stats ──
@app.route('/api/funnel')
def funnel_stats():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user['role'] in ('admin', 'super_admin')
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if is_admin:
        c.execute("SELECT status, COUNT(*) as count FROM leads WHERE (deleted_at IS NULL OR deleted_at = '') GROUP BY status")
    else:
        c.execute("SELECT status, COUNT(*) as count FROM leads WHERE saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '') GROUP BY status", (user['id'],))
    rows = c.fetchall()
    total = sum(r['count'] for r in rows)
    conn.close()
    return jsonify({'total': total, 'breakdown': {r['status']: r['count'] for r in rows}})

@app.route('/api/last-lead')
def last_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT page_url FROM leads WHERE saved_by_user_id = %s AND (deleted_at IS NULL OR deleted_at = '') ORDER BY created_at DESC LIMIT 1", (user['id'],))
    row = c.fetchone()
    conn.close()
    if row:
        return jsonify({'page_url': row['page_url']})
    return jsonify({'error': 'No recent lead'}), 404

@app.route('/api/leads/qualified')
def qualified_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    c.execute("SELECT * FROM leads WHERE status = 'qualified' AND (deleted_at IS NULL OR deleted_at = '') ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])
