#!/usr/bin/env python3
"""
Serper.dev Facebook Lead Finder — No Apify needed.
Extracts engagement data (likes, "talking about this") from search result snippets.
Saves to a separate CSV to avoid schema conflicts.
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import date

import requests

SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'collected_leads')
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'serper_leads.csv')

BANNED_SLUGS = {
    'login', 'signup', 'help', 'about', 'home', 'watch',
    'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
    'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live',
    'business', 'commerce_manager', 'shops',
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
    slug_lower = slug.lower()
    if slug_lower in BANNED_SLUGS:
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


def extract_engagement(snippet):
    """Extract likes and 'talking about this' from a Google snippet."""
    likes = 0
    talking_about = 0
    if not snippet:
        return likes, talking_about

    likes_match = re.search(r'([\d,\.]+)\s*(?:likes|like)', snippet)
    if likes_match:
        try:
            likes = int(likes_match.group(1).replace(',', '').replace('.', ''))
        except ValueError:
            pass

    talking_match = re.search(r'([\d,\.]+)\s*talking\s*about\s*(?:this|)', snippet)
    if talking_match:
        try:
            talking_about = int(talking_match.group(1).replace(',', '').replace('.', ''))
        except ValueError:
            pass

    if not likes:
        followers_match = re.search(r'([\d,\.]+)\s*(?:followers|follows|follower)', snippet)
        if followers_match:
            try:
                likes = int(followers_match.group(1).replace(',', '').replace('.', ''))
            except ValueError:
                pass

    return likes, talking_about


def score_lead(likes, talking_about):
    score = 0
    if likes >= 1000000: score += 4
    elif likes >= 100000: score += 3
    elif likes >= 10000: score += 2
    elif likes >= 1000: score += 1
    if talking_about >= 10000: score += 4
    elif talking_about >= 1000: score += 3
    elif talking_about >= 100: score += 2
    elif talking_about >= 10: score += 1
    return min(score, 10)


def search_facebook(keyword, limit=20):
    query = f'{keyword} Bangladesh facebook page'
    if 'bangladesh' in keyword.lower():
        query = f'{keyword} facebook page'

    print(f"  Searching: {query}")

    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    payload = {'q': query, 'num': min(limit * 3, 50)}

    try:
        resp = requests.post('https://google.serper.dev/search', headers=headers, json=payload, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"  Request error: {e}")
        return []

    if 'organic' not in data:
        print(f"  Unexpected response: {json.dumps(data)[:200]}")
        return []

    leads = []
    seen = set()
    for r in data.get('organic', []):
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

        title = (r.get('title') or '').strip()
        snippet = (r.get('snippet') or '').strip()
        likes, talking = extract_engagement(snippet)

        name = title.replace(' - Facebook', '').replace(' | Facebook', '').replace(' - Home | Facebook', '').strip()
        score = score_lead(likes, talking)

        leads.append({
            'date': str(date.today()),
            'name': name[:80],
            'url': clean,
            'likes': str(likes) if likes else '0',
            'talking_about': str(talking) if talking else '0',
            'score': str(score),
            'keyword': keyword,
        })

        if len(leads) >= limit:
            break

    return leads


def save_leads(leads):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    fieldnames = ['date', 'name', 'url', 'likes', 'talking_about', 'score', 'keyword']

    existing_urls = set()
    if os.path.isfile(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_urls.add(row.get('url', ''))

    new_leads = [l for l in leads if l['url'] not in existing_urls]

    if not new_leads:
        print("  No new leads to save (all already in CSV).")
        return leads

    file_exists = os.path.isfile(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for lead in new_leads:
            writer.writerow({k: lead.get(k, '') for k in fieldnames})

    print(f"  Saved {len(new_leads)} new lead(s) to {OUTPUT_FILE}")
    return leads


def main():
    parser = argparse.ArgumentParser(description='Serper.dev Facebook Lead Finder')
    parser.add_argument('keywords', nargs='+', help='Search keywords')
    parser.add_argument('--limit', type=int, default=10, help='Max leads per keyword')
    parser.add_argument('--save', action='store_true', help='Save to CSV')
    args = parser.parse_args()

    if not SERPER_API_KEY:
        print("ERROR: SERPER_API_KEY not set.")
        sys.exit(1)

    all_leads = []
    for keyword in args.keywords:
        print(f"\n▶ Searching for: {keyword}")
        leads = search_facebook(keyword, limit=args.limit)
        print(f"  Found {len(leads)} lead(s)")
        all_leads.extend(leads)

    if args.save and all_leads:
        save_leads(all_leads)

    # Display all results
    total = len(all_leads)
    print(f"\n{'='*60}")
    print(f"  ALL RESULTS — {total} lead(s)")
    print(f"{'='*60}")

    for i, lead in enumerate(all_leads, 1):
        score = int(lead['score'])
        bar = '█' * score + '░' * (10 - score)
        likes = lead['likes']
        talking = lead['talking_about']
        likes_str = f"{int(likes):,}" if likes.isdigit() and int(likes) > 0 else '?'
        talking_str = f"{int(talking):,}" if talking.isdigit() and int(talking) > 0 else '0'
        
        print(f"\n{'-'*50}")
        print(f"  {i}. 🔥 Score {score}/10\n"
              f"     {lead['name']}\n"
              f"     👍 {likes_str}  |  💬 {talking_str} talking\n"
              f"     🔗 {lead['url']}")


if __name__ == '__main__':
    main()
