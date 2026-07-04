"""Scraven Lead Gen API - Vercel + Supabase version.

Comprehensive API covering all endpoints from the original server.py
except Playwright-dependent extraction (which needs a worker with Chromium).
"""
import os, hashlib, secrets, json, time, smtplib, base64
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ── Supabase config ──
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://lkmgyvkqbdftpgyvpcrd.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxrbWd5dmtxYmRmdHBneXZwY3JkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzE3MDUzOCwiZXhwIjoyMDk4NzQ2NTM4fQ.nWfWIAgs-MgVAkAx67Spfj4QEr0KFH1D4aQTAHLTBqQ')
REST = f'{SUPABASE_URL}/rest/v1'
STORAGE = f'{SUPABASE_URL}/storage/v1'
HEADERS = {
    'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json', 'Prefer': 'return=representation',
}

# ── Email config ──
GMAIL_USER = os.environ.get('GMAIL_USER', 'jahid.skarbol@gmail.com')
GMAIL_APP_PASS = os.environ.get('GMAIL_APP_PASS', '')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'jahid.skarbol@gmail.com')

# ── API keys ──
APIFY_TOKEN = os.environ.get('APIFY_TOKEN', '')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')

# ── DB helpers ──
def query(table, params=None, method='GET', data=None, headers=None):
    url = f'{REST}/{table}'
    h = {**HEADERS, **(headers or {})}
    try:
        if method == 'GET':
            r = requests.get(url, headers=h, params=params, timeout=25)
        elif method == 'POST':
            r = requests.post(url, headers=h, json=data, params=params, timeout=25)
        elif method == 'PATCH':
            r = requests.patch(url, headers=h, json=data, params=params, timeout=25)
        elif method == 'DELETE':
            r = requests.delete(url, headers=h, params=params, timeout=25)
        if r.status_code >= 300:
            return {'_error': r.text, '_status': r.status_code}
        if not r.text:
            return []
        return r.json()
    except Exception as e:
        return {'_error': str(e), '_status': 500}

