"""Run Apify scraper and show likes/engagement data for leads."""
import subprocess, json, sys, os, re, time, csv
from datetime import date

APIFY_API_KEY = os.environ.get('APIFY_API_KEY', '')
SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')
APIFY_BASE = 'https://api.apify.com/v2'
ACTOR_ID = 'apify~facebook-pages-scraper'

# Run all keywords
keywords = sys.argv[1:] if len(sys.argv) > 1 else [
    'popular shop Bangladesh',
    'top brand Bangladesh',
    'fashion house Bangladesh',
    'online store Bangladesh',
]

for kw in keywords:
    print(f"\n{'='*60}")
    print(f"SEARCHING: {kw}")
    print(f"{'='*60}")
    
    # Step 1: Search with SerpAPI
    query = f'"{kw}" site:facebook.com -groups -events -marketplace'
    if 'bangladesh' not in kw.lower():
        query = f'"{kw} Bangladesh" site:facebook.com -groups -events -marketplace'
    else:
        query = f'"{kw}" site:facebook.com -groups -events -marketplace'
    
    import requests
    params = {
        'engine': 'google',
        'q': query,
        'api_key': SERPAPI_KEY,
        'num': 20,
    }
    try:
        resp = requests.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"  SerpAPI error: {e}")
        continue
    
    if 'error' in data:
        print(f"  SerpAPI error: {data['error']}")
        continue
    
    # Extract valid URLs
    BANNED_SLUGS = {'login', 'signup', 'help', 'about', 'home', 'watch',
                    'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
                    'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live'}
    
    urls = []
    seen = set()
    for r in data.get('organic_results', []):
        link = (r.get('link') or '').strip()
        if not link or 'facebook.com' not in link:
            continue
        # Normalize
        link = link.replace('m.facebook.com', 'www.facebook.com')
        q_idx = link.find('?')
        if q_idx != -1:
            link = link[:q_idx]
        link = link.rstrip('/')
        
        # Extract slug
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
        if clean in seen:
            continue
        seen.add(clean)
        urls.append(clean)
    
    if not urls:
        print("  No valid Facebook page URLs found.")
        continue
    
    print(f"  Found {len(urls)} URLs, sending to Apify...")
    
    # Step 2: Apify run
    headers = {'Authorization': f'Bearer {APIFY_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'startUrls': [{'url': u} for u in urls], 'maxPagesPerQuery': 1}
    
    resp = requests.post(f'{APIFY_BASE}/acts/{ACTOR_ID}/runs', headers=headers, json=payload, timeout=30)
    run_data = resp.json()
    run_id = run_data.get('data', {}).get('id')
    if not run_id:
        print(f"  Apify error: {run_data.get('error', {}).get('message', 'unknown')}")
        continue
    
    print(f"  Apify run: {run_id}")
    
    # Poll
    deadline = time.time() + 120
    while time.time() < deadline:
        resp = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}', headers=headers, timeout=15)
        status = resp.json().get('data', {}).get('status', 'UNKNOWN')
        print(f"    Status: {status}")
        if status == 'SUCCEEDED':
            break
        if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
            print(f"    Failed: {status}")
            run_id = None
            break
        time.sleep(10)
    
    if not run_id:
        continue
    
    # Get results
    resp = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}/dataset/items', headers=headers, timeout=20)
    if resp.status_code != 200:
        print(f"  Failed to get results: {resp.status_code}")
        continue
    
    items = resp.json()
    print(f"  Got {len(items)} result(s)")
    
    # Process with engagement data
    high_engagement = []
    for item in items:
        name = (item.get('title') or '').strip()
        url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
        phone = (item.get('phone') or '').strip()
        email = (item.get('email') or '').strip()
        website = (item.get('website') or '').strip()
        address = (item.get('address') or '').strip()
        categories = item.get('categories') or []
        
        likes_str = item.get('likes') or item.get('followers') or 0
        try:
            likes = int(re.sub(r'[^0-9]', '', str(likes_str))) if likes_str else 0
        except:
            likes = 0
        
        has_website = bool(website)
        
        # Score
        score = 5
        if not has_website:
            score += 2
        if phone:
            score += 2
        if email:
            score += 1
        if likes > 100:
            score += 1
        if 0 < likes < 50000:
            score += 1
        cat_text = ' '.join(categories).lower() if categories else ''
        if any(w in cat_text for w in ['government', 'politician', 'news', 'media']):
            score -= 3
        
        print(f"\n  [{score}/12] {name}")
        print(f"       📞 {phone or 'N/A'} | 📧 {email or 'N/A'}")
        print(f"       👍 Likes: {likes:,}" if likes else "       👍 Likes: N/A")
        print(f"       🌐 Website: {'Yes' if has_website else 'No'}")
        print(f"       📍 {address}" if address else "")
        print(f"       🔗 {url}")
        if categories:
            print(f"       🏷️ {', '.join(categories[:3])}")
        
        if likes >= 500 or phone:
            high_engagement.append({
                'name': name, 'url': url, 'phone': phone, 'likes': likes,
                'has_website': has_website, 'score': score, 'address': address
            })
    
    if high_engagement:
        print(f"\n  --- TOP ENGAGEMENT ({len(high_engagement)} leads) ---")
        high_engagement.sort(key=lambda x: (x['likes'], x['score']), reverse=True)
        for h in high_engagement[:5]:
            eng = f"👍 {h['likes']:,}" if h['likes'] else ""
            print(f"  [{h['score']}/12] {h['name']} | {eng} | 📞 {h['phone'] or 'N/A'} | {h['url']}")
    print()
