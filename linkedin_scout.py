#!/usr/bin/env python3
"""LinkedIn lead finder for Skarbol Tech using Google Dorks + SerpAPI.
Finds decision-makers aligned with Skarbol KB products.

Run with: source ~/.zshrc && python3 linkedin_scout.py

Usage:
  python3 linkedin_scout.py                     # all KB categories
  python3 linkedin_scout.py "CTO Dhaka"         # custom keyword
  python3 linkedin_scout.py --category medical  # specific category
  python3 linkedin_scout.py --limit 8           # results per query
  python3 linkedin_scout.py --notify            # send to Telegram
"""

import os, sys, csv, argparse, time
from datetime import datetime
import requests

LINKEDIN_LEADS_CSV = os.path.join(os.path.dirname(__file__), 'collected_leads', datetime.now().strftime('%Y-%m-%d'), 'linkedin_leads.csv')

SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = "-1004334910291"
TELEGRAM_THREAD_ID = 355
MIN_SCORE = 6.5

BD_LOCATIONS = ['Dhaka', 'Bangladesh', 'Chittagong', 'Sylhet', 'Rajshahi',
                'Khulna', 'Comilla', 'Mymensingh', 'Gazipur', 'Narayanganj',
                'BD', 'Bangladeshi']

BD_ALLOWED_DOMAINS = ['www.linkedin.com', 'bd.linkedin.com', 'linkedin.com']

KB_QUERY_MAP = {
    "cto_it": 'site:linkedin.com/in "CTO" OR "IT Director" OR "Head of IT" "Dhaka" OR "Bangladesh" -site:uk.linkedin.com -site:in.linkedin.com -site:ae.linkedin.com',
    "school": 'site:linkedin.com/in "principal" OR "school director" "Bangladesh" school OR college -site:in.linkedin.com',
    "medical": 'site:linkedin.com/in "clinic manager" OR "hospital admin" OR "diagnostic" "Bangladesh" -site:in.linkedin.com',
    "operations": 'site:linkedin.com/in "operations manager" OR "factory manager" "Bangladesh" manufacturing -site:in.linkedin.com',
    "owner": 'site:linkedin.com/in "founder" OR "owner" ("Dhaka" OR "Bangladesh") (restaurant OR salon OR shop) -site:in.linkedin.com -site:uk.linkedin.com -site:ae.linkedin.com -site:sa.linkedin.com',
    "freelancer_client": 'site:linkedin.com/in "project manager" OR "hiring manager" "software" "Bangladesh" -site:in.linkedin.com',
}

PRODUCT_MAP = {
    "ExecMate EOS":     ["cto", "it director", "head of it", "technology", "digital transformation", "chief digital"],
    "Smart Campus":     ["principal", "school", "college", "education", "campus", "academic"],
    "MediLab LIMS":     ["clinic", "diagnostic", "hospital", "laboratory", "medical", "lims"],
    "ExecERP":          ["operations", "factory", "manufacturing", "supply chain", "logistics", "inventory"],
    "CattleSync":       ["farm", "livestock", "agriculture", "cattle", "poultry", "agro"],
    "Quick Website":    ["restaurant", "salon", "shop", "owner", "founder", "entrepreneur", "small business"],
    "GuardianGuard":    ["it security", "device management", "security manager", "network"],
    "Freelancer Lead":  ["project manager", "hiring", "software project", "tech", "startup"],
}


def search_serper(query, limit=10):
    if not SERPER_API_KEY:
        return []
    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json',
    }
    payload = {
        'q': query,
        'num': limit,
        'gl': 'bd',
        'hl': 'en',
    }
    try:
        resp = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            json=payload,
            timeout=15,
        )
        data = resp.json()
        results = []
        for item in data.get('organic', []):
            results.append({
                'link': item.get('link', ''),
                'title': item.get('title', ''),
                'snippet': item.get('snippet', ''),
            })
        return results
    except Exception as e:
        print(f"  [serper] Error: {e}")
        return []


