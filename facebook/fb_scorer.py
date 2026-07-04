#!/usr/bin/env python3
"""KB-aligned lead scorer for Skarbol Tech.
Implements qualification_checklist.md green/red flag system.
Maps lead category to Skarbol product recommendation.
"""
from datetime import datetime, date
import re
import os
import sys

GREEN_FLAGS = {
    'low_followers':    'followers < 10000',
    'recent_posts':     'last_post within 50 days',
    'no_website':       'has_website is False or empty',
    'manual_ordering':  'description contains DM/inbox/WhatsApp order signals',
    'phone_only':       'has phone, no website',
    'operational_pain': 'description contains stock/availability/call signals',
    'target_vertical':  'category in Skarbol target verticals',
    'major_city':       'address contains major BD city',
    'has_address':      'physical address listed',
    'active_responses': 'engagement signals in description',
}

RED_FLAGS = {
    'inactive_6months': 'last_post > 180 days ago',
    'outside_bd':       'location not Bangladesh',
    'not_business':     'category is meme/entertainment/personal',
    'scam_signals':     'no real photos, no contact info',
    'multinational':    'name contains global brand indicators',
    'no_contact':       'no phone AND no email AND no website',
    'personal_profile': 'url contains /profile.php or personal indicators',
    'irrelevant':       'category is politics/news/blog',
}

SKARBOL_TARGET_VERTICALS = [
    'beauty', 'restaurant', 'healthcare', 'education', 'manufacturing',
    'retail', 'pharmacy', 'fitness', 'realestate', 'hotel', 'agriculture',
    'automotive', 'services', 'general',
]

KB_PRODUCT_ALIGNMENT = {
    'beauty':         {'product': 'Quick Website Package', 'entry': 'Demo website', 'upsell': 'ExecMate EOS'},
    'restaurant':     {'product': 'Quick Website Package', 'entry': 'Online menu', 'upsell': 'ExecERP'},
    'healthcare':     {'product': 'MediLab LIMS', 'entry': 'Patient records', 'upsell': 'ExecMate EOS'},
    'education':      {'product': 'Smart Campus', 'entry': 'Attendance system', 'upsell': 'ExecMate EOS'},
    'manufacturing':  {'product': 'ExecERP', 'entry': 'Inventory module', 'upsell': 'ExecMate EOS'},
    'retail':         {'product': 'Quick Website Package', 'entry': 'Product catalog', 'upsell': 'ExecERP'},
    'pharmacy':       {'product': 'Quick Website Package', 'entry': 'Medicine catalog', 'upsell': 'MediLab LIMS'},
    'fitness':        {'product': 'Quick Website Package', 'entry': 'Booking page', 'upsell': 'ExecMate EOS'},
    'agriculture':    {'product': 'CattleSync', 'entry': 'Farm records', 'upsell': 'ExecERP'},
    'hotel':          {'product': 'Quick Website Package', 'entry': 'Booking page', 'upsell': 'ExecERP'},
    'realestate':     {'product': 'Custom Software', 'entry': 'Property listing', 'upsell': 'ExecMate EOS'},
    'automotive':     {'product': 'Quick Website Package', 'entry': 'Service booking', 'upsell': 'ExecERP'},
    'services':       {'product': 'Quick Website Package', 'entry': 'Service catalog', 'upsell': 'ExecMate EOS'},
    'general':        {'product': 'Quick Website Package', 'entry': 'Business profile', 'upsell': 'ExecMate EOS'},
}

MAJOR_CITIES = ['dhaka', 'chattogram', 'chittagong', 'khulna', 'sylhet',
                'rajshahi', 'barisal', 'rangpur', 'mymensingh', 'narayanganj', 'gazipur']

MANUAL_ORDER_SIGNALS = ['dm to order', 'inbox to order', 'whatsapp', 'message to buy',
                        'call to order', 'comment to order', 'send message', 'inbox us']

OPERATIONAL_PAIN_SIGNALS = ['stock running out', 'call for availability', 'limited stock',
                             'cash on delivery', 'delivery available', 'home delivery']

MULTINATIONAL_SIGNALS = ['coca cola', 'pepsi', 'kfc', 'mcdonalds', 'unilever',
                          'samsung', 'apple', 'nokia', 'grameenphone', 'robi', 'airtel', 'banglalink']


def days_since(date_str):
    if not date_str:
        return 999
    try:
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%B %d, %Y']:
            try:
                d = datetime.strptime(date_str, fmt).date()
                return (date.today() - d).days
            except ValueError:
                continue
    except Exception:
        pass
    r = date_str.lower().strip()
    m = re.search(r'(\d+)\s*(hour|hours|day|days|week|weeks|month|months|year|years)\s*ago', r)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if 'hour' in unit:
            return 0
        if 'day' in unit:
            return n
        if 'week' in unit:
            return n * 7
        if 'month' in unit:
            return n * 30
        if 'year' in unit:
            return n * 365
    if 'just now' in r or 'minute' in r:
        return 0
    return 999


