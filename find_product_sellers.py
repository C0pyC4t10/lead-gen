"""Find Facebook pages actively selling products AND running ads."""
import requests, os, json, re, time, sys

key = os.environ.get('APIFY_API_KEY', '')
serp_key = os.environ.get('SERPAPI_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# Product-focused keywords for BD markets
keywords = [
    'products Dhaka', 'shop online Dhaka', 'buy Dhaka', 'selling Dhaka',
    'handmade products Dhaka', 'fashion products Bangladesh',
    'organic products Bangladesh', 'online store Bangladesh',
    'gadget shop BD', 'clothing brand Bangladesh',
    'accessories shop Dhaka', 'cosmetics shop Dhaka',
    'baby products Bangladesh', 'jewelry shop Bangladesh',
    'shoe shop Dhaka', 'home products Dhaka',
    'grocery shop Dhaka', 'electronics BD',
    'gift items Bangladesh', 'bags shop Dhaka',
    'toys BD', 'mobile accessories BD',
    'skin care products BD', 'perfume BD',
    'sports accessories BD', 'handicraft Bangladesh'
]

BANNED_SLUGS = {'login', 'signup', 'help', 'about', 'home', 'watch',
                'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
                'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live',
                'jobs', 'fundraisers', 'saved', 'offers', 'covid'}

seen_urls = set()
all_active = []

# Load existing saved URLs from CSV
try:
    import csv
    with open('collected_leads/facebook_leads.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('url', '').strip()
            if url and 'facebook.com' in url:
                seen_urls.add(url.rstrip('/'))
    print(f"Loaded {len(seen_urls)} existing saved URLs")
except:
    print("No existing CSV found")

print(f"\n{'='*70}")
print(f"SCANNING {len(keywords)} PRODUCT-SELLING KEYWORDS")
print(f"{'='*70}")

for kw in keywords:
    print(f"\n[{keywords.index(kw)+1}/{len(keywords)}] Searching: {kw}")
    
    import requests as req
    params = {
        'engine': 'google',
        'q': f'"{kw}" site:facebook.com -groups -events -marketplace',
        'api_key': serp_key,
        'num': 10,
    }
    try:
        resp = req.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"  SerpAPI error: {e}")
        continue
    
    if 'error' in data:
        print(f"  SerpAPI error: {data['error']}")
        continue
    
    urls = []
    seen = set()
    for r in data.get('organic_results', []):
        link = (r.get('link') or '').strip()
        if not link or 'facebook.com' not in link:
            continue
        link = link.replace('m.facebook.com', 'www.facebook.com')
        q_idx = link.find('?')
        if q_idx != -1:
            link = link[:q_idx]
        link = link.rstrip('/')
        
        idx = link.find('facebook.com')
        if idx == -1:
            continue
        path = link[idx + len('facebook.com'):].lstrip('/')
        if not path:
            continue
        slug = path.split('/')[0]
        if not slug or slug in BANNED_SLUGS:
            continue
        if not any(c.isalpha() for c in slug):
            continue
        if len(slug) < 3:
            continue
        
        clean = f'https://www.facebook.com/{slug}/'
        if clean in seen or clean in seen_urls:
            continue
        seen.add(clean)
        urls.append(clean)
    
    if not urls:
        print("  No new URLs")
        continue
    
    print(f"  {len(urls)} new URL(s), sending to Apify...")
    
    payload = {'startUrls': [{'url': u} for u in urls[:10]], 'maxPagesPerQuery': 1}
    resp = req.post('https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs',
                    headers=headers, json=payload, timeout=30)
    run_data = resp.json()
    run_id = run_data.get('data', {}).get('id')
    if not run_id:
        print(f"  Apify error")
        continue
    
    print(f"  Apify run: {run_id}")
    
    deadline = time.time() + 120
    while time.time() < deadline:
        resp = req.get(f'https://api.apify.com/v2/actor-runs/{run_id}', headers=headers, timeout=15)
        status = resp.json().get('data', {}).get('status', 'UNKNOWN')
        if status == 'SUCCEEDED':
            break
        if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
            print(f"    Failed: {status}")
            run_id = None
            break
        print('.', end='', flush=True)
        time.sleep(6)
    print()
    
    if not run_id:
        continue
    
    resp = req.get(f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
                   headers=headers, timeout=20)
    items = resp.json() if isinstance(resp.json(), list) else resp.json().get('data', [])
    
    for item in items:
        name = (item.get('title') or '').strip()
        url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
        phone = (item.get('phone') or '').strip()
        ad_status = item.get('ad_status', 'N/A')
        likes_str = item.get('likes') or item.get('followers') or 0
        email = (item.get('email') or '').strip()
        category = (item.get('category') or '').strip()
        website = (item.get('website') or '').strip()[:80]
        
        try:
            likes = int(re.sub(r'[^0-9]', '', str(likes_str))) if likes_str else 0
        except:
            likes = 0
        
        has_website = bool(website)
        is_running_ads = 'currently running' in ad_status.lower()
        
        score = 5
        if not has_website: score += 2
        if phone: score += 2
        if 0 < likes < 50000: score += 1
        if email: score += 1
        
        if is_running_ads:
            all_active.append({
                'name': name, 'url': url, 'phone': phone,
                'likes': likes, 'score': score,
                'has_website': has_website, 'email': email,
                'ad_status': ad_status, 'website': website
            })
        
        # Mark seen
        seen_urls.add(url)
        
        if is_running_ads and phone:
            print(f"  ✅ [{score}/12] {name} | 👍 {likes:,} | 📞 {phone} | {'🌐' if has_website else '❌'} | 🚀 BOOSTING")
        elif is_running_ads:
            print(f"  🔹 [{score}/12] {name} | 👍 {likes:,} | 📞 N/A | {'🌐' if has_website else '❌'} | 🚀 BOOSTING")
    
    time.sleep(1)

# Deduplicate
seen_names = set()
unique_active = []
for a in all_active:
    n = a['name'].lower().strip()
    if n and n not in seen_names and 'by ' not in n[:5]:
        seen_names.add(n)
        unique_active.append(a)

unique_active.sort(key=lambda x: (-x['likes'], -x['score']))

print(f"\n\n{'='*70}")
print(f"🔥 ACTIVE ADVERTISERS FOUND: {len(unique_active)}")
print(f"TOP PRODUCT-SELLING PAGES WITH BOOSTS")
print(f"{'='*70}")
print()

for i, a in enumerate(unique_active[:30], 1):
    no_web = "| ❌ No website" if not a['has_website'] else ""
    print(f"{i:2d}. 🔥 [{a['score']}/12] {a['name']}")
    print(f"     👍 {a['likes']:,} | 📞 {a['phone'] or 'N/A'} | 🚀 Currently Boosting{no_web}")
    print(f"     🔗 {a['url']}")
    if a['email']:
        print(f"     📧 {a['email']}")
    print()
