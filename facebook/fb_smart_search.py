#!/usr/bin/env python3
"""Smart Facebook lead search using SerpAPI + curated query bank.
Uses all 60 queries from search_queries.md, categorized by intent.
Filters duplicates via dedupe.py central dedup system.

Usage:
  python3 fb_smart_search.py --category beauty --limit 10
  python3 fb_smart_search.py --category no_website --limit 15
  python3 fb_smart_search.py --category fcommerce --limit 20
  python3 fb_smart_search.py --all --limit 5
  python3 fb_smart_search.py --keyword "restaurant Dhaka" --limit 10
"""
import json
import os
import sys
import time

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')
SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')

QUERY_BANK = {
    "no_website": [
        '"no website" "business" Bangladesh',
        '"call us at" "shop" "no website"',
        '"contact us on WhatsApp" "business page" Bangladesh',
        '"DM to order" "no website"',
        '"home delivery only" "page" Bangladesh 2026',
        '"we don\'t have a website" "business"',
        '"order via message" "shop" Bangladesh',
        '"only on Facebook" "business" Dhaka',
        '"no online store" "contact us" Bangladesh',
        '"call for price" "business" "no website"',
    ],
    "beauty": [
        '"beauty parlor" "Dhaka" "products"',
        '"cosmetics shop" "Bangladesh" "price list"',
        '"skincare products" "home delivery" Bangladesh',
        '"beauty products wholesale" Bangladesh',
        '"salon products" "order now" Bangladesh',
        '"makeup store" "Dhaka" "cash on delivery"',
        '"beauty boutique" "Bangladesh" "new collection"',
        '"organic skincare" "Bangladesh" "shop"',
    ],
    "erp_automation": [
        '"manual accounting" "business" Bangladesh',
        '"inventory management" "problems" Bangladesh',
        '"excel based" "business" "Bangladesh"',
        '"looking for ERP" "Bangladesh" small business',
        '"automate" "business processes" Bangladesh',
        '"struggling with" "order management" Bangladesh',
        '"paper based" "records" "business" Bangladesh',
    ],
    "general_sme": [
        '"small business" "Bangladesh" "growing"',
        '"startup" "Dhaka" "entrepreneur"',
        '"manufacturing" "Bangladesh" "SME"',
        '"retail shop" "Bangladesh" "business"',
        '"wholesale" "supplier" "Bangladesh"',
    ],
    "fcommerce": [
        '"DM to order" "price" Bangladesh',
        '"inbox to order" "delivery" Bangladesh',
        '"comment price" "product" Bangladesh',
        '"message us to order" Bangladesh',
        '"call to order" "home delivery" Bangladesh',
        '"cash on delivery" "DM" Bangladesh',
        '"price list" "new collection" "order"',
        '"WhatsApp" "order" "catalog" Bangladesh',
        '"no website" "selling" "Facebook" Bangladesh',
        '"only on Facebook" "shop" "Bangladesh"',
        '"order via inbox" "Dhaka"',
        '"send message to buy" Bangladesh',
        '"contact number" "order now" Bangladesh',
        '"WhatsApp me to order" Bangladesh',
        '"we deliver" "contact us" Bangladesh',
    ],
    "industry_commerce": [
        '"fashion" "DM to order" Bangladesh',
        '"cosmetics" "inbox to order" Dhaka',
        '"jewelry" "WhatsApp order" Bangladesh',
        '"gadgets" "electronic" "cash on delivery" Dhaka',
        '"baby products" "home delivery" Bangladesh',
        '"perfume brand" "order" "delivery" Bangladesh',
        '"bags accessories" "DM" Bangladesh',
        '"home decor" "inbox" "order" Dhaka',
        '"organic skincare" "order now" Bangladesh',
        '"grocery" "home delivery" "order" Dhaka',
        '"footwear" "cash on delivery" Bangladesh',
        '"toys" "order" "Facebook page" Bangladesh',
        '"phone accessories" "delivery" Bangladesh',
        '"dress" "new collection" "order" Bangladesh',
        '"kitchen items" "home delivery" Bangladesh',
    ],
}

