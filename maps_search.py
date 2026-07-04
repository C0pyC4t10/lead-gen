import os, sys, csv, argparse, time
from datetime import datetime
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'demo'))
from category_lib import classify_category, detect_trojan_horse

CSV_DIR = os.path.join(os.path.dirname(__file__), 'collected_leads')
CSV_PATH = os.path.join(CSV_DIR, 'maps_leads.csv')

CSV_COLUMNS = [
    'date', 'source', 'name', 'address', 'phone', 'website', 'has_website',
    'rating', 'reviews', 'maps_url', 'place_id', 'qualification_score',
    'status', 'notes', 'open_state', 'hours_text',
]

TARGET_VERTICALS = [
    'restaurant', 'cafe', 'bakery', 'food',
    'beauty', 'salon', 'parlor', 'spa', 'cosmetics',
    'retail', 'store', 'shop', 'fashion', 'boutique', 'grocery',
    'education', 'school', 'college', 'training', 'academy',
    'healthcare', 'hospital', 'clinic', 'diagnostic', 'lab', 'medical',
    'pharmacy', 'drug', 'medicine',
    'fitness', 'gym', 'yoga',
    'automotive', 'automobile', 'car', 'workshop', 'mechanic',
    'manufacturing', 'factory', 'garment', 'textile', 'industry',
    'agriculture', 'farm', 'agro', 'dairy', 'poultry',
    'hotel', 'resort', 'motel', 'guest house',
    'real estate', 'property', 'apartment', 'construction',
    'services', 'electrician', 'plumber', 'cleaning', 'tailor', 'repair',
    "footwear", "shoe", "sneaker", "sandal",
    "baby", "kids", "toy", "infant",
    "gym", "fitness", "yoga", "wellness",
    "real estate", "property", "apartment",
    "automobile", "car", "workshop", "garage",
    "hotel", "resort", "hospitality",
]


def score_lead(has_website, has_phone, rating, reviews, name):
    score = 5
    if not has_website:
        score += 1
    if has_phone:
        score += 1
    if rating >= 4.0:
        score += 1
    if reviews >= 10:
        score += 1
    name_lower = name.lower()
    for v in TARGET_VERTICALS:
        if v in name_lower:
            score += 1
            break
    return max(1, min(10, score))


def ensure_csv():
    os.makedirs(CSV_DIR, exist_ok=True)
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
    else:
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            existing_cols = [c.strip() for c in f.readline().strip().split(',')]
        if existing_cols != CSV_COLUMNS:
            rows = []
            with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
                next(f)
                for line in f:
                    vals = [v.strip() for v in line.strip().split(',')]
                    row = {}
                    for i, col in enumerate(existing_cols):
                        if i < len(vals):
                            row[col] = vals[i]
                        else:
                            row[col] = ''
                    rows.append(row)
            with open(CSV_PATH, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)


def load_place_ids():
    ids = set()
    if not os.path.exists(CSV_PATH):
        return ids
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row.get('place_id', '').strip()
            if pid:
                ids.add(pid)
    return ids


LEAD_GEN_API = 'http://127.0.0.1:8800/api/lead'


def send_to_dashboard(lead):
    raw_cat = lead.get('notes', '').replace('Keyword: ', '').split(',')[0].strip()
    canonical = classify_category(raw_cat)
    try:
        payload = {
            'page_url': lead.get('maps_url', ''),
            'business_name': lead.get('name', ''),
            'category': canonical,
            'phone': lead.get('phone', ''),
            'address': lead.get('address', ''),
            'website': lead.get('website', ''),
            'has_website': lead.get('has_website', 'false'),
            'followers': '',
            'platform': 'google_maps',
            'qualification_score': lead.get('qualification_score', '5'),
            'status': 'new',
            'notes': lead.get('notes', ''),
            'open_state': lead.get('open_state', ''),
            'hours_text': lead.get('hours_text', ''),
        }
        resp = requests.post(LEAD_GEN_API, json=payload, timeout=10)
        result = resp.json()
        if result.get('status') == 'duplicate':
            return 'duplicate'
        return 'sent'
    except requests.ConnectionError:
        print("  ⚠️ Lead gen server not running. Skipping dashboard notification.", flush=True)
        return 'server_offline'
    except Exception as e:
        print(f"  ⚠️ Dashboard notification failed: {e}", flush=True)
        return 'error'


