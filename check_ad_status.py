"""Check ad_status field values."""
import requests, os, json

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# Check a few datasets for ad_status values
ds_ids = ['vcey88LQWadN8b4us', 'T9oPd1adAbivcTLHH', '2D3dCUo392l0whi1m',
          'uHfyvK9caxce46E25']

for ds_id in ds_ids:
    resp = requests.get(
        f'https://api.apify.com/v2/datasets/{ds_id}/items',
        headers=headers,
        params={'limit': 3}
    )
    results = resp.json()
    if not results or len(results) == 0:
        continue
    print(f"\n--- Dataset: {ds_id} ({len(results)} items) ---")
    for item in results:
        title = item.get('title', 'N/A')[:40]
        ad_status = item.get('ad_status', 'MISSING')
        creation_date = item.get('creation_date', 'MISSING')
        ad_lib = item.get('pageAdLibrary', 'MISSING')
        print(f"  {title[:35]:35s} | ad_status: {ad_status} | created: {creation_date}")
        if ad_lib != 'MISSING':
            print(f"    Ad Library: {str(ad_lib)[:100]}")
