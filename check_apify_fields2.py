"""Check what fields the Apify Facebook Pages Scraper returns."""
import requests, os

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# List actor runs for the FB scraper
resp = requests.get(
    'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs?limit=5&status=SUCCEEDED',
    headers=headers
)
data = resp.json()
items = data.get('data', [])
print(f"Got {len(items)} runs")
if not items:
    print("Response keys:", list(data.keys()))
    if 'error' in data:
        print("Error:", data['error'])
    # Try getting runs via different endpoint
    resp2 = requests.get(
        'https://api.apify.com/v2/actor-runs?limit=1&status=SUCCEEDED',
        headers=headers
    )
    d2 = resp2.json()
    print("actor-runs response keys:", list(d2.keys()))
    if 'data' in d2:
        print("data type:", type(d2['data']))
        if isinstance(d2['data'], list):
            print(f"len: {len(d2['data'])}")
            if d2['data']:
                print("first keys:", list(d2['data'][0].keys()))
    exit(0)

run_id = items[0]['id']
print(f"Latest run: {run_id}")

# Get items
resp = requests.get(
    f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
    headers=headers,
    params={'limit': 2}
)
results = resp.json()
print(f"Got {len(results)} items")
if results and len(results) > 0:
    item = results[0]
    print(f"\nPage: {item.get('title', 'N/A')}")
    print(f"All fields ({len(item)} total):")
    for k, v in item.items():
        if k in ('title', 'pageUrl', 'facebookUrl'):
            continue
        val = str(v)
        t = type(v).__name__
        print(f"  {k} ({t}) = {val[:200]}")
