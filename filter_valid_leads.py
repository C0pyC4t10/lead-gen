#!/usr/bin/env python3
"""Filter truly valid, active, product-selling Bangladeshi Facebook pages from our data."""
import csv, re
from datetime import date

CSV_PATH = '/home/skarbolt/kb/lead-gen/collected_leads/facebook_leads.csv'
OUT_CSV = '/home/skarbolt/kb/lead-gen/qualified_leads/valid_active_leads.csv'

# ── Load all leads ──
all_leads = []
with open(CSV_PATH, 'r') as f:
    reader = csv.DictReader(f)
    for r in reader:
        all_leads.append(r)

print(f"Loaded {len(all_leads)} total leads")

# ── Exclusion patterns (personal profiles, non-BD, news, etc.) ──
BANNED_NAMES = re.compile(
    r'(Md\s|Md\.|Md |Mohammad\s|Muhammad\s|M\s?[A-Z][a-z]+ [A-Z][a-z]+$|'  # Personal names
    r'Shakil|Haque|Hassain|Hassan|Haque$|' 
    r'Sumon\s|Nurunnobi|Ahir|Sabbir|Hasan\s|Ahmed\s|Alam\s|' 
    r'Kuldeep\s|Kumar\s|Rahman\s|Mokhles\s|Akter\s|Hoque\s|' 
    r'Barisha|Triệu|คำภู|พรมผิว|Limbuwan|Szanyel|Sajid\s|' 
    r'vlogs$|Vlog\s|vlog\s|'  # Vloggers
    r'Kamal|Salman|Nurunnobi|Ziabul|Robiul)',  # More personal names
    re.IGNORECASE
)

BANNED_URL_SLUGS = [
    'firstpost', 'dohanews', 'tbsnews', 'textiletoday',  # News
    'nrbbank', 'DGB.Bank', 'ccithn',  # Banks/orgs
    'Kailash.Blades',  # Nepal
    'Federation.of.Handicraft',  # Nepal
]

def is_valid_name(name):
    """Check if it looks like a real business, not a personal profile."""
    name_s = name.strip()
    if not name_s or len(name_s) < 3:
        return False
    if BANNED_NAMES.search(name_s):
        return False
    # Must have descriptive business-like words 
    # (vs plain "First Name Last Name" pattern)
    return True

def is_bangladesh(lead):
    """Check if lead appears to be a Bangladeshi business."""
    name = (lead.get('name') or '').lower()
    url = (lead.get('url') or '').lower()
    phone = (lead.get('phone') or '').strip()
    area = name + ' ' + url
    
    # Check if clearly not Bangladesh
    not_bd_hints = ['kathmandu', 'nepal', 'bhaktapur', 'lalitpur',
                    'phnom penh', 'tegucigalpa', 'honduras',
                    'toronto', 'bronx', 'new york', 'australia',
                    'paranaque', 'philippines', 'manama', 'bahrain',
                    'tatebayashi', 'gunma', 'japan',
                    'usa', 'london uk', 'doha', 'qatar']
    for hint in not_bd_hints:
        if hint in area:
            return False
    
    # Check if Bangladesh via area mentions or BD phone
    bd_hints = ['dhaka', 'bangladesh', 'bd', 'chittagong', 'banani',
                'mirpur', 'kushtia', 'mohammadpur']
    area_bd = any(hint in area for hint in bd_hints)
    phone_bd = phone.startswith('+880') if phone else False
    phone_01 = phone.startswith('01') if phone else False
    
    return area_bd or phone_bd or phone_01

def is_running_ads(lead):
    status = (lead.get('ad_status') or '').lower()
    return 'currently running' in status and 'isn' not in status

def has_good_engagement(lead):
    """Check if page has substantial engagement."""
    try:
        likes_raw = lead.get('likes', '0')
        likes = int(re.sub(r'[^0-9]', '', str(likes_raw))) if str(likes_raw).strip() else 0
        return likes >= 1000  # At least 1K likes for "much engagement"
    except:
        return False

