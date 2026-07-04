"""Check what fields the Apify Facebook Pages Scraper returns."""
import requests, os, json

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# Get a recent run that had results (use a dataset from a bigger run)
# Run SiWs5tNgquq9Fhj1k has dataset: y8w3AbyXRpT3lCdsm
dataset_id = 'y8w3AbyXRpT3lCdsm'

resp = requests.get(
    f'https://api.apify.com/v2/datasets/{dataset_id}/items',
    headers=headers,
    params={'limit': 1}
)
results = resp.json()
print(f"Got {len(results)} items")
print()

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
        trunc = val[:250]
        print(f"  {k} ({t}) = {trunc}")
else:
    print("No items. Let me check another dataset...")
    # Try the first run's dataset
    resp2 = requests.get(
        'https://api.apify.com/v2/datasets/vcey88LQWadN8b4us/items',
        headers=headers
    )
    r2 = resp2.json()
    print(f"Got {len(r2)} items")
    if r2 and len(r2) > 0:
        item = r2[0]
        print(f"Page: {item.get('title', 'N/A')}")
        for k, v in item.items():
            val = str(v)
            t = type(v).__name__
            print(f"  {k} ({t}) = {val[:200]}")
