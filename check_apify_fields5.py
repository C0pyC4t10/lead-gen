"""Check what fields the Apify Facebook Pages Scraper returns."""
import requests, os, json

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# Get runs for the FB scraper, filter to SUCCEEDED
resp = requests.get(
    'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs?limit=10&status=SUCCEEDED',
    headers=headers
)
data = resp.json()
items = data.get('data', {}).get('items', [])

for run in items[:5]:
    ds_id = run.get('defaultDatasetId', '')
    print(f"Run {run['id']} - dataset: {ds_id}")
    
    resp = requests.get(
        f'https://api.apify.com/v2/datasets/{ds_id}/items',
        headers=headers,
        params={'limit': 1}
    )
    results = resp.json()
    if results and len(results) > 0:
        item = results[0]
        print(f"  Page: {item.get('title', 'N/A')}")
        # Show key fields that might indicate ads/boosting
        for k in ['likes', 'followers', 'is_advertiser', 'has_active_ads',
                   'ads', 'advertiser', 'posts', 'recentPosts',
                   'lastPost', 'engagement', 'verified', 'page_created']:
            if k in item:
                print(f"  {k}: {item[k]}")
        # Show top-level field names
        print(f"  ALL fields: {list(item.keys())}")
        print()
    else:
        print(f"  Empty dataset")
        print()