def send_email(to, subject, html):
    if not GMAIL_USER or not GMAIL_APP_PASS:
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = GMAIL_USER
        msg['To'] = to
        msg.attach(MIMEText(html, 'html'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f'Email error: {e}', flush=True)
        return False

def send_telegram(text):
    if not TELEGRAM_TOKEN:
        return False
    try:
        url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
        requests.post(url, json={'chat_id': -1004334910291, 'message_thread_id': 354, 'text': text, 'parse_mode': 'HTML'}, timeout=10)
        return True
    except:
        return False

# ── Auth helpers ──
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return salt, h

def require_auth():
    auth = request.headers.get('Authorization', '')
    token_q = request.args.get('token', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
    elif token_q:
        token = token_q
    else:
        return None
    rows = query('sessions', params={'token': f'eq.{token}', 'limit': '1'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        return None
    user_id = rows[0].get('user_id')
    if not user_id:
        return None
    users = query('users', params={'id': f'eq.{user_id}', 'limit': '1'})
    if not users or isinstance(users, dict) or len(users) == 0:
        return None
    return users[0]

def check_login_rate_limit(ip):
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    rows = query('login_attempts', params={'ip': f'eq.{ip}', 'attempted_at': f'gt.{cutoff}', 'select': 'count'})
    if isinstance(rows, list) and len(rows) > 0:
        return rows[0].get('count', 0) < 5
    return True

def record_login_attempt(ip):
    query('login_attempts', method='POST', data={
        'ip': ip, 'attempted_at': datetime.now(timezone.utc).isoformat(),
    })

def get_lead_limit(user):
    tier = user.get('subscription_tier', 'free')
    if user.get('role') in ('admin', 'super_admin'):
        return 999999
    return 999999 if tier == 'pro' else 20

# ── Error handler ──
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e), 'type': type(e).__name__}), 500

# ── CORS ──
@app.after_request
def add_cors(response):
    origin = request.headers.get('Origin', '')
    response.headers['Access-Control-Allow-Origin'] = origin or '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# ═════════════════════════════════════════════════════════════
# HEALTH
# ═════════════════════════════════════════════════════════════
@app.route('/api/health')
def health():
    try:
        rows = query('users', params={'select': 'count', 'limit': '1'})
        if isinstance(rows, dict) and rows.get('_error'):
            return jsonify({'status': 'error', 'db': rows['_error']}), 500
        return jsonify({'status': 'ok', 'db': 'connected'})
    except Exception as e:
        return jsonify({'status': 'error', 'db': str(e)}), 500

# ═════════════════════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════════════════════
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not name or not email or not password:
        return jsonify({'error': 'name, email, password required'}), 400
    existing = query('users', params={'email': f'eq.{email}'})
    if existing and not isinstance(existing, dict) and len(existing) > 0:
        return jsonify({'error': 'Email already registered'}), 409
    salt, pw_hash = hash_password(password)
    role = 'admin' if email == ADMIN_EMAIL else 'user'
    tier = 'pro' if role in ('admin', 'super_admin') else 'free'
    now = datetime.now(timezone.utc).isoformat()
    result = query('users', method='POST', data={
        'name': name, 'email': email, 'password_hash': pw_hash, 'password_salt': salt,
        'role': role, 'email_verified': 1, 'telegram_notifications': 1,
        'leads_used': 0, 'subscription_tier': tier,
        'created_at': now, 'updated_at': now,
    })
    if isinstance(result, dict) and result.get('_error'):
        return jsonify({'error': result['_error']}), 500
    uid = result[0]['id']
    token = secrets.token_hex(32)
    query('sessions', method='POST', data={'user_id': uid, 'token': token, 'created_at': now})
    return jsonify({'token': token, 'user': {
        'id': uid, 'name': name, 'email': email,
        'role': role, 'subscription_tier': tier, 'email_verified': True,
    }}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'error': 'email and password required'}), 400
    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown')
    if not check_login_rate_limit(ip):
        return jsonify({'error': 'Too many login attempts. Try again later.'}), 429
    rows = query('users', params={'email': f'eq.{email}'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        record_login_attempt(ip)
        return jsonify({'error': 'Invalid email or password'}), 401
    user = rows[0]
    _, expected_hash = hash_password(password, user['password_salt'])
    if expected_hash != user['password_hash']:
        record_login_attempt(ip)
        return jsonify({'error': 'Invalid email or password'}), 401
    now = datetime.now(timezone.utc).isoformat()
    token = secrets.token_hex(32)
    query('sessions', method='POST', data={'user_id': user['id'], 'token': token, 'created_at': now})
    return jsonify({'token': token, 'user': {
        'id': user['id'], 'name': user['name'], 'email': user['email'],
        'role': user['role'], 'subscription_tier': user.get('subscription_tier', 'free'),
        'email_verified': bool(user.get('email_verified', 0)),
    }})

@app.route('/api/auth/me')
def me():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'id': user['id'], 'name': user['name'], 'email': user['email'],
        'role': user['role'], 'subscription_tier': user.get('subscription_tier', 'free'),
        'email_verified': bool(user.get('email_verified', 0)),
        'leads_used': user.get('leads_used', 0),
        'created_at': user.get('created_at', ''),
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        query('sessions', params={'token': f'eq.{auth[7:]}'}, method='DELETE')
    return jsonify({'ok': True})

@app.route('/api/auth/refresh', methods=['POST'])
def refresh():
    auth = request.headers.get('Authorization', '')
    new_token = secrets.token_hex(32)
    now = datetime.now(timezone.utc).isoformat()
    if auth.startswith('Bearer '):
        old = auth[7:]
        rows = query('sessions', params={'token': f'eq.{old}', 'limit': '1'})
        if rows and not isinstance(rows, dict) and len(rows) > 0:
            uid = rows[0]['user_id']
            query('sessions', params={'token': f'eq.{old}'}, method='DELETE')
            query('sessions', method='POST', data={'user_id': uid, 'token': new_token, 'created_at': now})
            return jsonify({'token': new_token})
    return jsonify({'error': 'No session to refresh'}), 400

@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json() or {}
    code = (data.get('code') or '').strip()
    if not code:
        return jsonify({'error': 'code required'}), 400
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Unauthorized'}), 401
    token = auth[7:]
    rows = query('sessions', params={'token': f'eq.{token}', 'limit': '1'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        return jsonify({'error': 'Unauthorized'}), 401
    uid = rows[0]['user_id']
    users = query('users', params={'id': f'eq.{uid}', 'verification_code': f'eq.{code}', 'limit': '1'})
    if not users or isinstance(users, dict) or len(users) == 0:
        return jsonify({'error': 'Invalid code'}), 400
    expires = users[0].get('verification_expires', '')
    if expires and float(expires) < time.time():
        return jsonify({'error': 'Code expired'}), 400
    query('users', params={'id': f'eq.{uid}'}, method='PATCH', data={
        'email_verified': 1, 'verification_code': None, 'verification_expires': None,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    })
    return jsonify({'ok': True, 'email_verified': True})

@app.route('/api/auth/resend-verification', methods=['POST'])
def resend_verification():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    expires = str(int(time.time()) + 600)
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data={
        'verification_code': code, 'verification_expires': expires,
    })
    send_email(user['email'], 'Verify your Scraven account',
               f'<h2>Your code: <b>{code}</b></h2><p>Expires in 10 minutes.</p>')
    return jsonify({'ok': True})

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = (data.get('email') or '').strip().lower()
    rows = query('users', params={'email': f'eq.{email}'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        return jsonify({'ok': True})
    user = rows[0]
    token = secrets.token_urlsafe(48)
    expires = str(int(time.time()) + 3600)
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data={
        'password_reset_token': token, 'password_reset_expires': expires,
    })
    host = (request.headers.get('Origin') or request.host_url).rstrip('/')
    send_email(email, 'Reset your Scraven password',
               f'<h2>Reset Link</h2><p><a href="{host}/reset-password.html?token={token}">Click here to reset</a></p><p>Expires in 1 hour.</p>')
    return jsonify({'ok': True})

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    token = (data.get('token') or '').strip()
    new_password = data.get('password') or ''
    if not token or not new_password:
        return jsonify({'error': 'token and password required'}), 400
    rows = query('users', params={'password_reset_token': f'eq.{token}', 'limit': '1'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        return jsonify({'error': 'Invalid token'}), 400
    user = rows[0]
    expires = user.get('password_reset_expires', '')
    if expires and float(expires) < time.time():
        return jsonify({'error': 'Token expired'}), 400
    salt, pw_hash = hash_password(new_password)
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data={
        'password_hash': pw_hash, 'password_salt': salt,
        'password_reset_token': None, 'password_reset_expires': None,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    })
    return jsonify({'ok': True})

@app.route('/api/auth/change-password', methods=['POST'])
def change_password():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    old_pw = data.get('old_password') or ''
    new_pw = data.get('new_password') or ''
    if not old_pw or not new_pw:
        return jsonify({'error': 'old_password and new_password required'}), 400
    _, expected = hash_password(old_pw, user['password_salt'])
    if expected != user['password_hash']:
        return jsonify({'error': 'Wrong current password'}), 401
    salt, pw_hash = hash_password(new_pw)
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data={
        'password_hash': pw_hash, 'password_salt': salt,
        'updated_at': datetime.now(timezone.utc).isoformat(),
    })
    return jsonify({'ok': True})

@app.route('/api/auth/profile', methods=['POST'])
def update_profile():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    update = {'updated_at': datetime.now(timezone.utc).isoformat()}
    if data.get('name'):
        update['name'] = data['name']
    if data.get('email'):
        update['email'] = data['email'].strip().lower()
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data=update)
    return jsonify({'ok': True})

@app.route('/api/auth/leads-remaining')
def leads_remaining():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    limit = get_lead_limit(user)
    used = user.get('leads_used', 0)
    return jsonify({
        'leads_used': used, 'leads_limit': limit,
        'leads_remaining': max(0, limit - used) if limit < 999999 else 999999,
        'tier': user.get('subscription_tier', 'free'),
    })

@app.route('/api/user/preferences', methods=['GET', 'POST'])
def user_preferences():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        return jsonify({
            'telegram_notifications': bool(user.get('telegram_notifications', 1)),
            'theme': 'dark',
        })
    data = request.get_json() or {}
    update = {}
    if 'telegram_notifications' in data:
        update['telegram_notifications'] = 1 if data['telegram_notifications'] else 0
    if update:
        query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data=update)
    return jsonify({'ok': True})

# ═════════════════════════════════════════════════════════════
# LEADS
# ═════════════════════════════════════════════════════════════
@app.route('/api/leads')
def list_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user.get('role') in ('admin', 'super_admin')
    status_filter = request.args.get('status')
    params = {'select': '*', 'order': 'created_at.desc', 'deleted_at': 'is.null'}
    if not is_admin:
        params['saved_by_user_id'] = f'eq.{user["id"]}'
    if status_filter:
        params['status'] = f'eq.{status_filter}'
    rows = query('leads', params=params)
    return jsonify([] if isinstance(rows, dict) else rows)

@app.route('/api/leads/trash')
def trash_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user.get('role') in ('admin', 'super_admin')
    params = {'select': '*', 'order': 'deleted_at.desc', 'deleted_at': 'not.is.null'}
    if not is_admin:
        params['saved_by_user_id'] = f'eq.{user["id"]}'
    rows = query('leads', params=params)
    return jsonify([] if isinstance(rows, dict) else rows)

@app.route('/api/trash/stats')
def trash_stats():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user.get('role') in ('admin', 'super_admin')
    params = {'select': 'id', 'deleted_at': 'not.is.null'}
    if not is_admin:
        params['saved_by_user_id'] = f'eq.{user["id"]}'
    rows = query('leads', params=params)
    return jsonify({'trashed_count': 0 if isinstance(rows, dict) else len(rows)})

@app.route('/api/lead', methods=['GET', 'POST'])
def lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        url_param = request.args.get('url', '')
        params = {'page_url': f'eq.{url_param}', 'deleted_at': 'is.null'}
        if user.get('role') not in ('admin', 'super_admin'):
            params['saved_by_user_id'] = f'eq.{user["id"]}'
        rows = query('leads', params=params)
        if rows and not isinstance(rows, dict) and len(rows) > 0:
            return jsonify(rows[0])
        return jsonify({'error': 'Lead not found'}), 404
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    if not user.get('email_verified'):
        return jsonify({'error': 'Please verify your email before saving leads', 'verify_required': True}), 403
    limit = get_lead_limit(user)
    used = user.get('leads_used', 0)
    if used >= limit:
        return jsonify({'error': 'Lead limit reached', 'limit_reached': True, 'tier': user.get('subscription_tier', 'free')}), 403
    existing = query('leads', params={
        'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}',
        'deleted_at': 'is.null',
    })
    if existing and not isinstance(existing, dict) and len(existing) > 0:
        return jsonify({'status': 'duplicate', 'message': 'Lead already exists, skipped'})
    now = datetime.now(timezone.utc).isoformat()
    is_admin_or_super = user.get('role') in ('admin', 'super_admin')
    if is_admin_or_super:
        notify = bool(data.get('notify_telegram')) if 'notify_telegram' in data else bool(user.get('telegram_notifications', 1))
    else:
        notify = False
    lead_data = {
        'date': data.get('date', now[:10]), 'platform': data.get('platform', ''),
        'business_name': data.get('business_name', ''), 'page_url': page_url,
        'category': data.get('category', ''), 'followers': data.get('followers', ''),
        'email': data.get('email', ''), 'phone': data.get('phone', ''),
        'website': data.get('website', ''), 'has_website': data.get('has_website', ''),
        'address': data.get('address', ''), 'last_post_date': data.get('last_post_date', ''),
        'qualification_score': str(data.get('qualification_score', '')),
        'status': data.get('status', 'new'), 'notes': data.get('notes', ''),
        'follow_up_date': data.get('follow_up_date', ''),
        'open_state': data.get('open_state', ''), 'hours_text': data.get('hours_text', ''),
        'saved_by_user_id': user['id'], 'saved_by_user_name': user.get('name', ''),
        'created_at': now,
    }
    result = query('leads', method='POST', data=lead_data)
    if isinstance(result, dict) and result.get('_error'):
        return jsonify({'error': result['_error']}), 500
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data={'leads_used': used + 1})
    if notify and result and not isinstance(result, dict):
        send_telegram(f'🦅 New Lead: <b>{result[0]["business_name"]}</b>\n{result[0]["page_url"]}')
    remaining = max(0, limit - used - 1) if limit < 999999 else 999999
    return jsonify({'status': 'saved', 'message': 'Lead saved', 'leads_remaining': remaining}), 201

@app.route('/api/lead/status', methods=['POST'])
def update_lead_status():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    new_status = (data.get('status') or '').strip().lower()
    follow_up = (data.get('follow_up_date') or '').strip()
    if not page_url or not new_status:
        return jsonify({'error': 'page_url and status required'}), 400
    update = {'status': new_status}
    if follow_up:
        update['follow_up_date'] = follow_up
    query('leads', params={'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}'}, method='PATCH', data=update)
    if new_status == 'qualified':
        existing_lead = query('leads', params={'page_url': f'eq.{page_url}', 'limit': '1'})
        if existing_lead and not isinstance(existing_lead, dict) and len(existing_lead) > 0:
            lead = existing_lead[0]
            query('qualified_leads', method='POST', data={
                'lead_id': lead['id'], 'page_url': lead['page_url'],
                'business_name': lead['business_name'], 'phone': lead.get('phone', ''),
                'email': lead.get('email', ''), 'category': lead.get('category', ''),
                'qualification_score': str(lead.get('qualification_score', '')),
                'qualified_at': datetime.now(timezone.utc).isoformat(),
                'qualified_by': user['id'], 'qualified_by_name': user.get('name', ''),
                'saved_by_user_id': lead.get('saved_by_user_id', 0),
                'notes': lead.get('notes', ''),
            })
    return jsonify({'status': 'updated'})

@app.route('/api/lead/delete', methods=['POST'])
@app.route('/api/lead/trash', methods=['POST'])
def delete_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    now = datetime.now(timezone.utc).isoformat()
    query('leads', params={
        'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}',
        'deleted_at': 'is.null',
    }, method='PATCH', data={'deleted_at': now, 'status': 'trashed'})
    return jsonify({'status': 'deleted'})

@app.route('/api/lead/restore', methods=['POST'])
def restore_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    query('leads', params={
        'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}',
    }, method='PATCH', data={'deleted_at': None, 'status': 'new'})
    return jsonify({'status': 'restored'})

@app.route('/api/lead/purge', methods=['POST'])
def purge_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    query('leads', params={
        'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}',
        'deleted_at': 'not.is.null',
    }, method='DELETE')
    return jsonify({'status': 'purged'})

@app.route('/api/lead/bulk-trash', methods=['POST'])
@app.route('/api/lead/bulk-delete', methods=['POST'])
def bulk_trash():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    urls = (request.get_json() or {}).get('urls') or []
    now = datetime.now(timezone.utc).isoformat()
    moved = 0
    failed = []
    for url in urls:
        result = query('leads', params={
            'page_url': f'eq.{url}', 'saved_by_user_id': f'eq.{user["id"]}',
            'deleted_at': 'is.null',
        }, method='PATCH', data={'deleted_at': now, 'status': 'trashed'})
        if not isinstance(result, dict):
            moved += 1
        else:
            failed.append(url)
    return jsonify({'moved_count': moved, 'failed': failed, 'count': moved})

@app.route('/api/lead/bulk-restore', methods=['POST'])
def bulk_restore():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    urls = (request.get_json() or {}).get('urls') or []
    for url in urls:
        query('leads', params={
            'page_url': f'eq.{url}', 'saved_by_user_id': f'eq.{user["id"]}',
        }, method='PATCH', data={'deleted_at': None, 'status': 'new'})
    return jsonify({'status': 'restored', 'count': len(urls)})

@app.route('/api/lead/bulk-purge', methods=['POST'])
def bulk_purge():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    urls = (request.get_json() or {}).get('urls') or []
    for url in urls:
        query('leads', params={
            'page_url': f'eq.{url}', 'saved_by_user_id': f'eq.{user["id"]}',
            'deleted_at': 'not.is.null',
        }, method='DELETE')
    return jsonify({'status': 'purged', 'count': len(urls)})

@app.route('/api/lead/action', methods=['POST'])
def lead_action():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or {}
    action = data.get('action')
    page_url = (data.get('page_url') or '').strip()
    if not action or not page_url:
        return jsonify({'error': 'action and page_url required'}), 400
    update = {}
    if action == 'qualified':
        update = {'status': 'qualified', 'qualification_score': '90'}
    elif action == 'contacted':
        update = {'status': 'contacted'}
    elif action == 'reset':
        update = {'status': 'new', 'qualification_score': ''}
    elif action == 'disqualify':
        query('leads', params={'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}'}, method='DELETE')
        return jsonify({'status': 'deleted'})
    else:
        return jsonify({'error': 'Unknown action'}), 400
    if update:
        query('leads', params={'page_url': f'eq.{page_url}', 'saved_by_user_id': f'eq.{user["id"]}'}, method='PATCH', data=update)
    return jsonify({'status': 'ok', 'action': action})

# ═════════════════════════════════════════════════════════════
# FUNNEL & QUALIFIED
# ═════════════════════════════════════════════════════════════
@app.route('/api/funnel')
def funnel_stats():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user.get('role') in ('admin', 'super_admin')
    params = {'select': 'status', 'deleted_at': 'is.null'}
    if not is_admin:
        params['saved_by_user_id'] = f'eq.{user["id"]}'
    rows = query('leads', params=params)
    if isinstance(rows, dict):
        return jsonify({'total': 0, 'breakdown': {}})
    total = len(rows)
    breakdown = {}
    for r in rows:
        s = r.get('status', 'unknown') or 'unknown'
        breakdown[s] = breakdown.get(s, 0) + 1
    return jsonify({'total': total, 'breakdown': breakdown})

@app.route('/api/leads/qualified')
def qualified_leads():
    rows = query('qualified_leads', params={'select': '*', 'order': 'qualified_at.desc'})
    return jsonify([] if isinstance(rows, dict) else rows)

@app.route('/api/qualified/daily-files')
def qualified_daily_files():
    rows = query('qualified_leads', params={'select': 'qualified_at'})
    if isinstance(rows, dict):
        return jsonify([])
    dates = sorted(set(r['qualified_at'][:10] for r in rows), reverse=True)
    return jsonify([{'date': d, 'filename': f'{d}.csv'} for d in dates])

@app.route('/api/qualified/daily')
def qualified_daily():
    date = request.args.get('date', '')
    if not date:
        return jsonify({'error': 'date required'}), 400
    rows = query('qualified_leads', params={
        'select': '*', 'qualified_at': f'like.{date}%', 'order': 'qualified_at.desc',
    })
    return jsonify([] if isinstance(rows, dict) else rows)

@app.route('/api/last-lead')
def last_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    rows = query('leads', params={
        'select': 'page_url', 'saved_by_user_id': f'eq.{user["id"]}',
        'deleted_at': 'is.null', 'order': 'created_at.desc', 'limit': '1',
    })
    if rows and not isinstance(rows, dict) and len(rows) > 0:
        return jsonify({'page_url': rows[0]['page_url']})
    return jsonify({'error': 'No recent lead'}), 404

# ═════════════════════════════════════════════════════════════
# EXTRACTION (Apify only - Playwright won't run on Vercel)
# ═════════════════════════════════════════════════════════════
@app.route('/api/extract-facebook', methods=['POST'])
def extract_facebook():
    """Manual entry fallback - real extraction needs a worker."""
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'url required'}), 400
    return jsonify({
        'url': url, 'business_name': '', 'category': '', 'followers': '',
        'email': '', 'phone': '', 'website': '', 'has_website': '',
        'address': '', 'last_post_date': '', 'qualification_score': 0,
        'note': 'Playwright extraction is disabled on serverless. Use manual entry or Apify.',
    })