def score_lead_kb(lead):
    score = 5
    green = []
    red = []

    name = (lead.get('business_name') or '').lower()
    desc = (lead.get('description') or lead.get('notes', '') or '').lower()
    addr = (lead.get('address') or '').lower()
    cat = (lead.get('category') or 'general').lower()
    url = (lead.get('page_url') or lead.get('url') or '').lower()

    followers_raw = lead.get('followers', 0)
    try:
        followers = int(str(followers_raw).replace(',', '').split()[0])
    except (ValueError, IndexError):
        followers = 0

    hw = lead.get('has_website', '')
    has_website = str(hw).lower() not in ('false', 'no', '', 'none', '0', 'f', 'n')

    if followers > 0 and followers < 10000:
        score += 1
        green.append('low_followers')

    days_old = days_since(lead.get('last_post_date', ''))
    if days_old <= 50:
        score += 1
        green.append('recent_posts')
    elif days_old <= 90:
        score -= 2
        green.append('recent_posts')
    elif days_old > 180:
        score -= 4
        red.append('inactive_6months')

    if not has_website:
        score += 1
        green.append('no_website')

    if any(sig in desc for sig in MANUAL_ORDER_SIGNALS):
        score += 1
        green.append('manual_ordering')

    if lead.get('phone') and not has_website:
        score += 1
        green.append('phone_only')

    if any(sig in desc for sig in OPERATIONAL_PAIN_SIGNALS):
        score += 1
        green.append('operational_pain')

    if cat in SKARBOL_TARGET_VERTICALS:
        score += 1
        green.append('target_vertical')

    if any(city in addr for city in MAJOR_CITIES):
        score += 1
        green.append('major_city')

    if addr and len(addr) > 10:
        score += 1
        green.append('has_address')

    if 'bangladesh' not in addr and 'dhaka' not in addr and 'bd' not in addr:
        phone = lead.get('phone', '')
        if not phone.startswith('+880') and not phone.startswith('880') and not phone.startswith('01'):
            score -= 2
            red.append('outside_bd')

    if any(b in name for b in MULTINATIONAL_SIGNALS):
        score -= 2
        red.append('multinational')

    if not lead.get('phone') and not lead.get('email') and not has_website:
        score -= 2
        red.append('no_contact')

    if '/profile.php' in url:
        score -= 2
        red.append('personal_profile')

    score = max(1, min(10, score))

    kb = KB_PRODUCT_ALIGNMENT.get(cat, KB_PRODUCT_ALIGNMENT['general'])

    if score >= 8:
        priority = 'immediate'
    elif score >= 6:
        priority = 'queue'
    elif score >= 4:
        priority = 'low'
    else:
        priority = 'discard'

    notes = f"Green: {', '.join(green) or 'none'} | Red: {', '.join(red) or 'none'}"

    return {
        'score': score,
        'green_flags': green,
        'red_flags': red,
        'kb_product': kb['product'],
        'kb_entry': kb['entry'],
        'kb_upsell': kb['upsell'],
        'priority': priority,
        'notes': notes,
    }


def score_and_update(lead):
    result = score_lead_kb(lead)
    lead['qualification_score'] = str(result['score'])
    lead['kb_product'] = result['kb_product']
    lead['kb_entry'] = result['kb_entry']
    lead['kb_upsell'] = result['kb_upsell']
    lead['priority'] = result['priority']
    lead['notes'] = result['notes']
    lead['green_flags'] = ','.join(result['green_flags'])
    lead['red_flags'] = ','.join(result['red_flags'])
    return lead


if __name__ == '__main__':
    tests = [
        {'business_name': 'Beauty Parlor', 'category': 'beauty', 'followers': '5000',
         'has_website': 'false', 'phone': '+8801712345678', 'address': 'Gulshan, Dhaka',
         'last_post_date': '2 days ago', 'description': 'DM to order, home delivery'},
        {'business_name': 'Big Corp', 'category': 'manufacturing', 'followers': '50000',
         'has_website': 'true', 'phone': '', 'address': 'New York',
         'last_post_date': '2 years ago', 'description': 'Official page'},
        {'business_name': 'Local Shop', 'category': 'retail', 'followers': '200',
         'has_website': 'no', 'phone': '+8801987654321', 'address': 'Mirpur, Dhaka, Bangladesh',
         'last_post_date': '5 days ago', 'description': 'inbox to order, cash on delivery'},
    ]
    for t in tests:
        r = score_lead_kb(t)
        print(f"\n{t['business_name']}:")
        print(f"  Score: {r['score']}/10 | Priority: {r['priority']}")
        print(f"  Product: {r['kb_product']} -> {r['kb_entry']} (upsell: {r['kb_upsell']})")
        print(f"  Green: {r['green_flags']}")
        print(f"  Red: {r['red_flags']}")
        print(f"  Notes: {r['notes']}")
