# Agent Instructions — Lead Gen Demo Builder

## CRITICAL: Answering "how many leads found?"
After a hunt, NEVER trust the script's reported count alone. You MUST:
1. Run `wc -l /home/skarbolt/kb/lead-gen/collected_leads/leads.csv` to get total rows
2. Then grep for today's date + category to confirm exact saved count
3. Report the CSV-verified number, not the script's stdout number

Example:
```bash
grep "2026-06-29" /home/skarbolt/kb/lead-gen/collected_leads/leads.csv | grep -i "jewelry" | wc -l
```

If smart_hunt says "server offline", cached leads are in `pending_leads_cache.json`. Run `--flush-cache` when server is back:
```bash
python3 smart_hunt.py --flush-cache
```

## How to build a category demo

Use `build_demo.py` from the project root:

```bash
python3 build_demo.py --category fashion --name "My Store" --phone 01712345678
python3 build_demo.py --category "beauty salon" --name "Bella-BD" --phone 01712345678 --deploy
python3 build_demo.py --category home --name "Home Decor" --phone 01712345678 --deploy
```

### Arguments
| Flag | Required | Description |
|------|----------|-------------|
| `--category` / `-c` | Yes | Business category name (fashion, beauty, home, etc.) |
| `--name` / `-n` | Yes | Store/business display name |
| `--phone` / `-p` | Yes | Phone number (Bangladesh format) |
| `--address` / `-a` | No | Business address (default: Dhaka, Bangladesh) |
| `--facebook` | No | Facebook page URL or handle |
| `--instagram` | No | Instagram handle |
| `--out` / `-o` | No | Output directory (default: demos/outreach_<category>) |
| `--facebook-page` | No | Facebook page URL — auto-extract name, category, phone |
| `--deploy` | No | Auto-deploy to Netlify after building |

### Available categories
agriculture, automotive, baby, beauty, education, fashion, fitness, general, healthcare, home, hotel, jewelry, manufacturing, pharmacy, realestate, restaurant, retail, services, skincare

Category names are flexible — "beauty salon", "Beauty Salon", and "beauty" all work.

### Deploy
With `--deploy`, the site is uploaded to Netlify at https://bella-bd-shop.netlify.app.
The Netlify token comes from `.env` (`NETLIFY_TOKEN`).

### Output
All pages are generated in the output directory:
- index.html (homepage with hero, best sellers, newsletter)
- products.html (all products with subcategory filters)
- order.html (4-step checkout with cart, payment, confirmation)
- about.html, contact.html, login.html, register.html
- styles.css, script.js

## Telegram Agent Workflow ("Lead Gen Outreach" topic)

When a lead comes into the Telegram topic and the user asks you to build a demo:

1. **Read lead details** from the Telegram chat topic
2. **Find the business on Facebook** using the provided URL or name
3. **Visit the Facebook page** with browser tools (or use `extract_facebook_brand.py` as fallback)
4. **Extract brand info from the page:**
   - Business name (from page title / about section)
   - Business category (determine from their posts/page description)
   - Brand colors (look at the cover photo, profile pic, page theme)
   - Products/prices (look at their posts, shop section, or pinned posts)
   - Logo / profile picture URL
   - Phone number (from about section or posts)
5. **Build the demo** with `build_demo.py`
6. **Present the result** — share the output path or deployed URL

### Facebook scraping notes
- `extract_facebook_brand.py <url>` tries to auto-extract info via HTTP
- If it fails (Facebook blocks it), **you must manually browse the page** with browser tools
- Look at the cover photo for brand colors, posts for products/pricing, about section for contact info

### Quick reference
```bash
# Build from scratch
python3 build_demo.py -c fashion -n "Fashion Hub" -p 01712345678 --deploy

# Auto-extract from Facebook (partial — may need manual overrides)
python3 build_demo.py --facebook-page "https://facebook.com/bellabd.bd" --deploy

# Extract just the brand info
python3 extract_facebook_brand.py "bellabd.bd" --json
```
