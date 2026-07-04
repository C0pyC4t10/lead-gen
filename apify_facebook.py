import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import date

import requests

SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')
APIFY_API_KEY = os.environ.get('APIFY_API_KEY', '')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'collected_leads')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'facebook_leads.csv')

BANNED_SLUGS = {
    'login', 'signup', 'help', 'about', 'home', 'watch',
    'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
    'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live',
}


def normalize_url(url):
    url = url.replace('m.facebook.com', 'www.facebook.com')
    q_idx = url.find('?')
    if q_idx != -1:
        url = url[:q_idx]
    f_idx = url.find('#')
    if f_idx != -1:
        url = url[:f_idx]
    return url.rstrip('/')


def extract_slug(url):
    idx = url.find('facebook.com')
    if idx == -1:
        return None
    path = url[idx + len('facebook.com'):].lstrip('/')
    if not path:
        return None
    return path.split('/')[0]


def is_valid_slug(slug):
    if not slug:
        return False
    if slug in BANNED_SLUGS:
        return False
    if not any(c.isalpha() for c in slug):
        return False
    if len(slug) < 3:
        return False
    return True


def clean_url(url):
    url = normalize_url(url)
    slug = extract_slug(url)
    if slug:
        return f'https://www.facebook.com/{slug}/'
    return url


# ── Step 1: SerpAPI Google Search ──────────────────────────────

AVAILABLE_FACEBOOK_ACTORS = [
    "apify/facebook-pages-scraper — Facebook Pages Scraper (URLs only, no search query)",
]


def search_facebook_urls(keyword, limit=20):
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY not set.")
        return []

    query = f'"{keyword}" site:facebook.com -groups -events -marketplace'
    if 'bangladesh' not in keyword.lower():
        query = f'"{keyword} Bangladesh" site:facebook.com -groups -events -marketplace'
    else:
        query = f'"{keyword}" site:facebook.com -groups -events -marketplace'

    print(f"  SerpAPI query: {query}")

    params = {
        'engine': 'google',
        'q': query,
        'api_key': SERPAPI_KEY,
        'num': limit,
    }

    try:
        resp = requests.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"  SerpAPI request error: {e}")
        return []

    if 'error' in data:
        print(f"  SerpAPI error: {data['error']}")
        return []

    urls = []
    seen = set()
    for r in data.get('organic_results', []):
        link = (r.get('link') or '').strip()
        if not link or 'facebook.com' not in link:
            continue
        clean = clean_url(link)
        slug = extract_slug(clean)
        if not is_valid_slug(slug):
            continue
        if clean in seen:
            continue
        seen.add(clean)
        urls.append(clean)
        if len(urls) >= limit:
            break

    print(f"  Found {len(urls)} Facebook page URL(s)")
    return urls


# ── Step 2: Apify Facebook Pages Scraper ───────────────────────

APIFY_BASE = 'https://api.apify.com/v2'
ACTOR_ID = 'apify~facebook-pages-scraper'


def start_apify_run(page_urls):
    headers = {
        'Authorization': f'Bearer {APIFY_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'startUrls': [{'url': u} for u in page_urls],
        'maxPagesPerQuery': 1,
    }
    resp = requests.post(
        f'{APIFY_BASE}/acts/{ACTOR_ID}/runs',
        headers=headers,
        json=payload,
        timeout=30,
    )
    data = resp.json()
    run_id = data.get('data', {}).get('id')
    if not run_id:
        print(f"  Apify start run error: {data.get('error', {}).get('message', 'unknown')}")
        return None
    print(f"  Apify run started: {run_id}")
    return run_id


def poll_apify_run(run_id, timeout=120, interval=10):
    headers = {'Authorization': f'Bearer {APIFY_API_KEY}'}
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f'{APIFY_BASE}/actor-runs/{run_id}',
            headers=headers,
            timeout=15,
        )
        data = resp.json()
        status = data.get('data', {}).get('status', 'UNKNOWN')
        print(f"    Status: {status}")
        if status == 'SUCCEEDED':
            return True
        if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
            print(f"    Run ended with status: {status}")
            return False
        time.sleep(interval)
    print("    Timeout reached.")
    return False


