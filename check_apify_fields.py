"""Check what fields the Apify Facebook Pages Scraper returns."""
import requests, os

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# Get most recent SUCCEEDED run
resp = requests.get(
    'https://api.apify.com/v2/actor-runs?limit=1&status=SUCCEEDED',
    headers=headers
)
data = resp.json()
items = data.get('data', [])
if not items:
    print("No runs found")
    exit(0)

run_id = items[0]['id']
print(f"Latest run: {run_id}")
print()

# Get 3 items to see full fields
resp = requests.get(
    f'https://api.apify.com/v2/actor-runs/{run_id}/dataset/items',
    headers=headers,
    params={'limit': 3}
)
results = resp.json()
if results and len(results) > 0:
    item = results[0]
    print(f"Page: {item.get('title', 'N/A')}")
    print(f"URL: {item.get('pageUrl', 'N/A')}")
    print(f"\nAll fields ({len(item)} total):")
    for k, v in item.items():
        if k in ('title', 'pageUrl', 'facebookUrl'):
            continue
        val = str(v)
        t = type(v).__name__
        print(f"  {k} ({t}) = {val[:200]}")
