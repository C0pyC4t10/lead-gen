"""Migrate local SQLite + CSV data to Supabase."""
import csv, json, os, sys, sqlite3
import requests
from datetime import datetime, timezone

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://lkmgyvkqbdftpgyvpcrd.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxrbWd5dmtxYmRmdHBneXZwY3JkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzE3MDUzOCwiZXhwIjoyMDk4NzQ2NTM4fQ.nWfWIAgs-MgVAkAx67Spfj4QEr0KFH1D4aQTAHLTBqQ')
HEADERS = {
    'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json', 'Prefer': 'return=representation',
}

BASE = os.path.dirname(os.path.abspath(__file__))
AUTH_DB = os.path.join(BASE, 'auth.db')
CSV_PATH = os.path.join(BASE, 'collected_leads', 'leads.csv')
CSV_COLUMNS = [
    'date', 'platform', 'business_name', 'page_url', 'category', 'followers',
    'email', 'phone', 'website', 'has_website', 'address', 'last_post_date',
    'qualification_score', 'status', 'notes', 'follow_up_date', 'open_state', 'hours_text',
    'deleted_at', 'saved_by_user_id', 'saved_by_user_name',
]

def post(table, data):
    r = requests.post(f'{SUPABASE_URL}/rest/v1/{table}', headers=HEADERS, json=data)
    if r.status_code >= 300:
        print(f'  ERROR {table}: {r.status_code} {r.text[:150]}')
        return None
    return r.json()

# ── Migrate users ──
print('=== Migrating users ===')
conn = sqlite3.connect(AUTH_DB)
c = conn.cursor()
c.execute('SELECT * FROM users')
users = c.fetchall()
cols = [d[0] for d in c.description]

user_id_map = {}
for row in users:
    u = dict(zip(cols, row))
    u['email_verified'] = 1
    existing = requests.get(f'{SUPABASE_URL}/rest/v1/users', headers=HEADERS,
                            params={'email': f'eq.{u["email"]}'}).json()
    if existing and not isinstance(existing, dict) and len(existing) > 0:
        print(f'  Skipping {u["email"]} (already exists)')
        user_id_map[u['id']] = existing[0]['id']
        continue
    result = post('users', {
        'id': u['id'], 'name': u['name'], 'email': u['email'],
        'password_hash': u['password_hash'], 'password_salt': u['password_salt'],
        'role': u['role'], 'email_verified': 1,
        'leads_used': u.get('leads_used', 0), 'subscription_tier': u.get('subscription_tier', 'free'),
        'created_at': u['created_at'], 'updated_at': u['updated_at'],
    })
    if result:
        user_id_map[u['id']] = u['id']
        print(f'  Migrated: {u["name"]} ({u["email"]})')

# ── Migrate sessions ──
print('\n=== Migrating sessions ===')
c.execute('SELECT * FROM sessions')
for row in c.fetchall():
    s = dict(zip([d[0] for d in c.description], row))
    uid = user_id_map.get(s['user_id'])
    if not uid:
        continue
    post('sessions', {
        'user_id': uid, 'token': s['token'], 'created_at': s['created_at'],
    })
print(f'  Sessions migrated')

conn.close()

# ── Migrate leads ──
print('\n=== Migrating leads ===')
if not os.path.exists(CSV_PATH):
    print('  No CSV found')
else:
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        leads = list(reader)
    print(f'  Found {len(leads)} leads in CSV')

    batch = []
    for i, lead in enumerate(leads):
        uid = user_id_map.get(int(lead.get('saved_by_user_id', 0) or 0)) or 0
        batch.append({
            'date': lead.get('date', '')[:10],
            'platform': lead.get('platform', ''),
            'business_name': lead.get('business_name', ''),
            'page_url': lead.get('page_url', ''),
            'category': lead.get('category', ''),
            'followers': lead.get('followers', ''),
            'email': lead.get('email', ''),
            'phone': lead.get('phone', ''),
            'website': lead.get('website', ''),
            'has_website': lead.get('has_website', ''),
            'address': lead.get('address', ''),
            'last_post_date': lead.get('last_post_date', ''),
            'qualification_score': lead.get('qualification_score', ''),
            'status': lead.get('status', 'new'),
            'notes': lead.get('notes', ''),
            'follow_up_date': lead.get('follow_up_date', ''),
            'open_state': lead.get('open_state', ''),
            'hours_text': lead.get('hours_text', ''),
            'deleted_at': lead.get('deleted_at', '') or None,
            'saved_by_user_id': uid,
            'saved_by_user_name': lead.get('saved_by_user_name', ''),
            'created_at': datetime.now(timezone.utc).isoformat(),
        })
        if len(batch) >= 100:
            r = requests.post(f'{SUPABASE_URL}/rest/v1/leads', headers=HEADERS, json=batch)
            print(f'  Inserted {len(batch)} leads (status {r.status_code})')
            batch = []

    if batch:
        r = requests.post(f'{SUPABASE_URL}/rest/v1/leads', headers=HEADERS, json=batch)
        print(f'  Inserted final {len(batch)} leads (status {r.status_code})')

print('\n=== Migration complete ===')