def get_apify_results(run_id):
    headers = {'Authorization': f'Bearer {APIFY_API_KEY}'}
    resp = requests.get(
        f'{APIFY_BASE}/actor-runs/{run_id}/dataset/items',
        headers=headers,
        timeout=20,
    )
    if resp.status_code != 200:
        print(f"  Failed to get results: {resp.status_code}")
        return []
    return resp.json()


def score_apify_result(item):
    name = (item.get('title') or '').strip()
    phone = (item.get('phone') or '').strip()
    email = (item.get('email') or '').strip()
    address = (item.get('address') or '').strip()
    url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
    website = (item.get('website') or '').strip()
    categories = item.get('categories') or []
    likes_str = item.get('likes') or item.get('followers') or 0
    try:
        likes = int(re.sub(r'[^0-9]', '', str(likes_str))) if likes_str else 0
    except (ValueError, TypeError):
        likes = 0

    has_website = bool(website)

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

    return {
        'name': name or extract_slug(url),
        'url': url,
        'phone': phone,
        'email': email,
        'address': address,
        'likes': likes,
        'category': '; '.join(categories) if categories else '',
        'website': website,
        'has_website': has_website,
        'score': score,
    }, score


# ── CSV Save ──────────────────────────────────────────────────

def load_existing_urls():
    if not os.path.exists(OUTPUT_FILE):
        return set()
    with open(OUTPUT_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return set(row['url'].strip() for row in reader if row.get('url'))


def save_results(results, apify_run_id=''):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing_urls = load_existing_urls()

    fieldnames = ['date', 'name', 'url', 'snippet', 'phone', 'has_website', 'score', 'status', 'notes', 'apify_run_id']
    rows = []
    new_count = 0
    dup_count = 0

    for r in results:
        url = r.get('url', '').rstrip('/')
        if url in existing_urls:
            dup_count += 1
            continue
        rows.append({
            'date': str(date.today()),
            'name': r.get('name', ''),
            'url': url,
            'snippet': '',
            'phone': r.get('phone', ''),
            'has_website': str(r.get('has_website', False)),
            'score': r.get('score', 0),
            'status': 'new',
            'notes': '',
            'apify_run_id': apify_run_id,
        })
        new_count += 1

    if not rows:
        return new_count, dup_count

    file_exists = os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    return new_count, dup_count


# ── Main ──────────────────────────────────────────────────────

def main():
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY environment variable not set.")
        sys.exit(1)
    if not APIFY_API_KEY:
        print("ERROR: APIFY_API_KEY environment variable not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Find Facebook page URLs (SerpAPI) then scrape full page data (Apify facebook-pages-scraper)'
    )
    parser.add_argument('keyword', help='Business type to search (e.g. "beauty parlor")')
    parser.add_argument('--limit', type=int, default=5, help='Max results (default: 5)')
    args = parser.parse_args()

    keyword = args.keyword

    # Step 1
    print(f"Step 1 — Searching Facebook pages for: {keyword}")
    page_urls = search_facebook_urls(keyword, limit=20)

    if not page_urls:
        print('No Facebook page URLs found via SerpAPI.')
        return

    # Step 2
    print(f"\nStep 2 — Sending {len(page_urls)} URL(s) to Apify Facebook Pages Scraper...")
    run_id = start_apify_run(page_urls)
    if not run_id:
        print('Failed to start Apify run.')
        return

    if not poll_apify_run(run_id):
        print('Apify run did not complete successfully.')
        return

    print('  Fetching results...')
    items = get_apify_results(run_id)
    print(f"  Got {len(items)} raw result(s) from Apify")

    if not items:
        print('No results returned from Apify.')
        return

    # Score and filter
    scored = []
    for item in items:
        result, s = score_apify_result(item)
        scored.append(result)

    scored = [r for r in scored if r['score'] >= 6]
    scored.sort(key=lambda r: r['score'], reverse=True)
    scored = scored[:args.limit]

    if not scored:
        print('No results passed score threshold (>= 6).')
        return

    # Save
    new_count, dup_count = save_results(scored, apify_run_id=run_id)

    if dup_count > 0:
        print(f'\nSkipped {dup_count} existing URL(s) (already saved).')

    if new_count == 0 and dup_count > 0:
        print('No new Facebook pages found.')
        return

    print(f'\nFound {new_count} new Facebook page(s):')
    for i, r in enumerate(scored, 1):
        print(f'{i}. {r["url"]}')

    print(f'\n{new_count} new lead(s) saved to {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
