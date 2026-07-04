#!/usr/bin/env python3
"""Intelligently filter qualified, real Bangladeshi product-selling Facebook pages."""
import csv, re, json

CSV_PATH = '/home/skarbolt/kb/lead-gen/collected_leads/facebook_leads.csv'

# ── Load data ──
all_rows = []
with open(CSV_PATH, 'r') as f:
    reader = csv.DictReader(f)
    for r in reader:
        all_rows.append(r)

print(f"Total raw leads: {len(all_rows)}")

def get_likes(r):
    try:
        return int(re.sub(r'[^0-9]', '', str(r.get('likes', '0'))))
    except:
        return 0

def get_score(r):
    try:
        return int(r.get('score', '0'))
    except:
        return 0

def is_personal_profile(name, url):
    """Check if page is a personal profile, not a business."""
    n = name.lower().strip()
    u = url.lower().strip()
    
    # Known personal names (Bangladeshi)
    personal_first_names = ['md ', 'md.', 'mohammad ', 'muhammad ', 'syed ', 
                           'sk ', 'shakil', 'haque', 'hasan', 'hassan', 'hossain',
                           'sumon', 'rahman', 'akter', 'akter ', 'akter$',
                           'hoque', 'ahmed ', 'alam ', 'mokhles', 'monjurul',
                           'robiul', 'jahid', 'joy', 'kamal', 'salman',
                           'nurunnobi', 'ziabul', 'sabbir', 'ahir', 'sajid',
                           'kumar', 'kuldeep', 'szanyel', 'limbuwan',
                           'andreea', 'chatchareeya', 'triệu', 'คำภู', 'พรมผิว',
                           'niha', 'nihab', 'mc cho', 'barisha']
    
    for pn in personal_first_names:
        if n.startswith(pn) or pn in n.split():
            return True
    
    # Check if name is just "First Last" (2 short words)
    parts = n.split()
    if len(parts) <= 2 and len(n) < 20 and not any(w in n for w in 
        ['shop', 'store', 'mart', 'bd', 'fashion', 'beauty', 'online', 'bd',
         'brand', 'collection', 'products', 'home', 'gadget', 'mobile',
         'baby', 'kids', 'toy', 'sport', 'gift', 'organic', 'craft',
         'perfume', 'footwear', 'cosmetic', 'care', 'food', 'lifestyle',
         'enterprise', 'limited', 'ltd', 'corporation', 'trading',
         'international', 'bazaar', 'wholesale', 'retail', 'boutique',
         'jewel', 'gold', 'decoration', 'interior', 'electric']):
        return True
    
    return False

def is_bangladesh_business(r):
    """Check if this is a Bangladeshi business."""
    n = (r.get('name') or '').lower()
    u = (r.get('url') or '').lower()
    phone = (r.get('phone') or '').strip()
    
    # Check if clearly NOT Bangladesh
    foreign_hints = ['toronto', 'canada', 'new york', 'bronx', 'usa',
                     'harare', 'zimbabwe', 'philippines', 'paranaque',
                     'tatebayashi', 'gunma', 'japan', 'bahrain', 'manama',
                     'tegucigalpa', 'honduras', 'nepal', 'kathmandu',
                     'bhaktapur', 'lalitpur', 'doha', 'qatar',
                     'london uk', 'australia', 'saudi', 'dubai', 'uae']
    
    for h in foreign_hints:
        if h in n or h in u:
            return False
    
    # Check if Bangladeshi
    bd_hints = ['dhaka', 'bangladesh', 'bd', 'chittagong', 'banani',
                'mirpur', 'kushtia', 'pabna', 'maulvi', 'mohammadpur']
    is_bd = any(h in n for h in bd_hints)
    has_bd_phone = phone.startswith('+880') if phone else False
    
    return is_bd or has_bd_phone

