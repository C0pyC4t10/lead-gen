#!/usr/bin/env python3
"""Add the latest product-seller leads from Apify to CSV, then generate full XLSX."""
import requests, os, json, re, time, sys
import csv
from datetime import date

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# Load existing saved URLs from CSV
CSV_PATH = '/home/skarbolt/kb/lead-gen/collected_leads/facebook_leads.csv'
seen_urls = set()
existing_rows = []

try:
    with open(CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            existing_rows.append(r)
            url = r.get('url', '').strip()
            if url:
                seen_urls.add(url.rstrip('/'))
    print(f"Existing CSV: {len(existing_rows)} rows, {len(seen_urls)} unique URLs")
except:
    print("No existing CSV, starting fresh")

FIELD_NAMES = ['date', 'name', 'url', 'snippet', 'phone', 'has_website', 
               'score', 'status', 'notes', 'apify_run_id',
               'likes', 'email', 'ad_status', 'website']

# Get recent Apify runs for the product seller actor
resp = requests.get(
    'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs?limit=20&status=SUCCEEDED',
    headers=headers, timeout=20
)
runs = resp.json().get('data', [])
if isinstance(runs, dict):
    runs = runs.get('items', [])

print(f"Found {len(runs)} recent runs")

new_count = 0
today = date.today().isoformat()

for run in runs:
    run_id = run.get('id', '')
    if not run_id:
        continue
    
    resp = requests.get(
        f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
        headers=headers, timeout=20
    )
    items = resp.json()
    if isinstance(items, dict):
        items = items.get('data', [])
    
    for item in items:
        name = (item.get('title') or '').strip()
        page_url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
        if not name or not page_url:
            continue
        
        # Clean URL
        page_url = page_url.replace('m.facebook.com', 'www.facebook.com')
        q_idx = page_url.find('?')
        if q_idx != -1:
            page_url = page_url[:q_idx]
        page_url = page_url.rstrip('/')
        
        if page_url in seen_urls:
            continue
        
        phone = (item.get('phone') or '').strip()
        email = (item.get('email') or '').strip()
        likes_str = item.get('likes') or item.get('followers') or 0
        ad_status = item.get('ad_status', '')
        website = (item.get('website') or '').strip()
        has_website = 'Yes' if website else 'No'
        
        try:
            likes = int(re.sub(r'[^0-9]', '', str(likes_str))) if likes_str else 0
        except:
            likes = 0
        
        # Calculate score
        score = 5
        if not has_website or not website:
            score += 2
        if phone:
            score += 2
        if email:
            score += 1
        if likes > 100:
            score += 1
        if likes > 10000:
            score += 1
        
        notes = 'Active Boost'
        if 'currently running' in ad_status.lower():
            notes = '🚀 Running Boost'
        
        row = {
            'date': today,
            'name': name,
            'url': page_url,
            'snippet': '',
            'phone': phone,
            'has_website': has_website,
            'score': score,
            'status': 'new',
            'notes': notes,
            'apify_run_id': run_id,
            'likes': likes,
            'email': email,
            'ad_status': ad_status,
            'website': website[:80] if website else ''
        }
        
        existing_rows.append(row)
        seen_urls.add(page_url)
        new_count += 1
        print(f"  NEW: [{score}/12] {name} | 📞 {phone or 'N/A'} | {has_website} | 🚀 {ad_status[:30]}")

print(f"\nTotal new leads added: {new_count}")
print(f"Total rows in CSV: {len(existing_rows)}")

# Write updated CSV
with open(CSV_PATH, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=FIELD_NAMES, extrasaction='ignore')
    writer.writeheader()
    for row in existing_rows:
        # Create a clean dict with only FIELD_NAMES keys
        clean = {}
        for fn in FIELD_NAMES:
            if fn == 'snippet':
                clean[fn] = ''
            elif fn == 'likes':
                val = row.get('likes', '')
                clean[fn] = int(re.sub(r'[^0-9]', '', str(val))) if val else 0
            else:
                clean[fn] = row.get(fn, '')
        writer.writerow(clean)

print(f"\n✅ CSV updated: {CSV_PATH} ({len(existing_rows)} leads)")
print("Now run generate_xlsx_report.py to create the XLSX")
