#!/usr/bin/env python3
"""Central deduplication for Skarbol lead gen system.
Single source of truth for all seen Facebook page URLs.

All scripts should import from here instead of maintaining
their own tracking systems.
"""
import csv
import os
import re

LEADS_DIR = os.path.join(os.path.dirname(__file__), 'collected_leads')
DISCOVERED_FILE = os.path.join(LEADS_DIR, 'discovered_urls.txt')

CSV_SOURCES = [
    (os.path.join(LEADS_DIR, 'leads.csv'), 'page_url'),
    (os.path.join(LEADS_DIR, 'facebook_leads.csv'), 'url'),
    (os.path.join(LEADS_DIR, 'fcommerce_leads.csv'), 'page_url'),
    (os.path.join(LEADS_DIR, 'maps_leads.csv'), 'maps_url'),
]

BANNED_SLUGS = {
    'login', 'signup', 'help', 'about', 'home', 'watch',
    'gaming', 'marketplace', 'pages', 'groups', 'events', 'hashtag',
    'media', 'photos', 'videos', 'posts', 'stories', 'reels', 'live',
}


def normalize_fb_url(url):
    """Normalize Facebook URL to canonical slug for comparison.
    Handles: m.facebook.com, www.facebook.com, facebook.com
    Strips: query params, fragments, trailing slashes, locale params
    Returns: lowercase slug like 'facebook.com/pagename'
    """
    if not url:
        return ''
    url = url.strip().lower()
    # Normalize subdomain (m.facebook.com, www.facebook.com -> facebook.com)
    url = re.sub(r'https?://(m\.|www\.|web\.)?facebook\.com', 'facebook.com', url)
    # Remove query params and fragments
    url = url.split('?')[0].split('#')[0]
    # Remove trailing slash
    url = url.rstrip('/')
    # Remove /posts/, /photos/, /videos/, etc — keep only page path
    url = re.sub(r'/(posts|photos|videos|about|reviews|events|reels|shorts)/.*$', '', url)
    return url


def load_all_seen_urls():
    """Load ALL previously seen Facebook URLs from every source.
    Returns a set of normalized slugs.
    """
    seen = set()

    # Load from discovered_urls.txt
    if os.path.exists(DISCOVERED_FILE):
        with open(DISCOVERED_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                u = line.strip()
                if u:
                    seen.add(normalize_fb_url(u))

    # Load from all CSV files
    for csv_path, url_col in CSV_SOURCES:
        if not os.path.exists(csv_path):
            continue
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u = (row.get(url_col) or '').strip()
                    if u:
                        seen.add(normalize_fb_url(u))
        except Exception as e:
            print(f"  [dedupe] Warning: could not read {csv_path}: {e}")

    return seen


def is_duplicate(url, seen=None):
    """Check if a Facebook URL has already been seen.
    Accepts optional pre-loaded seen set for efficiency.
    """
    if seen is None:
        seen = load_all_seen_urls()
    normalized = normalize_fb_url(url)
    return normalized in seen


def mark_url_seen(url):
    """Record a URL in the discovered_urls.txt tracking file.
    Also ensures it exists in at least one CSV source.
    """
    os.makedirs(os.path.dirname(DISCOVERED_FILE), exist_ok=True)
    normalized = normalize_fb_url(url)
    if not normalized:
        return

    # Read existing to avoid duplicate lines
    existing = set()
    if os.path.exists(DISCOVERED_FILE):
        with open(DISCOVERED_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    existing.add(normalize_fb_url(stripped))

    if normalized not in existing:
        with open(DISCOVERED_FILE, 'a', encoding='utf-8') as f:
            f.write(url.strip() + '\n')


def is_valid_facebook_page(url):
    """Validate that a URL is a real Facebook page (not a group, event, etc.)."""
    url = url.rstrip('/')
    if 'facebook.com' not in url:
        return False

    # Normalize mobile URLs
    url = url.replace('m.facebook.com', 'www.facebook.com')

    # Skip known non-page patterns
    skip_patterns = [
        '/groups/', '/events/', '/marketplace/',
        '/story.php', '/photo.php', '/video.php',
        '/profile.php', '/messages/', '/watch/',
        '/posts/', '/reel/', '/share/', '/photos/',
    ]
    for skip in skip_patterns:
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

    # Check against banned slugs
    if slug.lower() in BANNED_SLUGS:
        return False

    return True


def deduplicate_csv(csv_path, url_col, dry_run=False):
    """Scan a CSV file and remove duplicate Facebook URLs.
    Returns (removed_count, kept_count).
    """
    if not os.path.exists(csv_path):
        return 0, 0

    seen = set()
    unique_rows = []
    removed = 0
    kept = 0

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            u = (row.get(url_col) or '').strip()
            normalized = normalize_fb_url(u) if u else ''
            if normalized and normalized in seen:
                removed += 1
                continue
            if normalized:
                seen.add(normalized)
            unique_rows.append(row)
            kept += 1

    if not dry_run and removed > 0:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_rows)

    return removed, kept


def filter_new_urls(urls):
    """Given a list of URLs, return only those not yet seen
    in any tracking source. Normalizes and checks centrally.
    """
    seen = load_all_seen_urls()
    return [u for u in urls if not is_duplicate(u, seen)]


def main():
    """CLI: inspect duplicates or backfill CSV files."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Central deduplication for Skarbol lead gen'
    )
    parser.add_argument(
        '--check', action='store_true',
        help='Check all sources and report duplicate stats'
    )
    parser.add_argument(
        '--dedup-csv', nargs=2, metavar=('CSV_PATH', 'URL_COL'),
        help='Deduplicate a specific CSV file (use --no-dry-run to write)'
    )
    parser.add_argument(
        '--no-dry-run', action='store_true',
        help='Actually write deduplication changes'
    )
    args = parser.parse_args()

    if args.check:
        print("Loading all seen URLs across all sources...")
        seen = load_all_seen_urls()
        print(f"  Total unique normalized URLs: {len(seen)}")

        for csv_path, url_col in CSV_SOURCES:
            if not os.path.exists(csv_path):
                print(f"  {os.path.basename(csv_path)}: NOT FOUND")
                continue
            total = 0
            dups = 0
            file_seen = set()
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    u = (row.get(url_col) or '').strip()
                    if u:
                        total += 1
                        n = normalize_fb_url(u)
                        if n in file_seen:
                            dups += 1
                        file_seen.add(n)
            print(f"  {os.path.basename(csv_path)} ({url_col}): {total} rows, {dups} internal duplicates")

    if args.dedup_csv:
        csv_path, url_col = args.dedup_csv
        removed, kept = deduplicate_csv(csv_path, url_col, dry_run=not args.no_dry_run)
        action = "Would remove" if not args.no_dry_run else "Removed"
        print(f"  {action} {removed} duplicate(s) from {csv_path} ({kept} kept)")

    if not args.check and not args.dedup_csv:
        parser.print_help()


if __name__ == '__main__':
    main()