KB_PRODUCT_MAP = {
    "no_website":        "Quick Website Package",
    "beauty":            "Quick Website Package",
    "fcommerce":         "Quick Website Package",
    "industry_commerce": "Quick Website Package",
    "erp_automation":    "ExecERP / ExecMate EOS",
    "general_sme":       "Quick Website Package",
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


def clean_url(url):
    """Normalize and clean a Facebook URL to canonical form."""
    from dedupe import normalize_fb_url
    norm = normalize_fb_url(url)
    if norm:
        return 'https://www.' + norm
    return url


def extract_slug(url):
    """Extract the page slug from a Facebook URL."""
    from dedupe import normalize_fb_url
    norm = normalize_fb_url(url)
    if norm and norm.startswith('facebook.com/'):
        return norm.split('facebook.com/')[1].split('/')[0]
    return None


def is_valid_slug(slug):
    """Validate a Facebook page slug."""
    from dedupe import BANNED_SLUGS
    if not slug:
        return False
    if slug.lower() in BANNED_SLUGS:
        return False
    if not any(c.isalpha() for c in slug):
        return False
    if len(slug) < 3:
        return False
    return True


def search_serpapi_facebook(query, limit=10):
    """Search Google for Facebook page URLs.
    Tries Serper.dev first (if SERPER_API_KEY set), falls back to DuckDuckGo.
    Filters and returns clean canonical Facebook page URLs.
    """
    full_query = f'{query} site:facebook.com -groups -events -marketplace'

    if SERPER_API_KEY:
        raw = search_serper(full_query, limit)
        urls = []
        seen = set()
        for item in raw:
            url = item.get('link', '')
            if not url:
                continue
            clean = clean_url(url)
            slug = extract_slug(clean)
            if not is_valid_slug(slug):
                continue
            if clean in seen:
                continue
            seen.add(clean)
            urls.append(clean)
            if len(urls) >= limit:
                break
        return urls

    # DuckDuckGo fallback
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from google_search import search_serpapi as ddg_search
    raw = ddg_search(query, limit=limit)
    return [u for u in raw if 'facebook.com' in u][:limit]


def search_category(category, limit=10):
    """Run all queries for a category, return deduplicated URLs.
    Uses dedupe.py filter_new_urls() to exclude already-seen pages.
    Returns list of {url, query, category, kb_product}.
    """
    from dedupe import filter_new_urls

    queries = QUERY_BANK.get(category, [])
    all_urls = []
    seen_in_batch = set()

    for query in queries:
        print(f"  [search] {query[:70]}...")
        urls = search_serpapi_facebook(query, limit=5)
        for url in urls:
            from dedupe import normalize_fb_url
            norm = normalize_fb_url(url)
            if norm not in seen_in_batch:
                seen_in_batch.add(norm)
                all_urls.append({
                    'url': url,
                    'query': query,
                    'category': category,
                    'kb_product': KB_PRODUCT_MAP.get(category, 'General'),
                })
        time.sleep(0.5)

    new_urls_list = filter_new_urls([r['url'] for r in all_urls])
    new_set = set(new_urls_list)
    filtered = [r for r in all_urls if r['url'] in new_set]

    print(f"  [search] {category}: {len(all_urls)} found, {len(filtered)} new")
    return filtered[:limit]


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description='Smart Facebook lead search using SerpAPI + 60 curated queries'
    )
    parser.add_argument(
        '--category',
        choices=list(QUERY_BANK.keys()) + ['all'],
        help='Query category to search'
    )
    parser.add_argument(
        '--keyword', type=str,
        help='Custom keyword search (bypasses query bank)'
    )
    parser.add_argument(
        '--all', action='store_true', dest='run_all',
        help='Run all categories'
    )
    parser.add_argument(
        '--limit', type=int, default=10,
        help='Max results per category (default: 10)'
    )
    args = parser.parse_args()

    if not SERPAPI_KEY and not SERPER_API_KEY:
        print("ERROR: SERPAPI_KEY or SERPER_API_KEY not set. Run: source ~/.zshrc")
        sys.exit(1)

    results = []
    if args.keyword:
        urls = search_serpapi_facebook(
            f'"{args.keyword}" site:facebook.com -groups -events',
            args.limit,
        )
        results = [
            {'url': u, 'category': 'custom', 'kb_product': 'General'}
            for u in urls
        ]
    elif args.run_all or not args.category:
        for cat in QUERY_BANK:
            results.extend(search_category(cat, limit=args.limit))
    elif args.category == 'all':
        for cat in QUERY_BANK:
            results.extend(search_category(cat, limit=args.limit))
    else:
        results = search_category(args.category, args.limit)

    print(f"\n[search] Total new URLs found: {len(results)}")
    for r in results:
        print(f"  [{r['category']}] {r['url']}")

    out_file = os.path.join(
        os.path.dirname(__file__), '..', 'collected_leads', 'pending_urls.json'
    )
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"[search] Saved {len(results)} URLs to pending_urls.json")
    print(f"[search] Pipe into fb_pipeline or apify_facebook.py to scrape")


if __name__ == '__main__':
    main()