@app.route('/api/extract-facebook/apify', methods=['POST'])
def extract_facebook_apify():
    """Apify-based extraction - works on Vercel."""
    if not APIFY_TOKEN:
        return jsonify({'error': 'APIFY_TOKEN not configured'}), 500
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    if not url:
        return jsonify({'error': 'url required'}), 400
    try:
        # Start Apify run
        run_resp = requests.post(
            f'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs?token={APIFY_TOKEN}',
            json={'startUrls': [{'url': url}], 'maxPosts': 5},
            timeout=20,
        )
        if run_resp.status_code >= 300:
            return jsonify({'error': f'Apify start failed: {run_resp.text[:200]}'}), 500
        run_id = run_resp.json().get('data', {}).get('id')
        if not run_id:
            return jsonify({'error': 'Apify no run ID'}), 500
        # Poll for completion (up to 50s)
        for _ in range(10):
            time.sleep(5)
            status_resp = requests.get(
                f'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs/{run_id}?token={APIFY_TOKEN}',
                timeout=15,
            )
            status = status_resp.json().get('data', {}).get('status')
            if status == 'SUCCEEDED':
                dataset_id = status_resp.json().get('data', {}).get('defaultDatasetId')
                items = requests.get(f'https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}', timeout=15).json()
                if not items:
                    return jsonify({'error': 'No results from Apify'}), 404
                page = items[0]
                return jsonify({
                    'url': url,
                    'business_name': page.get('pageName', page.get('name', '')),
                    'category': page.get('categories', ''),
                    'followers': str(page.get('likes', page.get('followers', ''))),
                    'email': page.get('email', ''),
                    'phone': page.get('phone', ''),
                    'website': page.get('website', ''),
                    'has_website': 'yes' if page.get('website') else 'no',
                    'address': page.get('address', ''),
                    'last_post_date': page.get('lastPostDate', ''),
                    'qualification_score': 5,
                })
            elif status in ('FAILED', 'ABORTED', 'TIMED-OUT'):
                return jsonify({'error': f'Apify run {status}'}), 500
        return jsonify({'error': 'Apify timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-facebook/manual', methods=['POST'])
def extract_facebook_manual():
    data = request.get_json() or {}
    url = (data.get('url') or '').strip()
    if not url or 'facebook.com' not in url:
        return jsonify({'error': 'valid Facebook URL required'}), 400
    return jsonify({
        'url': url, 'business_name': data.get('business_name', ''),
        'phone': data.get('phone', ''), 'email': data.get('email', ''),
        'category': data.get('category', ''), 'followers': data.get('followers', ''),
        'website': data.get('website', ''), 'address': data.get('address', ''),
        'qualification_score': data.get('qualification_score', 0),
    })

@app.route('/api/extract-instagram', methods=['POST'])
def extract_instagram():
    return jsonify({'error': 'Instagram extraction disabled on serverless. Use manual entry.'}), 501

@app.route('/api/bookmarklet-extract')
def bookmarklet_extract():
    """Return JS bookmarklet that scrapes current FB page."""
    js = '''javascript:(function(){
        var d=document;
        var url=location.href;
        var name=d.querySelector('meta[property="og:title"]')?.content||d.title||'';
        var desc=d.querySelector('meta[property="og:description"]')?.content||'';
        var data={url:url,business_name:name,description:desc};
        window.location='EXTRACT_URL?data='+encodeURIComponent(JSON.stringify(data));
    })();'''
    extract_url = request.host_url.rstrip('/') + '/extract.html'
    return js.replace('EXTRACT_URL', extract_url), 200, {'Content-Type': 'application/javascript'}

# ═════════════════════════════════════════════════════════════
# F-COMMERCE
# ═════════════════════════════════════════════════════════════
@app.route('/api/fcommerce/leads')
def fcommerce_leads():
    priority = request.args.get('priority')
    source = request.args.get('source')
    category = request.args.get('category')
    params = {'select': '*', 'order': 'created_at.desc'}
    if priority: params['priority'] = f'eq.{priority}'
    if source: params['source'] = f'eq.{source}'
    if category: params['category'] = f'ilike.%25{category}%25'
    rows = query('fcommerce_leads', params=params)
    return jsonify([] if isinstance(rows, dict) else rows)

@app.route('/api/fcommerce/stats')
def fcommerce_stats():
    rows = query('fcommerce_leads', params={'select': 'priority,source,product_categories,status'})
    if isinstance(rows, dict):
        return jsonify({'by_priority': {}, 'by_source': {}, 'by_status': {}, 'total': 0})
    by_priority, by_source, by_status = {}, {}, {}
    for r in rows:
        by_priority[r.get('priority', 'unknown')] = by_priority.get(r.get('priority', 'unknown'), 0) + 1
        by_source[r.get('source', 'unknown')] = by_source.get(r.get('source', 'unknown'), 0) + 1
        by_status[r.get('status', 'unknown')] = by_status.get(r.get('status', 'unknown'), 0) + 1
    return jsonify({'by_priority': by_priority, 'by_source': by_source, 'by_status': by_status, 'total': len(rows)})

@app.route('/api/fcommerce/export')
def fcommerce_export():
    rows = query('fcommerce_leads', params={'select': '*', 'order': 'created_at.desc'})
    if isinstance(rows, dict):
        rows = []
    import csv, io
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    from flask import Response
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=fcommerce_leads_export.csv'})

@app.route('/api/fcommerce/lead', methods=['POST'])
def fcommerce_save():
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    score = int(data.get('qualification_score', 0))
    priority = 'HIGH' if score >= 9 else ('MEDIUM' if score >= 6 else 'LOW')
    flags = []
    if not data.get('has_website'): flags.append('no_website')
    if data.get('phone'): flags.append('has_phone')
    if data.get('email'): flags.append('has_email')
    if data.get('order_method') == 'inbox': flags.append('inbox_signal')
    now = datetime.now(timezone.utc).isoformat()
    lead_data = {
        'date': data.get('date', now[:10]), 'source': data.get('source', 'apify'),
        'business_name': data.get('business_name', ''), 'page_url': page_url,
        'followers_int': str(data.get('followers_int', '')), 'has_website': data.get('has_website', ''),
        'order_method': data.get('order_method', ''), 'last_post_date': data.get('last_post_date', ''),
        'product_categories': data.get('product_categories', ''),
        'discovery_source': data.get('discovery_source', ''),
        'qualification_score': str(score), 'priority': priority,
        'opportunity_flags': ','.join(flags),
        'email': data.get('email', ''), 'phone': data.get('phone', ''),
        'address': data.get('address', ''), 'status': data.get('status', 'new'),
        'notes': data.get('notes', ''), 'created_at': now,
    }
    if score < 6:
        return jsonify({'error': 'Score too low (<6) - lead rejected', 'priority': 'LOW'}), 400
    result = query('fcommerce_leads', method='POST', data=lead_data)
    if isinstance(result, dict) and result.get('_error'):
        return jsonify({'error': result['_error']}), 500
    if priority == 'HIGH':
        send_telegram(f'🔥 HIGH Priority F-Commerce Lead: {data.get("business_name")}\n{page_url}')
    return jsonify({'status': 'saved', 'priority': priority}), 201

@app.route('/api/fcommerce/lead/delete', methods=['POST'])
def fcommerce_delete():
    data = request.get_json() or {}
    page_url = (data.get('page_url') or '').strip()
    if not page_url:
        return jsonify({'error': 'page_url required'}), 400
    query('fcommerce_leads', params={'page_url': f'eq.{page_url}'}, method='DELETE')
    return jsonify({'status': 'deleted'})

# ═════════════════════════════════════════════════════════════
# LINKEDIN
# ═════════════════════════════════════════════════════════════
@app.route('/api/linkedin/save', methods=['POST'])
def linkedin_save():
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name required'}), 400
    now = datetime.now(timezone.utc).isoformat()
    lead_data = {
        'date': now[:10], 'name': name, 'headline': data.get('headline', ''),
        'company': data.get('company', ''), 'location': data.get('location', ''),
        'url': data.get('url', ''), 'kb_score': str(data.get('kb_score', 0)),
        'kb_category': data.get('kb_category', ''),
        'matched_products': data.get('matched_products', ''),
        'status': 'new', 'source': data.get('source', 'linkedin'),
    }
    result = query('linkedin_leads', method='POST', data=lead_data)
    if isinstance(result, dict) and result.get('_error'):
        return jsonify({'error': result['_error']}), 500
    if float(lead_data['kb_score']) >= 8.0:
        send_telegram(f'💼 Hot LinkedIn Lead: <b>{name}</b> ({lead_data["headline"]})\n{lead_data["url"]}')
    return jsonify({'status': 'saved'}), 201

# ═════════════════════════════════════════════════════════════
# ADMIN
# ═════════════════════════════════════════════════════════════
def require_admin():
    user = require_auth()
    if not user or user.get('role') not in ('admin', 'super_admin'):
        return None
    return user

@app.route('/api/admin/users')
def admin_users():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    rows = query('users', params={'select': 'id,name,email,role,subscription_tier,created_at', 'order': 'created_at.desc'})
    return jsonify([] if isinstance(rows, dict) else rows)

@app.route('/api/admin/stats')
def admin_stats():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    users = query('users', params={'select': 'id,role'})
    leads = query('leads', params={'select': 'status,created_at', 'deleted_at': 'is.null'})
    role_counts = {}
    if isinstance(users, list):
        for u in users:
            r = u.get('role', 'user')
            role_counts[r] = role_counts.get(r, 0) + 1
    status_counts = {}
    if isinstance(leads, list):
        for l in leads:
            s = l.get('status', 'new')
            status_counts[s] = status_counts.get(s, 0) + 1
    now = datetime.now(timezone.utc)
    this_month = f'{now.year}-{now.month:02d}'
    month_count = sum(1 for l in (leads if isinstance(leads, list) else []) if l.get('created_at', '').startswith(this_month))
    return jsonify({
        'total_users': len(users) if isinstance(users, list) else 0,
        'total_leads': len(leads) if isinstance(leads, list) else 0,
        'role_counts': role_counts,
        'statuses': status_counts,
        'this_month': month_count,
        'month_label': now.strftime('%B %Y'),
    })

@app.route('/api/admin/users/delete', methods=['POST'])
def admin_user_delete():
    if not require_admin():
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json() or {}
    uid = data.get('user_id')
    if not uid:
        return jsonify({'error': 'user_id required'}), 400
    target = query('users', params={'id': f'eq.{uid}', 'limit': '1'})
    if not target or isinstance(target, dict):
        return jsonify({'error': 'User not found'}), 404
    if target[0].get('role') in ('admin', 'super_admin'):
        return jsonify({'error': 'Cannot delete admin users'}), 403
    query('sessions', params={'user_id': f'eq.{uid}'}, method='DELETE')
    query('leads', params={'saved_by_user_id': f'eq.{uid}'}, method='DELETE')
    query('users', params={'id': f'eq.{uid}'}, method='DELETE')
    return jsonify({'status': 'deleted'})

@app.route('/api/admin/users/role', methods=['POST'])
def admin_user_role():
    user = require_admin()
    if not user:
        return jsonify({'error': 'Admin access required'}), 403
    data = request.get_json() or {}
    uid = data.get('user_id')
    new_role = data.get('role')
    if not uid or not new_role:
        return jsonify({'error': 'user_id and role required'}), 400
    if new_role not in ('user', 'pro', 'admin'):
        return jsonify({'error': 'Invalid role'}), 400
    if int(uid) == user['id']:
        return jsonify({'error': 'Cannot change your own role'}), 400
    tier = 'pro' if new_role in ('pro', 'admin') else 'free'
    query('users', params={'id': f'eq.{uid}'}, method='PATCH', data={'role': new_role, 'subscription_tier': tier})
    return jsonify({'status': 'updated'})

# ═════════════════════════════════════════════════════════════
# OUTREACH (simplified - demo gen needs a worker)
# ═════════════════════════════════════════════════════════════
@app.route('/api/outreach/status')
def outreach_status():
    return jsonify({
        'netlify_token_configured': bool(os.environ.get('NETLIFY_TOKEN')),
        'telegram_configured': bool(TELEGRAM_TOKEN),
        'note': 'Outreach demo generation runs on a separate worker. Use build_demo.py CLI locally.',
    })

@app.route('/api/outreach', methods=['POST'])
def outreach():
    data = request.get_json() or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text required'}), 400
    return jsonify({
        'status': 'pending',
        'note': 'Outreach demo generation requires a worker. Run build_demo.py CLI.',
        'parsed': text[:200],
    }), 202

# ═════════════════════════════════════════════════════════════
# HTML SERVING (read at module load, embedded in function)
# ═════════════════════════════════════════════════════════════
HTML_DIR_CANDIDATES = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'public'),
    os.path.join(os.getcwd(), 'public'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public'),
]

