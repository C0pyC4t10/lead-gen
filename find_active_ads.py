"""Find Facebook pages currently running ads in Bangladesh."""
import requests, os, json, re, time, sys

key = os.environ.get('APIFY_API_KEY', '')
serp_key = os.environ.get('SERPAPI_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

keywords = sys.argv[1:] if len(sys.argv) > 1 else [
    'fashion shop Dhaka', 'beauty salon Dhaka', 'restaurant Dhaka',
    'gadget store Dhaka', 'online shop Bangladesh'
]

seen_urls = set()

for kw in keywords:
    print(f"\n{'='*60}")
    print(f"SEARCHING: {kw}")
    print(f"{'='*60}")
    
    # SerpAPI search
    import requests as req
    params = {
        'engine': 'google',
        'q': f'"{kw}" site:facebook.com -groups -events -marketplace',
        'api_key': serp_key,
        'num': 15,
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
    
    BANNED_SLUGS = {'login', 'signup', 'help', 'about', 'home', 'watch',
                    'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
                    'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live'}
    
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
        if clean in seen:
            continue
        seen.add(clean)
        urls.append(clean)
    
    if not urls:
        print("  No valid URLs found")
        continue
    
    # Remove already-seen URLs
    urls = [u for u in urls if u not in seen_urls]
    if not urls:
        print("  All URLs already checked")
        continue
    
    print(f"  Found {len(urls)} new URLs, sending to Apify...")
    
    # Apify run
    payload = {'startUrls': [{'url': u} for u in urls[:10]], 'maxPagesPerQuery': 1}
    resp = req.post('https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs',
                    headers=headers, json=payload, timeout=30)
    run_data = resp.json()
    run_id = run_data.get('data', {}).get('id')
    if not run_id:
        print(f"  Apify error")
        continue
    
    print(f"  Apify run: {run_id}")
    
    # Poll
    deadline = time.time() + 120
    while time.time() < deadline:
        resp = req.get(f'https://api.apify.com/v2/actor-runs/{run_id}', headers=headers, timeout=15)
        status = resp.json().get('data', {}).get('status', 'UNKNOWN')
        print(f"    Status: {status}")
        if status == 'SUCCEEDED':
            break
        if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
            print(f"    Failed: {status}")
            run_id = None
            break
        time.sleep(8)
    
    if not run_id:
        continue
    
    resp = req.get(f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
                   headers=headers, timeout=20)
    items = resp.json()
    print(f"  Got {len(items)} result(s)")
    
    # Check ad_status and engagement
    active_ads = []
    for item in items:
        name = (item.get('title') or '').strip()
        url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
        phone = (item.get('phone') or '').strip()
        email = (item.get('email') or '').strip()
        ad_status = item.get('ad_status', 'N/A')
        likes_str = item.get('likes') or item.get('followers') or 0
        creation = item.get('creation_date', 'N/A')
        
        try:
            likes = int(re.sub(r'[^0-9]', '', str(likes_str))) if likes_str else 0
        except:
            likes = 0
        
        has_website = bool(item.get('website', ''))
        website = item.get('website', '')
        
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
        
        is_actively_ads = 'currently running' in ad_status.lower()
        
        ad_tag = "🔥 RUNNING ADS" if is_actively_ads else "❌ No ads"
        
        print(f"\n  [{score}/12] {name}")
        print(f"       📞 {phone or 'N/A'}")
        print(f"       👍 Likes: {likes:,}" if likes else "       👍 Likes: N/A")
        print(f"       {ad_tag} | Created: {creation}")
        print(f"       🌐 Website: {'Yes' if has_website else 'No'}")
        print(f"       🔗 {url}")
        
        if is_actively_ads:
            active_ads.append({
                'name': name, 'url': url, 'phone': phone,
                'likes': likes, 'score': score,
                'has_website': has_website, 'ad_status': ad_status
            })
        
        seen_urls.add(url)
    
    if active_ads:
        print(f"\n  🔥 ACTIVE ADVERTISERS ({len(active_ads)}):")
        for a in active_ads:
            print(f"  [{a['score']}/12] {a['name']} | 👍 {a['likes']:,} | 📞 {a['phone'] or 'N/A'} | {a['url']}")
    print()
