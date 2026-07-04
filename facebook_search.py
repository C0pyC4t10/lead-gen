import argparse
import csv
import os
import re
import sys
import time
from datetime import date

import requests

SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'collected_leads')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'facebook_leads.csv')

BANNED_PATH_SEGMENTS = {
    'media', 'mentions', 'photos', 'videos', 'posts', 'events', 'groups',
    'marketplace', 'watch', 'gaming', 'hashtag', 'set', 'story',
    'permalink', 'comment', 'reply', 'reactions', 'shares',
}

BANNED_SLUGS = {
    'login', 'signup', 'help', 'about', 'home', 'watch',
    'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
    'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live',
}

PHONE_PATTERN = re.compile(r'01[3-9]\d{8}')


def build_queries(keyword):
    k = keyword.strip()
    exclude = '-login -signup -help -groups -events'
    return [
        f'"{k}" site:facebook.com {exclude}',
        f'"{k}" Bangladesh site:facebook.com {exclude}',
        f'"{k}" Dhaka "01" site:facebook.com {exclude}',
    ]


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


def has_banned_path(url):
    idx = url.find('facebook.com')
    if idx == -1:
        return True
    path = url[idx + len('facebook.com'):].lstrip('/')
    segments = path.split('/')
    for seg in segments[1:]:
        if seg in BANNED_PATH_SEGMENTS:
            return True
    return False


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
    slug = extract_slug(url)
    if slug:
        return f'https://www.facebook.com/{slug}/'
    return url


def find_phone(snippet):
    m = PHONE_PATTERN.search(snippet)
    return m.group(0) if m else ''


def search_serpapi(query):
    params = {
        'engine': 'google',
        'q': query,
        'api_key': SERPAPI_KEY,
        'num': 10,
    }
    try:
        resp = requests.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"  Request error: {e}")
        return []

    if 'error' in data:
        print(f"  SerpAPI error: {data['error']}")
        return []

    results = []
    seen_clean = set()
    for r in data.get('organic_results', []):
        link = (r.get('link') or '').strip()
        title = (r.get('title') or '').strip()
        snippet = (r.get('snippet') or '')

        if not link or 'facebook.com' not in link:
            continue

        url = normalize_url(link)

        if has_banned_path(url):
            continue

        slug = extract_slug(url)
        if not is_valid_slug(slug):
            continue

        clean = clean_url(url)
        if not clean.startswith('https://www.facebook.com/'):
            continue

        if clean in seen_clean:
            continue
        seen_clean.add(clean)

        phone = find_phone(snippet)
        has_website = any(w in snippet.lower() for w in ['website', 'www.', 'http'])

        score = 5
        if phone:
            score += 2
        if not has_website:
            score += 2
        if any(w in snippet.lower() for w in ['delivery', 'order', 'shop', 'store', 'service']):
            score += 1
        if any(w in snippet.lower() for w in ['unofficial', 'fan page', 'community']):
            score -= 2

        results.append({
            'name': title,
            'url': clean,
            'snippet': snippet,
            'phone': phone,
            'has_website': has_website,
            'score': score,
        })

    return results


def search_all(keyword, limit=10):
    queries = build_queries(keyword)
    all_results = []
    seen_urls = set()

    for i, q in enumerate(queries, 1):
        print(f"  Query {i}: {q}")
        results = search_serpapi(q)

        for r in results:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                all_results.append(r)

        if i < len(queries):
            time.sleep(1)

    all_results = [r for r in all_results if r['score'] >= 5]
    all_results.sort(key=lambda r: r['score'], reverse=True)

    return all_results[:limit]


def load_existing_urls():
    if not os.path.exists(OUTPUT_FILE):
        return set()
    with open(OUTPUT_FILE, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return set(row['url'].strip() for row in reader if row.get('url'))


def save_results(results):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    existing_urls = load_existing_urls()

    fieldnames = ['date', 'name', 'url', 'snippet', 'phone', 'has_website', 'score', 'status', 'notes']
    rows = []
    new_count = 0
    dup_count = 0

    for r in results:
        if r['url'] in existing_urls:
            dup_count += 1
            continue
        rows.append({
            'date': str(date.today()),
            'name': r['name'],
            'url': r['url'],
            'snippet': r['snippet'],
            'phone': r['phone'],
            'has_website': str(r['has_website']),
            'score': r['score'],
            'status': 'new',
            'notes': '',
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


def main():
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY environment variable not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description='Search Facebook business pages via Google (SerpAPI)'
    )
    parser.add_argument('keyword', help='Business type to search (e.g. "beauty parlor")')
    parser.add_argument('--limit', type=int, default=10, help='Max results (default: 10)')
    args = parser.parse_args()

    keyword = args.keyword
    if 'bangladesh' not in keyword.lower():
        keyword = f'{keyword} Bangladesh'

    print(f"Searching Facebook pages for: {keyword}")
    results = search_all(keyword, limit=args.limit)

    if not results:
        print('No Facebook pages found.')
        return

    new_count, dup_count = save_results(results)

    if dup_count > 0:
        print(f'\nSkipped {dup_count} existing URL(s) (already saved).')

    if new_count == 0 and dup_count > 0:
        print('No new Facebook pages found.')
        return

    print(f'\nFound {new_count} new Facebook page(s):')
    for i, r in enumerate(results, 1):
        print(f'{i}. {r["url"]}')

    print(f'\n{new_count} new lead(s) saved to {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
