# Facebook Search Queries — Lead Generation

> Copy-paste these queries directly into the Facebook search bar. Use the "Posts" or "Pages" filter as needed.

---

## Category 1: No Website Businesses (10 queries)

These find SMEs operating without a web presence — prime candidates for website development and digital transformation.

```
1. "no website" "business" Bangladesh
2. "call us at" "shop" "no website"
3. "contact us on WhatsApp" "business page" Bangladesh
4. "DM to order" "no website"
5. "home delivery only" "page" Bangladesh 2026
6. "we don't have a website" "business"
7. "order via message" "shop" Bangladesh
8. "only on Facebook" "business" Dhaka
9. "no online store" "contact us" Bangladesh
10. "call for price" "business" "no website"
```

---

## Category 2: Beauty Product Sellers (8 queries)

Targeting beauty parlors, cosmetic boutiques, skincare sellers, and salon product retailers.

```
11. "beauty parlor" "Dhaka" "products"
12. "cosmetics shop" "Bangladesh" "price list"
13. "skincare products" "home delivery" Bangladesh
14. "beauty products wholesale" Bangladesh
15. "salon products" "order now" Bangladesh
16. "makeup store" "Dhaka" "cash on delivery"
17. "beauty boutique" "Bangladesh" "new collection"
18. "organic skincare" "Bangladesh" "shop"
```

---

## Category 3: Businesses Needing Automation/ERP (7 queries)

Prospects running on manual processes who need ExecERP, workflow automation, or AI integration.

```
19. "manual accounting" "business" Bangladesh
20. "inventory management" "problems" Bangladesh
21. "excel based" "business" "Bangladesh"
22. "looking for ERP" "Bangladesh" small business
23. "automate" "business processes" Bangladesh
24. "struggling with" "order management" Bangladesh
25. "paper based" "records" "business" Bangladesh
```

---

## Category 4: General SME Prospects (5 queries)

Broad queries to discover SMEs across multiple industries.

```
26. "small business" "Bangladesh" "growing"
27. "startup" "Dhaka" "entrepreneur"
28. "manufacturing" "Bangladesh" "SME"
29. "retail shop" "Bangladesh" "business"
30. "wholesale" "supplier" "Bangladesh"
```

---

## Category 5: F-Commerce — No-Website Signals (15 queries)

These surface businesses **actively selling on Facebook without a website** — the highest-conversion leads. Every query targets businesses taking orders manually (DM/inbox/WhatsApp) rather than through an online store.

```
31. "DM to order" "price" Bangladesh
32. "inbox to order" "delivery" Bangladesh
33. "comment price" "product" Bangladesh
34. "message us to order" Bangladesh
35. "call to order" "home delivery" Bangladesh
36. "cash on delivery" "DM" Bangladesh
37. "price list" "new collection" "order"
38. "WhatsApp" "order" "catalog" Bangladesh
39. "no website" "selling" "Facebook" Bangladesh
40. "only on Facebook" "shop" "Bangladesh"
41. "order via inbox" "Dhaka"
42. "send message to buy" Bangladesh
43. "contact number" "order now" Bangladesh
44. "WhatsApp me to order" Bangladesh
45. "we deliver" "contact us" Bangladesh
```

---

## Category 6: Industry Commerce — Active Sellers (15 queries)

Industry-specific queries targeting **active product sellers** who show manual-ordering patterns. Each query pairs a product vertical with a commerce pain signal.

```
46. "fashion" "DM to order" Bangladesh
47. "cosmetics" "inbox to order" Dhaka
48. "jewelry" "WhatsApp order" Bangladesh
49. "gadgets" "electronic" "cash on delivery" Dhaka
50. "baby products" "home delivery" Bangladesh
51. "perfume brand" "order" "delivery" Bangladesh
52. "bags accessories" "DM" Bangladesh
53. "home decor" "inbox" "order" Dhaka
54. "organic skincare" "order now" Bangladesh
55. "grocery" "home delivery" "order" Dhaka
56. "footwear" "cash on delivery" Bangladesh
57. "toys" "order" "Facebook page" Bangladesh
58. "phone accessories" "delivery" Bangladesh
59. "dress" "new collection" "order" Bangladesh
60. "kitchen items" "home delivery" Bangladesh
```

---

## F-Commerce Discovery Method: Facebook Ads Library

The **highest-conversion discovery source** — businesses running Facebook ads are already spending money on customer acquisition. They feel the pain of no website most acutely because ads perform 3-5x better when linked to a professional website.

### Workflow

1. Go to **facebook.com/ads/library**
2. Set **Country: Bangladesh**
3. Search by **category** (use these one at a time):
   - `Shopping & Retail`
   - `E-commerce`
   - `Beauty & Personal Care`
   - `Fashion & Apparel`
   - `Jewelry & Watches`
   - `Baby & Kids Products`
   - `Home & Garden`
   - `Electronics & Gadgets`
4. Browse active advertisers — each card shows the advertiser's Facebook Page
5. Visit each **Facebook Page** and check:
   - **Has Website?** → Look for "Website" link under About or in bio
   - **Order Method?** → Do they say "DM to order", "Inbox", "WhatsApp"?
   - **Recent Posts?** → Active in last 7 days?
   - **Followers?** → 20K+ preferred
6. For each qualifying lead, save via:
   ```
   POST /api/fcommerce/lead
   {
     "business_name": "Fashion Store BD",
     "page_url": "https://facebook.com/fashionstorebd",
     "followers_int": 35000,
     "has_website": "no",
     "order_method": "Inbox",
     "last_post_date": "2026-06-20",
     "product_categories": "Fashion & Boutique",
     "discovery_source": "Facebook Ads Library",
     "phone": "+8801712345678"
   }
   ```
7. Set `discovery_source: "Facebook Ads Library"` for all leads from this method

### Why Ads Library beats Search

| Signal | Search | Ads Library |
|---|---|---|
| Business is active | Sometimes | **Always** (running ads = active) |
| Has budget | Unknown | **Yes** (already spending) |
| Selling products | Maybe | **Yes** (ads mean commerce) |
| Needs website | Unknown | **High chance** (ads → leads → manual management) |
| Conversion rate | 5-10% | **30-40%** estimated |

### Ad Creative Analysis (Extra Signal)

When reviewing an advertiser's ads, look for these **high-priority signals**:
- Ad links go to **Facebook Page or Messenger** (not a website) → no website
- Ad says "DM to order" or "Message us" → manual ordering pain
- Ad is high quality but page lacks professionalism → weak branding opportunity
- Ad is running for 30+ days → committed advertiser, high conversion potential

**Scoring for Ads Library leads:**
- If ad links to FB Page (no website) → auto `has_website: "no"`
- Running ads 30+ days → manual +1 to score (already captured by other factors)
- Multiple active ads → high engagement signal
