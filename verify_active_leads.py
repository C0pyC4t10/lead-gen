#!/usr/bin/env python3
"""Re-check best candidate pages for active ads status, build clean CSV."""
import requests, os, json, re, time, sys
import csv

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

CSV_PATH = '/home/skarbolt/kb/lead-gen/collected_leads/facebook_leads.csv'

# ── Load existing CSV ──
all_rows = []
with open(CSV_PATH, 'r') as f:
    reader = csv.DictReader(f)
    for r in reader:
        all_rows.append(r)

# ── Known good leads from earlier runs (verified active ads) ──
# These were confirmed "🔥 RUNNING ADS" by find_active_ads.py
VERIFIED = [
    # From first batch
    "Dhaka Fashion Shop", "Your Shop BD", "Olivia's Makeover And Beauty Salon",
    "Lavish Boutique Salon", "Oishe Beauty Salon", "La Femme Beauty Salon Dhaka",
    "Leaf Lounge", "Hongbao", "Aquavista", "NH Gadget Store",
    "Gold Plated Jewellery Online Shop",
    
    # From clothing/home decor batch
    "Asma Fashion", "ANIQ - Home Decor", "Sohan mirror & glass decor",
    "Art Work Bangladesh",
    
    # From bags/footwear batch
    "Samia's Crochet", "Gootipa - গুটিপা", "Dreamers Shop",
    "Nishat Linen Bangladesh", "Sparrowfootwear", "Dhaka Audio & Gadgets",
    
    # From grocery/baby/perfume batch
    "Baby Blue or Pink Bird", "Mum & Little Ones", "Baby Shop Limited",
    "Little Angels", "Kids Paradise", "Unimart",
    "foodi", "Lavender Super Store Ltd.", "Khulshi Mart",
    "Elate Perfume",
    
    # From salon/gift batch
    "London's Cut", "Adonis Men's Grooming Salon", "Signature Men's Salon",
    "Safa Gift Shop", "Dhaka Gift Shop", "BD PRICE",
    
    # From skincare/cosmetics batch
    "Cetaphil Skincare Bangladesh", "Aveeno Skincare Bangladesh",
    "Emart Skincare Bangladesh", "Emily's Beauty Co.",
    "China Beauty Cosmetics", "Taupe Notch",
    
    # From product seller batch
    "Easy Fashion Ltd.", "Easy Fashion Online Shop",
    "Glamgrl", "Sarmin's CRAFT", "Moon's gallery- shop ur dreams",
    "Beautyology", "Don Sumdany", "Brand Electronics BD",
    "Fency skin care products BD", "Toy Shop BD",
    "Hlwcraft.com", "Mehedi Enterprise", "Hello Junior",
    "Craftimation-ক্রাফটিমেশন", "Electronics-BD",
    "Kids and Moms", "Dubai Electronics BD",
    "Everywear Bangladesh Limited", "Story Brand",
    "JFM Corporation",
]

# Also collect high-engagement pages that might be running ads from the actual ad_status data
print("Building verified active leads list...")

# ── Find and verify URL for each candidate ──
found = []
for verified_name in VERIFIED:
    matches = [r for r in all_rows if verified_name.lower() in (r.get('name') or '').lower()]
    if matches:
        # Take the best match
        best = max(matches, key=lambda x: len(x.get('url', '')))
        found.append(best)
        print(f"  ✅ Found: {verified_name}")

print(f"\nFound {len(found)} of {len(VERIFIED)} verified leads in CSV")

# ── Now let's actually check ad_status for these via Apify ──
print(f"\nRe-checking ad_status for all via Apify...")

# Get unique URLs
urls_to_check = []
seen = set()
for r in found:
    url = (r.get('url') or '').strip()
    if url and url not in seen:
        seen.add(url)
        urls_to_check.append(url)

print(f"Checking {len(urls_to_check)} unique URLs...")

# Check in batches of 10
active_verified = []
for i in range(0, len(urls_to_check), 10):
    batch = urls_to_check[i:i+10]
    payload = {
        'startUrls': [{'url': u} for u in batch],
        'maxPagesPerQuery': 1,
    }
    
    resp = requests.post(
        'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs',
        headers=headers, json=payload, timeout=30
    )
    run_data = resp.json()
    run_id = run_data.get('data', {}).get('id')
    if not run_id:
        print(f"  Batch {i//10+1}: Apify error")
        continue
    
    print(f"  Batch {i//10+1}: Apify run {run_id}", end='')
    
    deadline = time.time() + 120
    while time.time() < deadline:
        resp = requests.get(f'https://api.apify.com/v2/actor-runs/{run_id}', headers=headers, timeout=15)
        status = resp.json().get('data', {}).get('status', 'UNKNOWN')
        if status == 'SUCCEEDED':
            break
        if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
            print(f" -> {status}")
            run_id = None
            break
        print('.', end='', flush=True)
        time.sleep(6)
    
    if not run_id:
        continue
    
    print(" OK")
    
    resp = requests.get(
        f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
        headers=headers, timeout=20
    )
    items = resp.json()
    if isinstance(items, dict):
        items = items.get('data', [])
    
    for item in items:
        url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
        ad_status = item.get('ad_status', '')
        is_active = 'currently running' in ad_status.lower()
        
        # Find matching lead
        for r in found:
            r_url = (r.get('url') or '').strip()
            if r_url and r_url.rstrip('/') == url.rstrip('/'):
                r['ad_status'] = ad_status
                if is_active:
                    active_verified.append(r)
                    print(f"    ✅ ACTIVE: {r.get('name', '')}")
                break
    
    time.sleep(1)

print(f"\n═══ RESULTS ═══")
print(f"Total verified leads: {len(found)}")
print(f"Currently running ads: {len(active_verified)}")

# ── Sort by likes ──
def get_likes(r):
    try:
        return int(re.sub(r'[^0-9]', '', str(r.get('likes', '0'))))
    except:
        return 0

active_verified.sort(key=lambda r: -get_likes(r))

# ── Print ──
for i, r in enumerate(active_verified, 1):
    name = (r.get('name') or '')[:45]
    phone = (r.get('phone') or '').strip() or 'N/A'
    likes = get_likes(r)
    has_web = r.get('has_website', '').strip().lower() in ('yes', 'true', 'y', '1')
    score = r.get('score', '0')
    url = (r.get('url') or '')
    hot = "🔥" if not has_web and phone != 'N/A' else ""
    
    print(f" {i:2d}. {hot} [{score}/12] {name}")
    print(f"     👍 {likes:>8,} | 📞 {phone:15s} | {'❌ No website' if not has_web else '✅ Website'}")
    print(f"     🔗 {url}")
    print()

# ── Save clean CSV ──
OUT = '/home/skarbolt/kb/lead-gen/qualified_leads/verified_active_leads.csv'
import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['#', 'Name', 'Phone', 'Likes', 'Website', 'Score', 'Facebook URL'])
    for i, r in enumerate(active_verified, 1):
        w.writerow([
            i,
            (r.get('name') or '').strip(),
            (r.get('phone') or '').strip() or 'N/A',
            get_likes(r),
            'No' if (r.get('has_website', '').strip().lower() in ('no', 'false', 'n', '') or not r.get('has_website', '').strip()) else 'Yes',
            r.get('score', '0'),
            (r.get('url') or '').strip()
        ])
print(f"\n✅ Clean CSV saved: {OUT} ({len(active_verified)} active verified leads)")
