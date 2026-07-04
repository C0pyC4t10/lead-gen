import argparse, json, os, subprocess, sys, time

import requests

SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'collected_leads', 'discovered_urls.txt')
CHECK_SCRIPT = os.path.join(os.path.dirname(__file__), 'check_fb_activity.py')

SKIP_PATTERNS = [
    '/groups/', '/events/', '/marketplace/',
    '/story.php', '/photo.php', '/video.php',
    '/profile.php', '/messages/', '/watch/',
    '/posts/', '/reel/', '/share/', '/photos/',
]


def load_existing_urls():
    if not os.path.exists(OUTPUT_FILE):
        return set()
    with open(OUTPUT_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())


def save_url(url):
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'a') as f:
        f.write(url + '\n')


def is_valid_facebook_page(url):
    url = url.rstrip('/')
    if 'facebook.com' not in url:
        return False

    # Normalize mobile URLs
    url = url.replace('m.facebook.com', 'www.facebook.com')

    # Skip known non-page patterns
    for skip in SKIP_PATTERNS:
        if skip in url:
            return False

    # Skip old-format /pages/ URLs (unofficial/abandoned)
    if '/pages/' in url:
        return False

    # Extract path after facebook.com
    idx = url.find('facebook.com')
    path = url[idx + len('facebook.com'):]

    # Must have a path
    if not path or path == '/':
        return False

    # Get the first path segment as slug
    slug = path.lstrip('/').rstrip('/').split('/')[0]

    # Slug must be at least 5 characters
    if len(slug) < 5:
        return False

    # Slug must contain at least one letter (not purely numeric)
    if not any(c.isalpha() for c in slug):
        return False

    return True


def check_activity(url):
    try:
        result = subprocess.run(
            [sys.executable, CHECK_SCRIPT, url],
            capture_output=True, text=True, timeout=25,
        )
        if result.returncode == 0:
            return json.loads(result.stdout.strip())
    except Exception:
        pass
    return None


def search_serpapi(query, limit=10):
    full_query = f'site:facebook.com {query} Bangladesh -inurl:/pages/ -inurl:/groups/ -inurl:/events/ -inurl:/marketplace/ -inurl:profile.php'
    max_results = limit
    found = set()

    params = {
        'engine': 'google',
        'q': full_query,
        'api_key': SERPAPI_KEY,
        'num': min(max_results, 20),
    }

    while len(found) < max_results:
        resp = requests.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()

        if 'error' in data:
            print(f"SerpAPI error: {data['error']}")
            break

        results = data.get('organic_results', [])
        if not results:
            break

        for r in results:
            link = r.get('link', '')
            if is_valid_facebook_page(link):
                found.add(link.rstrip('/'))
                if len(found) >= max_results:
                    break

        pagination = data.get('serpapi_pagination') or {}
        next_token = pagination.get('next_page_token')
        if next_token and len(found) < max_results:
            params['next_page_token'] = next_token
            time.sleep(1)
        else:
            break

    return sorted(found)


def main():
    if not SERPAPI_KEY:
        print("ERROR: SERPAPI_KEY environment variable not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Search Google for Facebook pages via SerpAPI')
    parser.add_argument('keyword', help='Business type to search (e.g. "beauty parlor dhaka")')
    parser.add_argument('--limit', type=int, default=10,
                        help='Maximum number of URLs to return (default: 10)')
    parser.add_argument('--check-activity', action='store_true', default=False,
                        help='Check each URL for recent activity and filter inactive')
    args = parser.parse_args()

    print(f"Searching: site:facebook.com {args.keyword} Bangladesh")

    urls = search_serpapi(args.keyword, limit=args.limit)
    existing = load_existing_urls()

    if not urls:
        print('No Facebook pages found.')
        return

    if args.check_activity:
        print(f'\nChecking activity for {len(urls)} pages...')
        active_urls = []
        for i, url in enumerate(urls, 1):
            sys.stdout.write(f'\r  [{i}/{len(urls)}] checking...')
            sys.stdout.flush()
            info = check_activity(url)
            if info and info.get('status') in ('active', 'unknown'):
                active_urls.append((url, info))
            elif info:
                print(f'\n    SKIPPED {url} — {info["status"]} ({info.get("days_since_post", "?")} days)')
            else:
                active_urls.append((url, {'status': 'unknown', 'days_since_post': None}))
            time.sleep(0.5)
        sys.stdout.write('\n')
        sys.stdout.flush()
        urls = [u for u, _ in active_urls]

    urls = urls[:args.limit]

    new_urls = [url for url in urls if url not in existing]
    duplicates = len(urls) - len(new_urls)

    if duplicates > 0:
        print(f'\nSkipped {duplicates} existing URL(s) (already saved).')

    if not new_urls:
        print('No new Facebook pages found.')
        return

    print(f'\nFound {len(new_urls)} new Facebook page(s):\n')
    for url in new_urls:
        print(f'  [NEW] {url}')
        save_url(url)

    print(f'\n{len(new_urls)} new URL(s) saved to {OUTPUT_FILE}')


if __name__ == '__main__':
    main()
