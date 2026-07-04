import json, re, sys, time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}


def estimate_days(text):
    if not text:
        return None
    from datetime import datetime as _dt
    try:
        parsed = _dt.strptime(text, '%b %d, %Y %I:%M %p')
        return (datetime.now(timezone.utc) - parsed.replace(tzinfo=timezone.utc)).days
    except (ValueError, TypeError):
        pass
    t = text.lower().strip()
    if t in ('just now', 'now'):
        return 0
    if t == 'yesterday':
        return 1
    num = int(re.search(r'\d+', t).group()) if re.search(r'\d+', t) else None
    if num is None:
        return None
    if re.search(r'min', t):
        return 0
    if re.search(r'hour', t):
        hours_ago = num
        if hours_ago < 24:
            return 0
        return hours_ago // 24
    if re.search(r'day', t):
        return num
    if re.search(r'week', t):
        return num * 7
    if re.search(r'month', t):
        return num * 30
    if re.search(r'year', t):
        return num * 365
    return None


def classify(days):
    if days is None:
        return 'unknown'
    if days <= 50:
        return 'active'
    if days <= 90:
        return 'slow'
    return 'inactive'


def fetch_page(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        return None


def check_activity(url):
    html = fetch_page(url)
    if html is None:
        return {'url': url, 'days_since_post': None, 'status': 'unknown', 'raw_date': None}

    soup = BeautifulSoup(html, 'html.parser')
    candidates = []

    # data-utime attributes (unix timestamps)
    for el in soup.find_all(attrs={'data-utime': True}):
        try:
            ts = int(el['data-utime'])
            if ts > 1e9:
                raw = el.get_text(strip=True) or str(ts)
                days = (datetime.now(timezone.utc).timestamp() - ts) / 86400
                candidates.append((days, raw))
        except (ValueError, TypeError):
            pass

    # <abbr> with title or aria-label
    for el in soup.find_all('abbr'):
        for attr in ('title', 'aria-label'):
            val = el.get(attr, '')
            if val:
                d = estimate_days(val)
                if d is not None:
                    candidates.append((d, val))

    # <abbr> text content
    for el in soup.find_all('abbr'):
        txt = el.get_text(strip=True)
        if txt:
            d = estimate_days(txt)
            if d is not None:
                candidates.append((d, txt))

    # Text patterns in the page body
    time_pattern = re.compile(
        r'(?:just now|now|yesterday|'
        r'\d+\s*(?:min|hour|day|week|month|year)[s]?\s*ago)',
        re.IGNORECASE,
    )
    body = soup.get_text()
    for m in time_pattern.finditer(body):
        txt = m.group(0)
        d = estimate_days(txt)
        if d is not None:
            candidates.append((d, txt))

    if not candidates:
        return {'url': url, 'days_since_post': None, 'status': 'unknown', 'raw_date': None}

    best = min(candidates, key=lambda x: x[0])
    days_since = round(best[0])
    return {
        'url': url,
        'days_since_post': days_since,
        'status': classify(days_since),
        'raw_date': best[1],
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Usage: python3 check_fb_activity.py <facebook_url>'}))
        sys.exit(1)

    url = sys.argv[1].strip()
    result = check_activity(url)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