def search_serpapi_linkedin(query, limit, api_key):
    results = []

    # Try Serper first
    if SERPER_API_KEY:
        raw = search_serper(query, limit)
        for item in raw:
            url = item.get('link', '')
            if 'linkedin.com/in/' not in url:
                continue
            from urllib.parse import urlparse
            parsed_domain = urlparse(url).netloc
            country_subdomain = parsed_domain.split('.linkedin.com')[0]
            if country_subdomain not in ('www', 'bd', 'linkedin'):
                continue

            title = item.get('title', '')
            snippet = item.get('snippet', '')

            name = title.split(' - ')[0].strip() if ' - ' in title else title.split('|')[0].strip()
            headline = title.split(' - ')[1].replace('| LinkedIn', '').strip() if ' - ' in title else ''

            company = headline.split(' at ')[-1].strip() if ' at ' in headline else ''
            combined_text = snippet + ' ' + title
            location = next((w for w in BD_LOCATIONS if w in combined_text), '')
            if not location:
                continue

            results.append({
                'name': name,
                'headline': headline,
                'company': company,
                'location': location,
                'url': url,
                'snippet': snippet,
                'found_at': datetime.now().isoformat(),
            })

        if results:
            return results

    # Fallback to SerpAPI
    params = {
        'engine': 'google',
        'q': query,
        'api_key': api_key,
        'num': limit,
        'hl': 'en',
    }

    try:
        resp = requests.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()
    except Exception as e:
        print(f"  [linkedin] Request error: {e}")
        return results

    if 'error' in data:
        print(f"  [linkedin] SerpAPI error: {data['error']}")
        return results

    for item in data.get('organic_results', []):
        url = item.get('link', '')
        if 'linkedin.com/in/' not in url:
            continue

        from urllib.parse import urlparse
        parsed_domain = urlparse(url).netloc
        country_subdomain = parsed_domain.split('.linkedin.com')[0]
        if country_subdomain not in ('www', 'bd', 'linkedin'):
            continue

        title = item.get('title', '')
        snippet = item.get('snippet', '')

        name = title.split(' - ')[0].strip() if ' - ' in title else title.split('|')[0].strip()
        headline = title.split(' - ')[1].replace('| LinkedIn', '').strip() if ' - ' in title else ''

        company = headline.split(' at ')[-1].strip() if ' at ' in headline else ''
        combined_text = snippet + ' ' + title
        location = next((w for w in BD_LOCATIONS if w in combined_text), '')

        if not location:
            continue

        results.append({
            'name': name,
            'headline': headline,
            'company': company,
            'location': location,
            'url': url,
            'snippet': snippet,
            'found_at': datetime.now().isoformat(),
        })

    return results


def score_linkedin_lead(lead):
    text = (lead['headline'] + ' ' + lead['company']).lower()
    matched_products = []
    for product, keywords in PRODUCT_MAP.items():
        if any(kw in text for kw in keywords):
            matched_products.append(product)

    title_score = min(len(matched_products) * 2.5, 8.0)
    location_bonus = 2.0 if lead.get('location') else 0.0
    # No location = already filtered in search, but safety net:
    if not lead.get('location'):
        lead['kb_score'] = 0.0
        lead['matched_products'] = []
        lead['kb_category'] = 'Filtered'
        return lead
    has_company_bonus = 0.5 if lead.get('company') else 0.0
    final_score = min(title_score + location_bonus + has_company_bonus, 10.0)

    lead['kb_score'] = round(final_score, 1)
    lead['matched_products'] = matched_products
    lead['kb_category'] = matched_products[0] if matched_products else 'General'
    return lead


def save_to_csv(leads):
    os.makedirs(os.path.dirname(LINKEDIN_LEADS_CSV), exist_ok=True)

    fieldnames = ['date', 'name', 'headline', 'company', 'location', 'url', 'kb_score', 'kb_category', 'matched_products', 'status', 'source']

    existing_urls = set()
    if os.path.exists(LINKEDIN_LEADS_CSV):
        with open(LINKEDIN_LEADS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get('url', '').strip()
                if url:
                    existing_urls.add(url)

    new_count = 0
    dup_count = 0
    rows_to_write = []
    for lead in leads:
        if lead['url'] in existing_urls:
            dup_count += 1
            continue
        rows_to_write.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'name': lead['name'],
            'headline': lead['headline'],
            'company': lead['company'],
            'location': lead['location'],
            'url': lead['url'],
            'kb_score': str(lead['kb_score']),
            'kb_category': lead['kb_category'],
            'matched_products': '|'.join(lead['matched_products']),
            'status': 'new',
            'source': 'linkedin_google_dork',
        })
        existing_urls.add(lead['url'])
        new_count += 1

    if not rows_to_write:
        return new_count, dup_count

    file_exists = os.path.exists(LINKEDIN_LEADS_CSV) and os.path.getsize(LINKEDIN_LEADS_CSV) > 0
    with open(LINKEDIN_LEADS_CSV, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows_to_write)

    return new_count, dup_count


