"""Check what fields the Apify Facebook Pages Scraper returns."""
import requests, os, json

key = os.environ.get('APIFY_API_KEY', '')
headers = {'Authorization': f'Bearer {key}'}

# List actor runs for the FB scraper
resp = requests.get(
    'https://api.apify.com/v2/acts/apify~facebook-pages-scraper/runs?limit=5&status=SUCCEEDED',
    headers=headers
)
data = resp.json()
print(json.dumps(data, indent=2)[:2000])