def is_product_seller(name):
    """Check if name suggests they sell products."""
    name_l = name.lower()
    # Exclude clearly non-product services
    service_only = ['bank', 'news', 'magazine', 'school', 'college',
                    'university', 'hospital', 'clinic', 'hotel', 'restaurant',
                    'cafe', 'food', 'pizza', 'burger', 'kabab', 'restaurant',
                    'salon', 'makeover', 'barber', 'gym', 'fitness',
                    'salon', 'spa', 'interior', 'paint', 'glass', 'mirror',
                    'decor', 'matrix', 'theater', 'cinema', 'hall',
                    'sport*', 'sporting', 'print*', 'printing',
                    'club', 'lounge', 'vlog', 'media', 'production',
                    'studio', 'architect', 'consulting', 'agency',
                    'institute', 'training', 'academy', 'travel', 'tour',
                    'insurance', 'real estate', 'property', 'broker',
                    'logistic', 'transport', 'express', 'courier']
    
    for svc in service_only:
        if svc.replace('*', '') in name_l:
            return False
    
    # These ARE product sellers
    product_hints = ['shop', 'store', 'mart', 'collection', 'fashion',
                     'wear', 'clothing', 'jewel', 'gold', 'diamond',
                     'baby', 'toy', 'kids', 'gadget', 'electronic',
                     'mobile', 'accessorie', 'cosmetic', 'beauty',
                     'skincare', 'perfume', 'footwear', 'shoe',
                     'leather', 'bag', 'gift', 'organic', 'handicraft',
                     'craft', 'handmade', 'products', 'brand', 'online',
                     'grocery', 'foodi', 'supermarket', 'lifestyle',
                     'enterprise', 'corporation', 'ware', 'trading',
                     'international', 'limited', 'ltd', 'bd',
                     'bazaar', 'mart', 'wholesale', 'retail',
                     'boutique', 'art', 'decor', 'home', 'kitchen',
                     'toys', 'sport', 'perfume', 'fragrance',
                     'electronics', 'gift', 'books', 'stationery',
                     'halal', 'shopping', 'dreamer', 'gallery',
                     'fency', 'skin care', 'baby', 'mum', 'angel',
                     'little', 'paradise', 'blue', 'pink', 'bird',
                     'palli', 'sarmin', 'story brand', 'hlwcraft',
                     'craftimation', 'family', 'living', 'life']
    
    return any(h in name_l for h in product_hints)

# ── Apply filters ──
valid = []
for l in all_leads:
    name = (l.get('name') or '').strip()
    if not name:
        continue
    
    # Filter chain
    if not is_valid_name(name):
        continue
    if not is_bangladesh(l):
        continue
    if not is_running_ads(l):
        continue
    
    # For "much engagement", require at least 1K likes
    # But allow lower if they have phone AND no website (hot lead)
    try:
        likes_raw = l.get('likes', '0')
        likes = int(re.sub(r'[^0-9]', '', str(likes_raw))) if str(likes_raw).strip() else 0
    except:
        likes = 0
    
    phone = (l.get('phone') or '').strip()
    has_web = l.get('has_website', '').strip().lower() in ('yes', 'true', 'y', '1')
    
    # Low engagement + has website = skip (they're not proven sellers)
    if likes < 1000 and has_web:
        continue
    
    # Even without likes, require at least a phone to be valid
    if likes < 100 and not phone:
        continue
    
    valid.append(l)

# ── Sort by likes descending (engagement first) ──
def get_likes(l):
    try:
        return int(re.sub(r'[^0-9]', '', str(l.get('likes', '0'))))
    except:
        return 0

valid.sort(key=lambda l: (-get_likes(l)))

# ── Print results ──
print(f"\n{'='*70}")
print(f"🔥 VALID ACTIVE PRODUCT-SELLERS: {len(valid)}")
print(f"{'='*70}\n")

for i, l in enumerate(valid[:50], 1):
    name = (l.get('name') or '')[:45]
    phone = (l.get('phone') or '').strip() or 'N/A'
    likes = get_likes(l)
    has_web = l.get('has_website', '').strip().lower() in ('yes', 'true', 'y', '1')
    score = l.get('score', '0')
    url = (l.get('url') or '')
    
    hot = "🔥" if not has_web and phone != 'N/A' else ""
    print(f" {i:2d}. {hot} [{score}/12] {name:45s}")
    print(f"     👍 {likes:>8,} | 📞 {phone:15s} | {'❌ No website' if not has_web else '✅ Website'}")
    print(f"     🔗 {url}")
    print()

# ── Save to CSV ──
import os
os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
with open(OUT_CSV, 'w', newline='') as f:
    fields = ['name', 'phone', 'likes', 'has_website', 'email', 'url', 'score', 'ad_status', 'category']
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    for l in valid:
        cat = ''
        name_l = (l.get('name') or '').lower()
        if likes := get_likes(l):
            pass
        writer.writerow({
            'name': (l.get('name') or ''),
            'phone': (l.get('phone') or ''),
            'likes': likes,
            'has_website': 'No' if (l.get('has_website', '').strip().lower() in ('no', 'false', 'n', '') or not l.get('has_website', '').strip()) else 'Yes',
            'email': (l.get('email') or ''),
            'url': (l.get('url') or ''),
            'score': l.get('score', '0'),
            'ad_status': l.get('ad_status', ''),
            'category': ''
        })

print(f"\n✅ Saved {len(valid)} valid active leads to: {OUT_CSV}")
