import os, hashlib, secrets
from datetime import datetime, timezone
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://lkmgyvkqbdftpgyvpcrd.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxrbWd5dmtxYmRmdHBneXZwY3JkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzE3MDUzOCwiZXhwIjoyMDk4NzQ2NTM4fQ.nWfWIAgs-MgVAkAx67Spfj4QEr0KFH1D4aQTAHLTBqQ')
REST = f'{SUPABASE_URL}/rest/v1'
HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
}

def query(table, params=None, method='GET', data=None):
    url = f'{REST}/{table}'
    h = HEADERS.copy()
    if method == 'GET':
        r = requests.get(url, headers=h, params=params)
    elif method == 'POST':
        r = requests.post(url, headers=h, json=data, params=params)
    elif method == 'PATCH':
        r = requests.patch(url, headers=h, json=data, params=params)
    elif method == 'DELETE':
        r = requests.delete(url, headers=h, params=params)
    try:
        return r.json() if r.status_code < 300 else {'_error': r.text, '_status': r.status_code}
    except:
        return {'_error': r.text, '_status': r.status_code}

@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'error': str(e), 'type': type(e).__name__}), 500

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
    rows = query('sessions', params={'select': '*,users(*)', 'token': f'eq.{token}'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        return None
    s = rows[0]
    if 'users' not in s:
        return None
    u = s['users']
    u['id'] = u.get('id')
    return u



# ── Health ──
@app.route('/api/health')
def health():
    try:
        rows = query('users', params={'select': 'count', 'limit': '1'})
        if isinstance(rows, dict) and rows.get('_error'):
            return jsonify({'status': 'error', 'db': rows['_error']}), 500
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
    existing = query('users', params={'email': f'eq.{email}'})
    if existing and not isinstance(existing, dict) and len(existing) > 0:
        return jsonify({'error': 'Email already registered'}), 409
    salt, pw_hash = hash_password(password)
    now = datetime.now(timezone.utc).isoformat()
    result = query('users', method='POST', data={
        'name': name, 'email': email, 'password_hash': pw_hash,
        'password_salt': salt, 'created_at': now, 'updated_at': now,
    })
    if isinstance(result, dict) and result.get('_error'):
        return jsonify({'error': result['_error']}), 500
    uid = result[0]['id'] if isinstance(result, list) and len(result) > 0 else None
    if not uid:
        return jsonify({'error': 'Failed to create user'}), 500
    token = secrets.token_hex(32)
    query('sessions', method='POST', data={'user_id': uid, 'token': token, 'created_at': now})
    return jsonify({'token': token, 'user': {
        'id': uid, 'name': name, 'email': email,
        'role': 'user', 'subscription_tier': 'free'
    }}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'email and password required'}), 400
    email = data['email'].strip().lower()
    password = data['password']
    rows = query('users', params={'email': f'eq.{email}'})
    if not rows or isinstance(rows, dict) or len(rows) == 0:
        return jsonify({'error': 'Invalid email or password'}), 401
    user = rows[0]
    _, expected_hash = hash_password(password, user['password_salt'])
    if expected_hash != user['password_hash']:
        return jsonify({'error': 'Invalid email or password'}), 401
    now = datetime.now(timezone.utc).isoformat()
    token = secrets.token_hex(32)
    query('sessions', method='POST', data={'user_id': user['id'], 'token': token, 'created_at': now})
    return jsonify({'token': token, 'user': {
        'id': user['id'], 'name': user['name'], 'email': user['email'],
        'role': user['role'], 'subscription_tier': user['subscription_tier']
    }})

@app.route('/api/auth/me')
def me():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({
        'id': user['id'], 'name': user['name'], 'email': user['email'],
        'role': user['role'], 'subscription_tier': user.get('subscription_tier', 'free'),
        'email_verified': user.get('email_verified', 1)
    })

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        query('sessions', params={'token': f'eq.{auth[7:]}'}, method='DELETE')
    return jsonify({'ok': True})

@app.route('/api/auth/leads-remaining')
def leads_remaining():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    limit = 999999 if user.get('subscription_tier') in ('pro', 'admin') else 20
    return jsonify({'leads_used': user.get('leads_used', 0), 'leads_limit': limit})

# ── Leads ──
@app.route('/api/leads')
def list_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    is_admin = user.get('role') in ('admin', 'super_admin')
    params = {'select': '*', 'order': 'created_at.desc', 'deleted_at': 'is.null'}
    if not is_admin:
        params['saved_by_user_id'] = f'eq.{user["id"]}'
    status_filter = request.args.get('status')
    if status_filter:
        params['status'] = f'eq.{status_filter}'
    rows = query('leads', params=params)
    if isinstance(rows, dict):
        return jsonify([])
    return jsonify(rows)

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
    if isinstance(rows, dict):
        return jsonify([])
    return jsonify(rows)

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
    count = 0 if isinstance(rows, dict) else len(rows)
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
    existing = query('leads', params={
        'page_url': f'eq.{page_url}',
        'saved_by_user_id': f'eq.{user["id"]}',
        'deleted_at': 'is.null',
    })
    if existing and not isinstance(existing, dict) and len(existing) > 0:
        return jsonify({'status': 'duplicate', 'message': 'Lead already exists, skipped'})
    limit = 999999 if user.get('subscription_tier') in ('pro', 'admin') else 20
    if (user.get('leads_used') or 0) >= limit:
        return jsonify({'error': 'Lead limit reached', 'limit_reached': True}), 403
    lead_data = {
        'date': data.get('date', now[:10]), 'platform': data.get('platform', ''),
        'business_name': data.get('business_name', ''), 'page_url': page_url,
        'category': data.get('category', ''), 'followers': data.get('followers', ''),
        'email': data.get('email', ''), 'phone': data.get('phone', ''),
        'website': data.get('website', ''), 'has_website': data.get('has_website', ''),
        'address': data.get('address', ''), 'last_post_date': data.get('last_post_date', ''),
        'qualification_score': data.get('qualification_score', ''),
        'status': data.get('status', 'new'), 'notes': data.get('notes', ''),
        'follow_up_date': data.get('follow_up_date', ''),
        'open_state': data.get('open_state', ''), 'hours_text': data.get('hours_text', ''),
        'saved_by_user_id': user['id'], 'saved_by_user_name': user.get('name', ''),
        'created_at': now,
    }
    result = query('leads', method='POST', data=lead_data)
    if isinstance(result, dict) and result.get('_error'):
        return jsonify({'error': result['_error']}), 500
    query('users', params={'id': f'eq.{user["id"]}'}, method='PATCH', data={'leads_used': (user.get('leads_used', 0) + 1)})
    remaining = limit - (user.get('leads_used', 0) + 1)
    return jsonify({'status': 'saved', 'message': 'Lead saved', 'leads_remaining': max(0, remaining)}), 201

@app.route('/api/lead', methods=['GET'])
def get_lead():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    url_param = request.args.get('url', '')
    params = {'page_url': f'eq.{url_param}', 'deleted_at': 'is.null'}
    if user.get('role') not in ('admin', 'super_admin'):
        params['saved_by_user_id'] = f'eq.{user["id"]}'
    rows = query('leads', params=params)
    if rows and not isinstance(rows, dict) and len(rows) > 0:
        return jsonify(rows[0])
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
    update = {'status': new_status}
    if follow_up:
        update['follow_up_date'] = follow_up
    query('leads', params={
        'page_url': f'eq.{page_url}',
        'saved_by_user_id': f'eq.{user["id"]}',
    }, method='PATCH', data=update)
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
    query('leads', params={
        'page_url': f'eq.{page_url}',
        'saved_by_user_id': f'eq.{user["id"]}',
        'deleted_at': 'is.null',
    }, method='PATCH', data={'deleted_at': now})
    return jsonify({'status': 'deleted'})

@app.route('/api/lead/bulk-trash', methods=['POST'])
def bulk_trash():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    urls = request.get_json().get('urls', [])
    now = datetime.now(timezone.utc).isoformat()
    for url in urls:
        query('leads', params={
            'page_url': f'eq.{url}',
            'saved_by_user_id': f'eq.{user["id"]}',
            'deleted_at': 'is.null',
        }, method='PATCH', data={'deleted_at': now})
    return jsonify({'status': 'trashed', 'count': len(urls)})

@app.route('/api/lead/bulk-restore', methods=['POST'])
def bulk_restore():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    urls = request.get_json().get('urls', [])
    for url in urls:
        query('leads', params={
            'page_url': f'eq.{url}',
            'saved_by_user_id': f'eq.{user["id"]}',
        }, method='PATCH', data={'deleted_at': None})
    return jsonify({'status': 'restored', 'count': len(urls)})

@app.route('/api/lead/bulk-purge', methods=['POST'])
def bulk_purge():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    urls = request.get_json().get('urls', [])
    for url in urls:
        query('leads', params={
            'page_url': f'eq.{url}',
            'saved_by_user_id': f'eq.{user["id"]}',
            'deleted_at': 'not.is.null',
        }, method='DELETE')
    return jsonify({'status': 'purged', 'count': len(urls)})

@app.route('/api/lead/action', methods=['POST'])
def lead_action():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    action = data.get('action')
    page_url = (data.get('page_url') or '').strip()
    if not action or not page_url:
        return jsonify({'error': 'action and page_url required'}), 400
    status_map = {'qualified': 'qualified', 'contacted': 'contacted', 'reset': 'new'}
    if action not in status_map:
        return jsonify({'error': 'Unknown action'}), 400
    query('leads', params={
        'page_url': f'eq.{page_url}',
        'saved_by_user_id': f'eq.{user["id"]}',
    }, method='PATCH', data={'status': status_map[action], 'qualification_score': '90' if action == 'qualified' else ''})
    return jsonify({'status': 'ok', 'action': action})

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
        s = r.get('status', 'unknown')
        breakdown[s] = breakdown.get(s, 0) + 1
    return jsonify({'total': total, 'breakdown': breakdown})

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

@app.route('/api/leads/qualified')
def qualified_leads():
    user = require_auth()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    rows = query('leads', params={
        'select': '*', 'status': 'eq.qualified', 'deleted_at': 'is.null',
        'order': 'created_at.desc',
    })
    if isinstance(rows, dict):
        return jsonify([])
    return jsonify(rows)