def save_results(results):
    ensure_csv()
    existing = load_place_ids()
    new_count = 0
    sent_count = 0
    with open(CSV_PATH, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        for r in results:
            pid = r.get('place_id', '')
            if pid and pid in existing:
                continue
            writer.writerow(r)
            if pid:
                existing.add(pid)
            new_count += 1
            result = send_to_dashboard(r)
            if result == 'sent':
                sent_count += 1
    if sent_count:
        print(f"  📬 Sent {sent_count} to lead gen dashboard", flush=True)
    return new_count


def search_serpapi(keyword, location, limit=20, api_key=None):
    results = []
    params = {
        'engine': 'google_maps',
        'q': f"{keyword} in {location}",
        'api_key': api_key,
        'num': min(limit, 20),
    }

    while len(results) < limit:
        resp = requests.get('https://serpapi.com/search.json', params=params, timeout=20)
        data = resp.json()

        if 'error' in data:
            print(f"SerpAPI error: {data['error']}")
            break

        items = data.get('local_results') or data.get('place_results')
        if not items:
            break

        if isinstance(items, dict):
            items = [items]

        for place in items:
            name = place.get('title', '')
            if not name:
                continue
            address = place.get('address', '') or ''
            phone = place.get('phone', '') or ''
            website = place.get('website', '') or ''
            has_website = bool(website)
            rating = place.get('rating', 0) or 0
            reviews = place.get('reviews', 0) or 0
            place_id = place.get('place_id', '') or ''
            maps_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}" if place_id else ''
            hours_data = place.get('hours', {})
            open_state = 'Unknown'
            hours_text = ''
            if isinstance(hours_data, dict):
                open_state = hours_data.get('open_state', '') or ''
                weekday_text = hours_data.get('weekday_text', []) or []
                if weekday_text:
                    today_idx = datetime.now().weekday()
                    today_name = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][today_idx]
                    for line in weekday_text:
                        if line.lower().startswith(today_name.lower()):
                            hours_text = line.split(':', 1)[-1].strip() if ':' in line else ''
                            break
                    if not hours_text:
                        hours_text = weekday_text[0].split(':', 1)[-1].strip() if ':' in weekday_text[0] else ''
            elif isinstance(hours_data, str):
                open_state = hours_data
            if not open_state:
                open_state = 'Unknown'

            row = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'source': 'serpapi_maps',
                'name': name,
                'address': address,
                'phone': phone,
                'website': website,
                'has_website': 'true' if has_website else 'false',
                'rating': str(rating),
                'reviews': str(reviews),
                'maps_url': maps_url,
                'place_id': place_id,
                'open_state': open_state,
                'hours_text': hours_text,
                'qualification_score': str(score_lead(has_website, bool(phone), rating, reviews, name)),
                'status': 'new',
                'notes': f'Keyword: {keyword}, Location: {location}',
            }

            trojan = detect_trojan_horse(name, keyword)
            if trojan:
                row['notes'] += f" | 🎯 Trojan: {trojan['product']} ({trojan['entry']})"
            results.append(row)
            print(f"FOUND: {name} | Score: {row['qualification_score']} | Website: {row['has_website']}")
            if len(results) >= limit:
                break

        pagination = data.get('serpapi_pagination') or {}
        next_token = pagination.get('next_page_token')
        if next_token and len(results) < limit:
            params['next_page_token'] = next_token
            time.sleep(1)
        else:
            break

    return results


def main():
    parser = argparse.ArgumentParser(description='Search Google Maps for businesses via SerpAPI')
    parser.add_argument('keyword', help='Business type to search (e.g. "beauty parlor")')
    parser.add_argument('--location', default='Dhaka, Bangladesh', help='City or area to search in')
    parser.add_argument('--limit', type=int, default=20, help='Max results (default 20)')
    args = parser.parse_args()

    api_key = os.environ.get('SERPAPI_KEY')
    if not api_key:
        print("ERROR: SERPAPI_KEY environment variable not set.")
        print("Get a key at https://serpapi.com and export SERPAPI_KEY=your_key")
        sys.exit(1)

    print(f"Searching: \"{args.keyword}\" in {args.location} (limit: {args.limit})")

    results = search_serpapi(args.keyword, args.location, args.limit, api_key)

    if not results:
        print("No results found.")
        return

    saved = save_results(results)
    print(f"\n{'='*50}")
    print(f"Total found: {len(results)}")
    print(f"Newly saved: {saved}")
    print(f"CSV: {CSV_PATH}")

    print(f"\n--- Top Results ---")
    sorted_results = sorted(
        results, key=lambda r: int(r.get('qualification_score', 0) or 0), reverse=True
    )
    for r in sorted_results[:10]:
        score = r.get('qualification_score', '?')
        phone = r.get('phone', '') or '—'
        has_web = r.get('has_website') == 'true'
        web_status = '✅ Has website' if has_web else '❌ No website'
        website_url = r.get('website', '') or ''
        maps_url = r.get('maps_url', '') or ''
        print(f"  [{score}/10] {r['name']} | {web_status} | {phone}")
        print(f"    🗺️ {maps_url}")
        if website_url:
            print(f"    🌐 {website_url}")


if __name__ == '__main__':
    main()