def sells_products(name):
    """Check if the business name suggests product sales."""
    n = name.lower()
    
    # These clearly sell products
    product_seller = ['shop', 'store', 'mart', 'bazaar', 'collection',
                      'fashion', 'wear', 'clothing', 'apparel', 'fabric',
                      'jewel', 'jewellery', 'gold', 'diamond', 'pearl',
                      'baby', 'kids', 'toy', 'toys', 'child',
                      'gadget', 'electronic', 'electronics', 'mobile', 'phone',
                      'computer', 'laptop', 'tech', 'accessorie', 'accessories',
                      'cosmetic', 'cosmetics', 'beauty', 'skincare', 'skin',
                      'makeup', 'perfume', 'perfumes', 'fragrance',
                      'footwear', 'shoe', 'shoes', 'walk', 'leather', 'leatherex',
                      'bag', 'bags', 'gift', 'gifts', 'present',
                      'organic', 'herb', 'herbs', 'health',
                      'handicraft', 'craft', 'crafts', 'handmade', 'artisan',
                      'home', 'decor', 'decoration', 'furniture', 'interior',
                      'sport', 'sports', 'gym', 'fitness',
                      'grocery', 'foodi', 'supermarket', 'food',
                      'lifestyle', 'brand', 'online',
                      'enterprise', 'corporation', 'limited', 'ltd',
                      'trading', 'international', 'wholesale', 'retail',
                      'boutique', 'studio', 'gallery',
                      'products', 'product', 'outlet',
                      'light', 'lamp', 'mirror', 'glass',
                      'halal', 'stationery', 'book', 'bookstore',
                      'pharmacy', 'pharma', 'medical',
                      'audi', 'audio', 'sound', 'speaker',
                      'baby', 'mum', 'mom', 'moms', 'little', 'angel',
                      'paradise', 'dreamer', 'dreamers', 'world',
                      'family', 'life', 'living',
                      'blue', 'pink', 'bird',
                      'sarmin', 'hlwcraft', 'craftimation',
                      'story', 'taupe', 'notch', 'bondhon',
                      'tijara', 'wide', 'zone', 'accs', 'hunter',
                      'brand', 'nishat', 'linen', 'emart',
                      'glamgrl', 'beautyology', 'andeem', 'gootipa',
                      'totebd', 'hongbao', 'lavender', 'super',
                      'don', 'sumdany', 'sparrow',
                      'baper', 'hotel', 'building',
                      'foodpanda', 'kfc', 'daily', 'star']
    
    return any(h in n for h in product_seller)

# ── Filter ──
qualified = []
rejected_reasons = []

for r in all_rows:
    name = (r.get('name') or '').strip()
    url = (r.get('url') or '').strip()
    phone = (r.get('phone') or '').strip()
    likes = get_likes(r)
    score = get_score(r)
    
    if not name or not url:
        continue
    
    # Filter 1: Personal profiles
    if is_personal_profile(name, url):
        rejected_reasons.append((name, 'personal profile'))
        continue
    
    # Filter 2: Must be Bangladeshi
    if not is_bangladesh_business(r):
        rejected_reasons.append((name, 'not Bangladesh'))
        continue
    
    # Filter 3: Must sell products
    if not sells_products(name):
        rejected_reasons.append((name, 'not product seller'))
        continue
    
    # Filter 4: Reasonable engagement
    if likes < 100 and not phone:
        rejected_reasons.append((name, f'low engagement ({likes}) + no phone'))
        continue
    
    qualified.append(r)

# ── Sort by likes descending ──
qualified.sort(key=lambda r: (-get_likes(r)))

# ── Print rejection summary ──
rej_by_type = {}
for n, reason in rejected_reasons:
    rej_by_type.setdefault(reason, []).append(n)

print(f"\n{'='*60}")
print(f"REJECTED: {len(rejected_reasons)}")
for reason, names in sorted(rej_by_type.items()):
    print(f"  {reason}: {len(names)} — {', '.join(names[:5])}{'...' if len(names)>5 else ''}")

# ── Print qualified ──
print(f"\n{'='*60}")
print(f"🔥 QUALIFIED LEADS: {len(qualified)}")
print(f"{'='*60}\n")