def send_telegram_notification(leads):
    token = TELEGRAM_TOKEN
    if not token:
        print("  [linkedin] TELEGRAM_TOKEN not set, skipping notification")
        return

    for lead in leads:
        if lead['kb_score'] < MIN_SCORE:
            continue

        msg = (
            f"\U0001F3AF LinkedIn Lead \u2014 Score {lead['kb_score']}/10\n\n"
            f"\U0001F464 {lead['name']}\n"
            f"\U0001F4BC {lead['headline']}\n"
            f"\U0001F3E2 {lead['company'] or 'N/A'} | \U0001F4CD {lead['location'] or 'N/A'}\n"
            f"\U0001F3F7\U0000FE0F KB Match: {' · '.join(lead['matched_products']) or 'General'}\n"
            f"\U0001F517 {lead['url']}"
        )

        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "message_thread_id": TELEGRAM_THREAD_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            resp = requests.post(bot_url, json=payload, timeout=10)
            result = resp.json()
            if result.get('ok'):
                print(f"  [linkedin] Telegram notified: {lead['name']}")
            else:
                print(f"  [linkedin] Telegram API error: {result}")
        except Exception as e:
            print(f"  [linkedin] Telegram notification failed: {e}")


def main():
    api_key = os.environ.get('SERPAPI_KEY', '')
    if not api_key and not SERPER_API_KEY:
        print("ERROR: SERPAPI_KEY or SERPER_API_KEY environment variable not set.")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='LinkedIn lead finder for Skarbol Tech using Google Dorks + SerpAPI')
    parser.add_argument('--keyword', help='Custom search keyword')
    parser.add_argument('--category', choices=list(KB_QUERY_MAP.keys()) + ['all'], help='KB category to search')
    parser.add_argument('--limit', type=int, default=8, help='Results per query (default: 8)')
    parser.add_argument('--notify', action='store_true', help='Send results to Telegram')
    parser.add_argument('--min-score', type=float, default=MIN_SCORE, help=f'Minimum score threshold (default: {MIN_SCORE})')
    args = parser.parse_args()

    min_score = args.min_score

    queries_to_run = {}

    if args.keyword:
        queries_to_run = {"custom": f'site:linkedin.com/in "{args.keyword}" Bangladesh'}
    elif args.category and args.category != 'all':
        queries_to_run = {args.category: KB_QUERY_MAP[args.category]}
    else:
        queries_to_run = dict(KB_QUERY_MAP)

    total = 0
    saved = 0

    for cat, query in queries_to_run.items():
        print(f"[linkedin] Searching: [{cat}] {query}")
        results = search_serpapi_linkedin(query, args.limit, api_key)

        scored = [score_linkedin_lead(r) for r in results]
        filtered = [r for r in scored if r['kb_score'] >= min_score]

        for r in filtered:
            print(f"  [linkedin] {r['name']} | {r['headline']} | Score: {r['kb_score']}/10 | {r['company'] or 'N/A'}")
        if not filtered:
            print(f"  [linkedin] No qualifying profiles (min score: {min_score})")

        n, d = save_to_csv(filtered)
        total += len(filtered)
        saved += n
        if d > 0:
            print(f"  [linkedin] Skipped {d} duplicate(s)")

        if args.notify and filtered:
            send_telegram_notification(filtered)

        time.sleep(1)

    print(f"[linkedin] Done: {total} profiles found, {saved} saved (score >= {min_score})")


if __name__ == '__main__':
    main()