# Load HTML files at module load (bundled with Vercel Python function)
HTML_CACHE = {}
for _candidate in HTML_DIR_CANDIDATES:
    if os.path.isdir(_candidate):
        for _root, _dirs, _files in os.walk(_candidate):
            for _fname in _files:
                _full = os.path.join(_root, _fname)
                _rel = os.path.relpath(_full, _candidate)
                try:
                    with open(_full, 'rb') as _f:
                        HTML_CACHE[_rel] = _f.read()
                except:
                    pass
        break

print(f'Loaded {len(HTML_CACHE)} static files from {_candidate}', flush=True)

def serve_html(filename):
    """Serve HTML from preloaded cache."""
    if filename in HTML_CACHE:
        content_type = 'text/html; charset=utf-8'
        if filename.endswith('.js'): content_type = 'application/javascript'
        elif filename.endswith('.css'): content_type = 'text/css'
        elif filename.endswith('.json'): content_type = 'application/json'
        elif filename.endswith('.svg'): content_type = 'image/svg+xml'
        elif filename.endswith('.png'): content_type = 'image/png'
        elif filename.endswith('.jpg'): content_type = 'image/jpeg'
        elif filename.endswith('.ico'): content_type = 'image/x-icon'
        return HTML_CACHE[filename], 200, {'Content-Type': content_type, 'Cache-Control': 'public, max-age=3600'}
    return '<h1>Not Found</h1>', 404, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/')
def root_index():
    return serve_html('leads.html')

@app.route('/<path:filename>')
def static_html(filename):
    return serve_html(filename)