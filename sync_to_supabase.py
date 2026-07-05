"""Sync local leads to Supabase via REST API.

Reads from collected_leads/leads.csv and qualified_leads/CSV files,
posts new entries to Supabase via the REST API.

Usage:
    python3 sync_to_supabase.py
    python3 sync_to_supabase.py --watch   # keep running, sync every 30s
"""
import os, csv, time, json, hashlib, secrets, requests
from glob import glob
from datetime import datetime, timezone

SUPABASE_URL = 'https://lkmgyvkqbdftpgyvpcrd.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxrbWd5dmtxYmRmdHBneXZwY3JkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc4MzE3MDUzOCwiZXhwIjoyMDk4NzQ2NTM4fQ.nWfWIAgs-MgVAkAx67Spfj4QEr0KFH1D4aQTAHLTBqQ'
HEADERS = {
    'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json', 'Prefer': 'return=representation',
}

BASE = os.path.dirname(os.path.abspath(__file__))
LEADS_CSV = os.path.join(BASE, 'collected_leads', 'leads.csv')
QUALIFIED_DIR = os.path.join(BASE, 'qualified_leads')
LEADS_COLUMNS = [
    'date', 'platform', 'business_name', 'page_url', 'category', 'followers',
    'email', 'phone', 'website', 'has_website', 'address', 'last_post_date',
    'qualification_score', 'status', 'notes', 'follow_up_date', 'open_state', 'hours_text',
    'deleted_at', 'saved_by_user_id', 'saved_by_user_name',
]

def post(table, batch):
    r = requests.post(f'{SUPABASE_URL}/rest/v1/{table}', headers=HEADERS, json=batch, timeout=30)
    if r.status_code >= 300:
        return 0, r.text[:200]
    return len(batch), ''

def get_existing_urls():
    """Get all existing lead URLs to avoid duplicates."""
    r = requests.get(f'{SUPABASE_URL}/rest/v1/leads?select=page_url,saved_by_user_id', headers=HEADERS, timeout=30)
    if r.status_code >= 300:
        return set()
    rows = r.json()
    return {(r['page_url'], r.get('saved_by_user_id', 0)): True for r in rows}

def sync_leads():
    if not os.path.exists(LEADS_CSV):
        print('No leads.csv found')
        return 0
    with open(LEADS_CSV) as f:
        reader = csv.DictReader(f)
        leads = list(reader)
    if not leads:
        print('No leads to sync')
        return 0
    existing = get_existing_urls()
    new_leads = []
    for lead in leads:
        url = lead.get('page_url', '').strip()
        if not url:
            continue
        uid = int(lead.get('saved_by_user_id', 0) or 0)
        if (url, uid) in existing:
            continue
        new_leads.append({
            'date': lead.get('date', '')[:10],
            'platform': lead.get('platform', ''),
            'business_name': lead.get('business_name', ''),
            'page_url': url,
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
    if not new_leads:
        print(f'All {len(leads)} leads already synced')
        return 0
    total = 0
    for i in range(0, len(new_leads), 50):
        batch = new_leads[i:i+50]
        n, err = post('leads', batch)
        if err:
            print(f'  ERROR: {err}')
        else:
            total += n
            print(f'  Synced {n} leads ({total}/{len(new_leads)})')
    return total

def sync_qualified():
    if not os.path.isdir(QUALIFIED_DIR):
        return 0
    files = sorted(glob(f'{QUALIFIED_DIR}/2026-*.csv'))
    total = 0
    for filepath in files:
        with open(filepath) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if not rows:
            continue
        # Get existing qualified URLs to skip duplicates
        r = requests.get(f'{SUPABASE_URL}/rest/v1/qualified_leads?select=page_url,qualified_at', headers=HEADERS, timeout=30)
        existing = set()
        if r.status_code < 300:
            for q in r.json():
                existing.add((q.get('page_url', ''), q.get('qualified_at', '')))
        batch = []
        for row in rows:
            url = row.get('page_url', '').strip()
            if not url:
                continue
            qualified_at = row.get('qualified_at', '') or f"{row.get('date', '')} 00:00:00"
            if (url, qualified_at) in existing:
                continue
            batch.append({
                'page_url': url,
                'business_name': row.get('business_name', ''),
                'phone': row.get('phone', ''),
                'email': row.get('email', ''),
                'category': row.get('category', ''),
                'qualification_score': row.get('qualification_score', '0'),
                'qualified_at': qualified_at,
                'qualified_by_name': row.get('qualified_by', ''),
                'notes': row.get('notes', ''),
                'saved_by_user_id': 2,
            })
        if batch:
            n, err = post('qualified_leads', batch)
            if err:
                print(f'  qualified error: {err}')
            else:
                total += n
                print(f'  Synced {n} qualified from {os.path.basename(filepath)}')
    return total

def main():
    print('=== Syncing to Supabase via REST API ===')
    print(f'Target: {SUPABASE_URL}')
    print()
    n1 = sync_leads()
    print()
    n2 = sync_qualified()
    print()
    print(f'=== Done: {n1} new leads, {n2} new qualified ===')
    print('Refresh https://scraven.vercel.app to see them.')

if __name__ == '__main__':
    main()
