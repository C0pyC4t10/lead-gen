# fb_pipeline.py — Full lead gen pipeline: Search -> Scrape -> Qualify -> Save
# Skarbol Tech Lead Generation System

import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from facebook.fb_scraper import scrape_facebook_page, save_to_server
from facebook.fb_smart_search import search_category
from facebook.fb_scorer import score_and_update

def run_pipeline(query=None, max_urls=10, category=None):
    print("=" * 60)
    print("SKARBOL TECH LEAD GENERATION PIPELINE")
    print("=" * 60)

    # Determine search method
    if category:
        print(f"\nStep 1: Smart search — category={category}, limit={max_urls}")
        print("-" * 40)
        url_results = search_category(category, limit=max_urls)
    elif query:
        print(f"\nStep 1: Searching for: {query}")
        print("-" * 40)
        from facebook.fb_smart_search import search_serper
        raw = search_serper(f'"{query}" site:facebook.com -groups -events', max_urls)
        url_results = [{'url': r['link'], 'category': 'custom', 'kb_product': 'General'}
                      for r in raw if 'facebook.com/' in r.get('link', '')]
    else:
        print("[pipeline] No query or category provided.")
        return []

    urls = [r['url'] for r in url_results]

    if not urls:
        print("[pipeline] No new URLs found after deduplication.")
        return []

    results = []
    for i, url in enumerate(urls):
        print(f"\n--- Page {i + 1}/{len(urls)}: {url} ---")

        lead = scrape_facebook_page(url)
        if not lead:
            print(f"  ✗ Failed to scrape {url}")
            continue

        # KB-aligned scoring
        lead = score_and_update(lead)
        score = int(lead.get('qualification_score', 0))
        if score < 5:
            print(f"  ✗ Score {score}/10 — skipped")
            continue

        ok = save_to_server(lead)
        if ok:
            results.append(lead)

        if i < len(urls) - 1:
            delay = 3
            print(f"  Waiting {delay}s before next request...")
            time.sleep(delay)

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Search query:       {query or category or 'unknown'}")
    print(f"  URLs found:         {len(urls)}")
    print(f"  Pages scraped:      {len([r for r in results if r])}")
    print(f"  Leads saved:        {len(results)}")
    phones_count = sum(1 for r in results if r.get('phone'))
    emails_count = sum(1 for r in results if r.get('email'))
    print(f"  With phone:         {phones_count}")
    print(f"  With email:         {emails_count}")
    avg_score = sum(int(r.get('qualification_score', 0)) for r in results if r.get('qualification_score')) / max(len(results), 1)
    print(f"  Avg score:          {avg_score:.1f}")
    if results:
        print("\n  ── Found Pages ──")
        for r in results:
            name = r.get('business_name', '?')
            url = r.get('page_url', '?')
            phone = r.get('phone', '-') or '-'
            cat = r.get('category', '-') or '-'
            score = r.get('qualification_score', '?')
            print(f"  • {name}")
            print(f"    URL:   {url}")
            print(f"    Phone: {phone}  Category: {cat}  Score: {score}")
    print("=" * 60)

    return results

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('query', nargs='?', help='Search keyword')
    parser.add_argument('--category', choices=['beauty', 'fcommerce', 'no_website', 'erp_automation', 'general_sme', 'all'])
    parser.add_argument('--limit', type=int, default=10)
    args = parser.parse_args()

    if not args.query and not args.category:
        print("Usage: python3 fb_pipeline.py 'beauty parlor Dhaka'")
        print("       python3 fb_pipeline.py --category beauty --limit 10")
        sys.exit(1)

    run_pipeline(query=args.query, max_urls=args.limit, category=args.category)

if __name__ == '__main__':
    main()
