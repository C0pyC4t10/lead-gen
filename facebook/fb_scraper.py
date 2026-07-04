import re, sys, time, json, os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, quote_plus, unquote
from datetime import datetime

SERVER_URL = "http://127.0.0.1:8800/api/lead"

DESKTOP_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)
MOBILE_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) '
    'Version/17.0 Mobile/15E148 Safari/604.1'
)

HEADERS_DESKTOP = {
    'User-Agent': DESKTOP_UA,
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}
HEADERS_MOBILE = {
    'User-Agent': MOBILE_UA,
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

CATEGORY_KEYWORDS = {
    'restaurant': ['restaurant', 'cafe', 'bakery', 'grill', 'pizza', 'biryani', 'catering', 'food', 'dining', 'coffee shop'],
    'beauty': ['beauty', 'parlor', 'salon', 'cosmetic', 'cosmetics', 'skincare', 'makeup', 'parlour', 'spa', 'massage', 'nail', 'barber', 'hair'],
    'pharmacy': ['pharmacy', 'drug', 'chemist', 'medicine', 'pharmaceutical'],
    'fitness': ['gym', 'fitness', 'yoga', 'zumba', 'workout', 'crossfit'],
    'automotive': ['auto', 'car', 'mechanic', 'garage', 'workshop', 'automobile', 'car wash', 'towing', 'spare parts'],
    'agriculture': ['farm', 'agriculture', 'agro', 'dairy', 'poultry', 'hatchery', 'feed', 'seed', 'fertilizer', 'nursery'],
    'hotel': ['hotel', 'resort', 'motel', 'guest house', 'lodging', 'accommodation', 'rest house'],
    'healthcare': ['hospital', 'hospitals', 'clinic', 'clinics', 'diagnostic', 'medical', 'doctor', 'dental', 'dentist', 'physiotherapy', 'lab', 'nursing'],
    'education': ['school', 'schools', 'college', 'colleges', 'university', 'coaching', 'tutorial', 'training', 'academy', 'institute', 'madrasa', 'kindergarten'],
    'manufacturing': ['manufacturing', 'factory', 'factories', 'garment', 'garments', 'textile', 'industry', 'wholesale', 'supplier', 'distributor', 'inventory', 'erp'],
    'realestate': ['real estate', 'property', 'apartment', 'flat', 'land', 'builder', 'developer', 'construction', 'realtor', 'broker'],
    'services': ['electrician', 'plumber', 'carpenter', 'painter', 'repair', 'maintenance', 'cleaning', 'laundry', 'tailor', 'tailoring', 'photography', 'event', 'logistics', 'delivery', 'courier', 'travel', 'consultant', 'it services', 'software', 'security'],
    'retail': ['store', 'shop', 'fashion', 'boutique', 'grocery', 'supermarket', 'electronics', 'furniture', 'clothing', 'jewelry', 'gadget', 'mobile'],
}

MAJOR_CITIES = ['dhaka', 'chattogram', 'khulna', 'sylhet', 'rajshahi', 'barisal', 'rangpur', 'mymensingh', 'narayanganj', 'gazipur']

def detect_category(text):
    text_lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for k in keywords:
            if re.search(r'\b' + re.escape(k) + r'\b', text_lower):
                return cat
    return 'general'

def extract_phones(text):
    phones = re.findall(r'(?:\+?880|0)1[3-9]\d{8}', text)
    unique = list(set(phones))
    formatted = []
    for p in unique:
        if p.startswith('01') and len(p) == 11:
            formatted.append('+880' + p[1:])
        elif p.startswith('+880') and len(p) == 14:
            formatted.append(p)
        elif p.startswith('880') and len(p) == 13:
            formatted.append('+' + p)
        else:
            formatted.append(p)
    return formatted

def extract_emails(text):
    emails = re.findall(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(?:\b|(?=[^a-zA-Z]))', text)
    exclude_domains = ['facebook.com', 'example.com', 'sentry.io', 'fb.com', 'localhost']
    filtered = [
        e for e in emails
        if not any(d in e.lower() for d in exclude_domains)
        and not e.startswith('@')
    ]
    seen = set()
    result = []
    for e in filtered:
        e_clean = e.rstrip('.')
        if e_clean not in seen:
            seen.add(e_clean)
            result.append(e_clean)
    return result

def extract_followers(text):
    patterns = [
        r'([\d,.]+)\s*(?:people\s+)?(?:like|follow|follower)s?',
        r'(?:like|follow|follower)s?\s*([\d,.]+)',
        r'([\d,.]+)\s*likes',
    ]
    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            raw = match.group(1).replace(',', '').replace('.', '')
            try:
                val = int(raw)
                if val < 100_000_000:
                    return str(val)
            except ValueError:
                pass
    return ''

def extract_json_ld(soup):
    data = {}
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            parsed = json.loads(script.string)
            if isinstance(parsed, dict):
                data.update(parsed)
            elif isinstance(parsed, list) and len(parsed) > 0:
                for item in parsed:
                    if isinstance(item, dict):
                        for k, v in item.items():
                            if v and k not in data:
                                data[k] = v
        except (json.JSONDecodeError, TypeError):
            continue

    result = {}
    if 'name' in data:
        result['name'] = data['name']
    if 'telephone' in data:
        result['phone'] = data['telephone']
    if 'email' in data:
        result['email'] = data['email']
    if 'address' in data and isinstance(data['address'], dict):
        addr_parts = []
        for key in ['streetAddress', 'addressLocality', 'addressRegion', 'postalCode', 'addressCountry']:
            if key in data['address']:
                addr_parts.append(str(data['address'][key]))
        if addr_parts:
            result['address'] = ', '.join(addr_parts)
    if 'url' in data and 'facebook' not in data.get('url', '').lower():
        result['website'] = data['url']
    return result

def extract_meta_tags(soup):
    result = {}
    for prop in ['og:title', 'og:description', 'og:url', 'og:site_name']:
        tag = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
        if tag and tag.get('content'):
            result[prop] = tag['content'].strip()
    return result

def extract_page_info(soup, text, headers_used):
    info = {}

    title_tag = soup.find('title')
    raw_title = title_tag.get_text(strip=True) if title_tag else ''
    raw_biz = re.sub(r'\s*\|\s*(Facebook|Dhaka|Bangladesh|Home)\s*', '', raw_title, flags=re.IGNORECASE).strip()
    info['business_name'] = raw_biz.split('\n')[0].strip() if raw_biz else ''

    info['phones'] = extract_phones(text)
    info['emails'] = extract_emails(text)
    info['followers'] = extract_followers(text)

    info['website'] = ''
    info['has_website'] = 'false'
    for a in soup.find_all('a', href=True):
        href = a['href']
        if 'l.facebook.com/l.php' in href:
            match = re.search(r'u=(https?://[^&]+)', href)
            if match:
                candidate = unquote(match.group(1))
                parsed = urlparse(candidate)
                exclude = ['facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com', 'youtube.com', 'tiktok.com']
                if not any(d in parsed.netloc for d in exclude):
                    info['website'] = candidate
                    info['has_website'] = 'true'
                    break

    addr_match = re.search(r'(?:Address|Location)[:\s]+([^\n\|]{10,120})', text, re.IGNORECASE)
    if addr_match:
        info['address'] = addr_match.group(1).strip()
    else:
        info['address'] = ''

    info['last_post'] = ''
    date_patterns = [
        r'(\d+)\s*(hour|day|week|minute|month|year)s?\s*ago',
        r'(?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
    ]
    for p in date_patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            info['last_post'] = match.group(0)
            break

    return info

def calculate_qualification_score(info):
    score = 5
    reasons = []

    if info.get('has_website') == 'false':
        score += 1
        reasons.append('no_website')

    if info.get('followers'):
        try:
            if int(info['followers']) < 10000:
                score += 1
                reasons.append('small_page')
        except ValueError:
            pass

    if info.get('last_post'):
        score += 1
        reasons.append('recent_posts')

    if info.get('phones'):
        score += 1
        reasons.append('has_phone')

    if info.get('emails'):
        score += 1
        reasons.append('has_email')

    if info.get('address'):
        score += 1
        reasons.append('has_address')
        text_lower = info['address'].lower()
        if any(city in text_lower for city in MAJOR_CITIES):
            score += 1
            reasons.append('major_city')

    if not info.get('phones') and not info.get('emails') and not info.get('whatsapp'):
        score -= 2
        reasons.append('no_contact_info')

    score = max(1, min(10, score))
    return score, reasons

def scrape_facebook_page(url):
    print(f"\n  Scraping: {url}")
    info = {}
    page_texts = []

    attempts = [
        ('desktop', HEADERS_DESKTOP, False),
        ('mobile', HEADERS_MOBILE, False),
        ('mobile m.facebook', HEADERS_MOBILE, True),
    ]

    for label, headers, use_mobile in attempts:
        target_url = url
        if use_mobile:
            parsed = urlparse(url)
            target_url = f"https://m.facebook.com{parsed.path}"
            if parsed.query:
                target_url += f'?{parsed.query}'
            target_url = target_url.rstrip('/') + '/about/'

        try:
            resp = requests.get(target_url, headers=headers, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            page_texts.append(text)

            if not info.get('business_name'):
                jsonld = extract_json_ld(soup)
                if jsonld.get('name'):
                    info['business_name'] = jsonld['name']
                if jsonld.get('phone'):
                    info['phones'] = list(set(info.get('phones', []) + [jsonld['phone']]))
                if jsonld.get('email'):
                    info['emails'] = list(set(info.get('emails', []) + [jsonld['email']]))
                if jsonld.get('address'):
                    info['address'] = jsonld['address']
                if jsonld.get('website') and not info.get('website'):
                    info['website'] = jsonld['website']
                    info['has_website'] = 'true'

            page_info = extract_page_info(soup, text, headers)
            if page_info.get('business_name') and not info.get('business_name'):
                info['business_name'] = page_info['business_name']
            if page_info.get('phones'):
                info['phones'] = list(set(info.get('phones', []) + page_info['phones']))
            if page_info.get('emails'):
                info['emails'] = list(set(info.get('emails', []) + page_info['emails']))
            if page_info.get('followers') and not info.get('followers'):
                info['followers'] = page_info['followers']
            if page_info.get('website') and not info.get('website'):
                info['website'] = page_info['website']
                info['has_website'] = 'true'
            if page_info.get('address') and not info.get('address'):
                info['address'] = page_info['address']
            if page_info.get('last_post') and not info.get('last_post'):
                info['last_post'] = page_info['last_post']

            meta = extract_meta_tags(soup)
            if not info.get('business_name'):
                og_title = meta.get('og:title', '').replace('| Facebook', '').replace('Facebook', '').strip()
                info['business_name'] = og_title.split('\n')[0].strip() if og_title else ''
            if not info.get('description'):
                info['description'] = meta.get('og:description', '')

            if not info.get('business_name') or len(info.get('business_name', '')) < 3:
                info['business_name'] = meta.get('og:site_name', '').replace('| Facebook', '').replace('Facebook', '').strip()

            print(f"  ✓ {label} page fetched ({len(resp.text)} bytes)")
            if info.get('phones') or info.get('emails'):
                print(f"    Found: phones={len(info.get('phones', []))}, emails={len(info.get('emails', []))}, followers={info.get('followers', '?')}")
                break

        except requests.RequestException as e:
            print(f"  ✗ {label} failed: {e}")

    if not info.get('phones') and not info.get('emails'):
        print(f"  ⚠ No contact info from page HTML, trying DuckDuckGo fallback...")
        ddg_info = search_duckduckgo_contact(info.get('business_name', ''), page_url=url)
        if ddg_info.get('phones'):
            info['phones'] = list(set(info.get('phones', []) + ddg_info['phones']))
            print(f"    Found {len(ddg_info['phones'])} phone(s) via DDG")
        if ddg_info.get('emails'):
            info['emails'] = list(set(info.get('emails', []) + ddg_info['emails']))
            print(f"    Found {len(ddg_info['emails'])} email(s) via DDG")

    if not info.get('business_name') or len(info['business_name']) < 3 or 'facebook' in info['business_name'].lower():
        info['business_name'] = extract_business_name_from_url(url)

    category = detect_category(info.get('business_name', '') + ' ' + ' '.join(page_texts)[:500])
    if info.get('has_website') == 'false' and category == 'general':
        category = 'no_website'

    score, reasons = calculate_qualification_score(info)

    notes_parts = []
    if info.get('phones'):
        notes_parts.append(f"Phones: {', '.join(info['phones'])}")
    if info.get('emails'):
        notes_parts.append(f"Emails: {', '.join(info['emails'])}")
    if reasons:
        notes_parts.append(f"Flags: {', '.join(reasons)}")
    notes = '. '.join(notes_parts) if notes_parts else 'Auto-scraped, no contact info found.'

    lead = {
        'business_name': info.get('business_name', ''),
        'page_url': url,
        'platform': 'facebook',
        'category': category,
        'followers': info.get('followers', ''),
        'email': info.get('emails', [''])[0] if info.get('emails') else '',
        'phone': info.get('phones', [''])[0] if info.get('phones') else '',
        'website': info.get('website', ''),
        'has_website': info.get('has_website', 'false'),
        'address': info.get('address', ''),
        'last_post_date': info.get('last_post', ''),
        'qualification_score': str(score),
        'status': 'new',
        'notes': notes,
    }

    return lead

def search_duckduckgo_contact(business_name, page_url='', max_results=10):
    from ddgs import DDGS

    result = {'phones': [], 'emails': []}
    name = business_name
    if not name or name == 'Facebook':
        name = page_url.split('/')[-1] if page_url else ''

    short_name = re.sub(r'\s*\|\s*(Dhaka|Bangladesh|Spa|Salon|Parlour|Parlor|Beauty|Shop|Store).*', '', name, flags=re.IGNORECASE).strip()
    if not short_name or len(short_name) < 5:
        short_name = name

    queries = [
        f'"{short_name}" Bangladesh phone OR email OR contact',
        f'"{short_name}" Bangladesh contact number',
        f'"{short_name}" Dhaka phone',
        f'{short_name} Bangladesh phone contact',
    ]

    seen_texts = set()
    for query in queries:
        print(f"    DDG contact search: {query[:80]}")
        try:
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    if isinstance(r, dict):
                        href = r.get('href', '')
                        snippet = r.get('title', '') + ' ' + r.get('body', '')
                    else:
                        href = ''
                        snippet = str(r)
                    if not snippet or snippet in seen_texts:
                        continue
                    seen_texts.add(snippet)

                    phones_found = extract_phones(snippet)
                    emails_found = extract_emails(snippet)
                    result['phones'].extend(phones_found)
                    result['emails'].extend(emails_found)

                    time.sleep(0.5)
        except Exception as e:
            print(f"    DDG contact search failed: {e}")

    result['phones'] = list(set(result['phones']))
    result['emails'] = list(set(result['emails']))
    return result

def extract_business_name_from_url(url):
    path = urlparse(url).path.rstrip('/')
    slug = path.split('/')[-1] if path else ''
    name = re.sub(r'[.\-_]+', ' ', slug).strip()
    name = re.sub(r'\s+', ' ', name).title()
    return name

def save_to_server(lead):
    score = int(lead.get('qualification_score', 0))
    if score < 5:
        print(f"  ✗ DISCARDED — {lead['business_name'] or 'Unknown'} | Score: {score} (below threshold)")
        return False

    try:
        resp = requests.post(SERVER_URL, json=lead, timeout=10)
        if resp.status_code == 201:
            print(f"  ✓ SAVED — {lead['business_name'] or 'Unknown'} | Score: {score}")
            return True
        elif resp.status_code == 409:
            print(f"  ~ DUPLICATE — {lead['business_name'] or 'Unknown'}")
            return False
        else:
            print(f"  ✗ Server error {resp.status_code}: {resp.text}")
            return False
    except requests.RequestException as e:
        print(f"  ✗ Could not reach server: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fb_scraper.py <facebook_page_url> [url2] [url3] ...")
        sys.exit(1)

    urls = sys.argv[1:]
    saved = 0
    for i, url in enumerate(urls):
        print(f"\n--- Scraping {i + 1}/{len(urls)} ---")
        lead = scrape_facebook_page(url)
        if lead:
            ok = save_to_server(lead)
            if ok:
                saved += 1
        if i < len(urls) - 1:
            delay = 3
            print(f"  Waiting {delay}s...")
            time.sleep(delay)

    print(f"\n✓ Done. {saved}/{len(urls)} leads saved.")

if __name__ == '__main__':
    main()