cat_map = {
    'beauty': 'Beauty & Cosmetics',
    'cosmetic': 'Beauty & Cosmetics',
    'skincare': 'Beauty & Cosmetics',
    'skin': 'Beauty & Cosmetics',
    'makeup': 'Beauty & Cosmetics',
    'perfume': 'Beauty & Cosmetics',
    'glam': 'Beauty & Cosmetics',
    'beautyology': 'Beauty & Cosmetics',
    'emart': 'Beauty & Cosmetics',
    'emily': 'Beauty & Cosmetics',
    'china beauty': 'Beauty & Cosmetics',
    'fency': 'Beauty & Cosmetics',
    'mehedi': 'Beauty & Cosmetics',
    'jfm': 'Beauty & Cosmetics',
    'story brand': 'Beauty & Cosmetics',
    'taupe': 'Beauty & Cosmetics',
    'fashion': 'Fashion & Apparel',
    'wear': 'Fashion & Apparel',
    'clothing': 'Fashion & Apparel',
    'easy fashion': 'Fashion & Apparel',
    'glamgrl': 'Fashion & Apparel',
    'andeem': 'Fashion & Apparel',
    'everywear': 'Fashion & Apparel',
    'nishat': 'Fashion & Apparel',
    'dreamers': 'Fashion & Apparel',
    'gootipa': 'Fashion & Apparel',
    'linen': 'Fashion & Apparel',
    'samia': 'Fashion & Apparel',
    'baby': 'Baby & Kids',
    'kids': 'Baby & Kids',
    'toy': 'Baby & Kids',
    'mum': 'Baby & Kids',
    'moms': 'Baby & Kids',
    'little': 'Baby & Kids',
    'angel': 'Baby & Kids',
    'paradise': 'Baby & Kids',
    'blue': 'Baby & Kids',
    'pink': 'Baby & Kids',
    'bird': 'Baby & Kids',
    'hello junior': 'Baby & Kids',
    'electronic': 'Electronics & Gadgets',
    'gadget': 'Electronics & Gadgets',
    'mobile': 'Electronics & Gadgets',
    'phone': 'Electronics & Gadgets',
    'dubai electronic': 'Electronics & Gadgets',
    'brand electronic': 'Electronics & Gadgets',
    'hunter': 'Electronics & Gadgets',
    'dhaka audio': 'Electronics & Gadgets',
    'accessorie': 'Electronics & Gadgets',
    'accszone': 'Electronics & Gadgets',
    'jewel': 'Jewelry',
    'gold': 'Jewelry',
    'pearl': 'Jewelry',
    'barbara': 'Jewelry',
    'handicraft': 'Handicraft & Artisan',
    'craft': 'Handicraft & Artisan',
    'handmade': 'Handicraft & Artisan',
    'sarmin': 'Handicraft & Artisan',
    'hlwcraft': 'Handicraft & Artisan',
    'craftimation': 'Handicraft & Artisan',
    'moon': 'Handicraft & Artisan',
    'home': 'Home & Decor',
    'decor': 'Home & Decor',
    'furniture': 'Home & Decor',
    'interior': 'Home & Decor',
    'mirror': 'Home & Decor',
    'glass': 'Home & Decor',
    'light': 'Home & Decor',
    'lamp': 'Home & Decor',
    'bismillah': 'Home & Decor',
    'footwear': 'Footwear',
    'shoe': 'Footwear',
    'leather': 'Footwear',
    'walk': 'Footwear',
    'sparrow': 'Footwear',
    'orion': 'Footwear',
    'leatherex': 'Footwear',
    'organic': 'Organic & Health',
    'herb': 'Organic & Health',
    'rue': 'Organic & Health',
    'grocery': 'Grocery & Food',
    'foodi': 'Grocery & Food',
    'mart': 'Grocery & Food',
    'supermarket': 'Grocery & Food',
    'khulshi': 'Grocery & Food',
    'unimart': 'Grocery & Food',
    'lavender super': 'Grocery & Food',
    'bag': 'Accessories & Lifestyle',
    'don sumdany': 'Accessories & Lifestyle',
    'gift': 'Gift Shop',
    'bondhon': 'Gift Shop',
    'safa': 'Gift Shop',
    'wide zone': 'Accessories & Lifestyle',
    'tijara': 'Accessories & Lifestyle',
    'sport': 'Sports & Fitness',
    'ca sport': 'Sports & Fitness',
    'leisure': 'Sports & Fitness',
    'dugout': 'Sports & Fitness',
    'perfume': 'Perfume & Fragrance',
    'napa': 'Perfume & Fragrance',
    'elate': 'Perfume & Fragrance',
    'casio': 'Watches & Accessories',
    'lifestyle': 'Accessories & Lifestyle',
    'hatch': 'Accessories & Lifestyle',
    'episodes': 'Accessories & Lifestyle',
}

def get_category(name):
    n = name.lower()
    for kw, cat in sorted(cat_map.items(), key=lambda x: -len(x[0])):
        if kw in n:
            return cat
    return 'General Retail'

for i, r in enumerate(qualified[:35], 1):
    name = (r.get('name') or '').strip()
    phone = (r.get('phone') or '').strip() or 'N/A'
    likes = get_likes(r)
    has_web = r.get('has_website', '').strip().lower() in ('yes', 'true', 'y', '1')
    score = get_score(r)
    url = (r.get('url') or '').strip()
    email = (r.get('email') or '').strip()
    category = get_category(name)
    
    hot = "🔥" if not has_web and phone != 'N/A' else ""
    
    print(f" {i:2d}. {hot} [{score}/12] {name[:42]:42s} | 👍 {likes:>8,}")
    print(f"     {category:25s} | 📞 {phone:15s} | {'❌ No site' if not has_web else '✅ Website'}")
    if email:
        print(f"     📧 {email}")
    print(f"     🔗 {url}")
    print()

# ── Category summary ──
from collections import Counter
cats = Counter(get_category((r.get('name') or '').strip()) for r in qualified)
print(f"{'='*60}")
print(f"CATEGORY BREAKDOWN ({len(qualified)} total)")
print(f"{'='*60}")
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    hot_cat = sum(1 for r in qualified if not (r.get('has_website', '').strip().lower() in ('yes', 'true', 'y', '1')) and (r.get('phone') or '').strip() and get_category((r.get('name') or '').strip()) == cat)
    print(f"  {cat:30s} → {count:2d} leads{'  🔥 ' + str(hot_cat) + ' hot' if hot_cat else ''}")

print(f"\n🔥 HOT leads (no website + phone): {sum(1 for r in qualified if not (r.get('has_website', '').strip().lower() in ('yes', 'true', 'y', '1')) and (r.get('phone') or '').strip())}")
print(f"📧 With email: {sum(1 for r in qualified if (r.get('email') or '').strip())}")
