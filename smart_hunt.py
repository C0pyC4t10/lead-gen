#!/usr/bin/env python3
"""smart_hunt.py \u2014 High-engagement Bangladesh F-Commerce lead finder.

Finds Facebook businesses selling physical products via inbox/WhatsApp
without proper e-commerce websites. Uses Serper.dev for discovery,
Apify facebook-pages-scraper for enrichment, and scores leads 0-22.

Usage:
  python3 smart_hunt.py --category beauty
  python3 smart_hunt.py --category beauty,fashion,bags --count 30 --min-score 14
  python3 smart_hunt.py --category all --dry-run
  python3 smart_hunt.py --category home --no-apify --count 10
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, date, timedelta
from urllib.parse import urlparse

import requests

try:
    from tqdm import tqdm
except ImportError:
    tqdm = None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
APIFY_API_KEY = os.environ.get('APIFY_API_KEY', '')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = "-1004334910291"
TELEGRAM_THREAD_ID = 354

LEAD_GEN_API = 'http://localhost:8800/api/lead'

# \u2500\u2500 Category Search Queries \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

CATEGORY_QUERIES = {
    "skincare": [
        "skincare bd inbox order site:facebook.com",
        "\u09b8\u09cd\u0995\u09bf\u09a8\u0995\u09c7\u09af\u09bc\u09be\u09b0 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "face serum bangladesh whatsapp order site:facebook.com",
        "glow skincare dhaka inbox site:facebook.com",
        "skincare products cash on delivery bangladesh site:facebook.com",
    ],
    "cosmetics": [
        "cosmetics bd inbox order site:facebook.com",
        "\u09aa\u09cd\u09b0\u09b8\u09be\u09a7\u09a8\u09c0 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "makeup products bd whatsapp site:facebook.com",
        "cosmetics shop dhaka cash on delivery site:facebook.com",
        "beauty cosmetics bangladesh inbox site:facebook.com",
    ],
    "fashion": [
        "fashion house bd inbox order site:facebook.com",
        "\u09ab\u09cd\u09af\u09be\u09b6\u09a8 \u09b9\u09be\u0989\u09b8 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "dress collection bd whatsapp order site:facebook.com",
        "ladies fashion dhaka inbox site:facebook.com",
        "fashion collection cash on delivery bd site:facebook.com",
    ],
    "boutique": [
        "boutique dhaka inbox order site:facebook.com",
        "\u09ac\u09c1\u099f\u09bf\u0995 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "boutique house bd whatsapp site:facebook.com",
        "boutique collection dhaka cash on delivery site:facebook.com",
        "\u09ac\u09c1\u099f\u09bf\u0995 \u09b6\u09aa \u09a2\u09be\u0995\u09be inbox site:facebook.com",
    ],
    "jewelry": [
        "jewelry shop bd inbox order site:facebook.com",
        "\u099c\u09c1\u09af\u09bc\u09c7\u09b2\u09be\u09b0\u09bf \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "gold jewelry dhaka whatsapp order site:facebook.com",
        "\u0997\u09b9\u09a8\u09be \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 inbox site:facebook.com",
        "jewelry collection bd cash on delivery site:facebook.com",
    ],
    "perfume": [
        "perfume bd inbox order site:facebook.com",
        "\u0986\u09a4\u09b0 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "perfume shop dhaka whatsapp site:facebook.com",
        "\u09b8\u09c1\u0997\u09a8\u09cd\u09a7\u09bf \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 inbox site:facebook.com",
        "fragrance bd cash on delivery site:facebook.com",
    ],
    "baby": [
        "baby products bd inbox order site:facebook.com",
        "\u09b6\u09bf\u09b6\u09c1 \u09aa\u09a3\u09cd\u09af \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "baby shop dhaka whatsapp order site:facebook.com",
        "baby items bangladesh cash on delivery site:facebook.com",
        "\u09b6\u09bf\u09b6\u09c1 \u09aa\u09a3\u09cd\u09af \u09a2\u09be\u0995\u09be inbox site:facebook.com",
    ],
    "bags": [
        "bags collection bd inbox order site:facebook.com",
        "\u09ac\u09cd\u09af\u09be\u0997 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "handbag shop dhaka whatsapp site:facebook.com",
        "ladies bag bd cash on delivery site:facebook.com",
        "purse collection bangladesh inbox site:facebook.com",
    ],
    "home": [
        "home decor bd inbox order site:facebook.com",
        "\u0997\u09c3\u09b9\u09b8\u099c\u09cd\u099c\u09be \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "home products dhaka whatsapp order site:facebook.com",
        "household items bd cash on delivery site:facebook.com",
        "home accessories bangladesh inbox site:facebook.com",
    ],
    "food": [
        "homemade food bd inbox order site:facebook.com",
        "\u0998\u09b0\u09c7 \u09a4\u09c8\u09b0\u09bf \u0996\u09be\u09ac\u09be\u09b0 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "food delivery dhaka whatsapp order site:facebook.com",
        "\u0996\u09be\u09ac\u09be\u09b0 \u09a1\u09c7\u09b2\u09bf\u09ad\u09be\u09b0\u09bf \u09a2\u09be\u0995\u09be inbox site:facebook.com",
        "homemade food cash on delivery bd site:facebook.com",
    ],
    "fruit": [
        "fresh fruit bd inbox order site:facebook.com",
        "\u09a4\u09be\u099c\u09be \u09ab\u09b2 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "fruit delivery dhaka whatsapp site:facebook.com",
        "organic fruit bangladesh inbox site:facebook.com",
        "\u09ab\u09b2 \u09a1\u09c7\u09b2\u09bf\u09ad\u09be\u09b0\u09bf \u09a2\u09be\u0995\u09be site:facebook.com",
    ],
    "nursery": [
        "plant nursery bd inbox order site:facebook.com",
        "\u0997\u09be\u099b\u09aa\u09be\u09b2\u09be \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "nursery dhaka whatsapp order site:facebook.com",
        "indoor plants bangladesh inbox site:facebook.com",
        "\u0997\u09be\u099b \u09ac\u09bf\u0995\u09cd\u09b0\u09bf \u09a2\u09be\u0995\u09be site:facebook.com",
    ],
    "clothing_brand": [
        "clothing brand bd inbox order site:facebook.com",
        "\u09aa\u09cb\u09b6\u09be\u0995 \u09ac\u09cd\u09b0\u09cd\u09af\u09be\u09a8\u09cd\u09a1 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "t-shirt brand dhaka whatsapp site:facebook.com",
        "\u09aa\u09cb\u09b6\u09be\u0995 \u0995\u09be\u09b2\u09c7\u0995\u09b6\u09a8 inbox order site:facebook.com",
        "clothing brand cash on delivery bd site:facebook.com",
    ],
    "jewelry_watches": [
        "watch shop bd inbox order site:facebook.com",
        "\u0998\u09a1\u09bc\u09bf \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "jewelry watches dhaka whatsapp site:facebook.com",
        "\u0998\u09a1\u09bc\u09bf \u0993 \u0997\u09b9\u09a8\u09be bangladesh inbox site:facebook.com",
        "watches collection bd cash on delivery site:facebook.com",
    ],
    "bags_luggage": [
        "luggage shop bd inbox order site:facebook.com",
        "\u09b2\u09be\u0997\u09c7\u099c \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "travel bag dhaka whatsapp order site:facebook.com",
        "\u099f\u09cd\u09b0\u09be\u09ad\u09c7\u09b2 \u09ac\u09cd\u09af\u09be\u0997 bangladesh inbox site:facebook.com",
        "luggage collection bd cash on delivery site:facebook.com",
    ],
    "health_beauty": [
        "health beauty bd inbox order site:facebook.com",
        "\u09b8\u09cd\u09ac\u09be\u09b8\u09cd\u09a5\u09cd\u09af \u0993 \u09b8\u09cc\u09a8\u09cd\u09a6\u09b0\u09cd\u09af \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "health products dhaka whatsapp site:facebook.com",
        "beauty health bangladesh inbox site:facebook.com",
        "\u09b8\u09cd\u09ac\u09be\u09b8\u09cd\u09a5\u09cd\u09af \u09aa\u09a3\u09cd\u09af bd cash on delivery site:facebook.com",
    ],
    "cosmetics_store": [
        "cosmetics store bd inbox site:facebook.com",
        "\u0995\u09b8\u09ae\u09c7\u099f\u09bf\u0995\u09cd\u09b8 \u09b6\u09aa \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "beauty store dhaka whatsapp order site:facebook.com",
        "\u0995\u09b8\u09ae\u09c7\u099f\u09bf\u0995\u09cd\u09b8 \u09a1\u09c7\u09b2\u09bf\u09ad\u09be\u09b0\u09bf bangladesh inbox site:facebook.com",
        "makeup store bd cash on delivery site:facebook.com",
    ],
    "personal_care": [
        "personal care products bd inbox site:facebook.com",
        "\u09ac\u09cd\u09af\u0995\u09cd\u09a4\u09bf\u0997\u09a4 \u09af\u09a4\u09cd\u09a8 \u09aa\u09a3\u09cd\u09af \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "personal care dhaka whatsapp order site:facebook.com",
        "hygiene products bangladesh inbox site:facebook.com",
        "personal care bd cash on delivery site:facebook.com",
    ],
    "home_decor": [
        "home decor shop bd inbox site:facebook.com",
        "\u09b9\u09cb\u09ae \u09a1\u09c7\u0995\u09cb\u09b0 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "interior decor dhaka whatsapp order site:facebook.com",
        "\u0998\u09b0 \u09b8\u09be\u099c\u09be\u09a8\u09cb \u09aa\u09a3\u09cd\u09af bangladesh inbox site:facebook.com",
        "home decoration bd cash on delivery site:facebook.com",
    ],
    "kitchen_cooking": [
        "kitchen products bd inbox order site:facebook.com",
        "\u09b0\u09be\u09a8\u09cd\u09a8\u09be\u0998\u09b0 \u09aa\u09a3\u09cd\u09af \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "cookware dhaka whatsapp order site:facebook.com",
        "\u09b0\u09be\u09a8\u09cd\u09a8\u09be\u09b0 \u09b8\u09b0\u099e\u09cd\u099c\u09be\u09ae bangladesh inbox site:facebook.com",
        "kitchen items bd cash on delivery site:facebook.com",
    ],
    "furniture_store": [
        "furniture shop bd inbox order site:facebook.com",
        "\u0986\u09b8\u09ac\u09be\u09ac\u09aa\u09a4\u09cd\u09b0 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "furniture dhaka whatsapp order site:facebook.com",
        "\u0986\u09b8\u09ac\u09be\u09ac \u09a2\u09be\u0995\u09be inbox site:facebook.com",
        "furniture bd cash on delivery site:facebook.com",
    ],
    "patio_garden": [
        "garden products bd inbox site:facebook.com",
        "\u09ac\u09be\u0997\u09be\u09a8 \u09aa\u09a3\u09cd\u09af \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "outdoor garden dhaka whatsapp site:facebook.com",
        "\u0997\u09be\u09b0\u09cd\u09a1\u09c7\u09a8\u09bf\u0982 bangladesh inbox site:facebook.com",
        "garden tools bd cash on delivery site:facebook.com",
    ],
    "electronics": [
        "electronics shop bd inbox order site:facebook.com",
        "\u0987\u09b2\u09c7\u0995\u099f\u09cd\u09b0\u09a8\u09bf\u0995\u09cd\u09b8 \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "gadgets dhaka whatsapp order site:facebook.com",
        "\u0987\u09b2\u09c7\u0995\u099f\u09cd\u09b0\u09a8\u09bf\u0995\u09cd\u09b8 \u09aa\u09a3\u09cd\u09af bd inbox site:facebook.com",
        "electronics cash on delivery bangladesh site:facebook.com",
    ],
    "games_toys": [
        "toys shop bd inbox order site:facebook.com",
        "\u0996\u09c7\u09b2\u09a8\u09be \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "games toys dhaka whatsapp order site:facebook.com",
        "\u09b6\u09bf\u09b6\u09c1\u09a6\u09c7\u09b0 \u0996\u09c7\u09b2\u09a8\u09be bangladesh inbox site:facebook.com",
        "toys cash on delivery bd site:facebook.com",
    ],
    "outdoor_sporting": [
        "sports products bd inbox order site:facebook.com",
        "\u0995\u09cd\u09b0\u09c0\u09a1\u09bc\u09be \u09b8\u09b0\u099e\u09cd\u099c\u09be\u09ae \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "outdoor gear dhaka whatsapp order site:facebook.com",
        "sporting goods bangladesh inbox site:facebook.com",
        "sports equipment bd cash on delivery site:facebook.com",
    ],
    "food_beverage": [
        "food beverage bd inbox order site:facebook.com",
        "\u0996\u09be\u09a6\u09cd\u09af \u0993 \u09aa\u09be\u09a8\u09c0\u09af\u09bc \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "food products dhaka whatsapp order site:facebook.com",
        "\u09ac\u09c7\u09ad\u09be\u09b0\u09c7\u099c bangladesh inbox site:facebook.com",
        "food delivery bd cash on delivery site:facebook.com",
    ],
    "bakery": [
        "bakery bd inbox order site:facebook.com",
        "\u09ac\u09c7\u0995\u09be\u09b0\u09bf \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "cake shop dhaka whatsapp order site:facebook.com",
        "\u0995\u09c7\u0995 \u0993 \u09aa\u09c7\u09b8\u09cd\u099f\u09cd\u09b0\u09bf bangladesh inbox site:facebook.com",
        "homemade cake bd cash on delivery site:facebook.com",
    ],
    "specialty_grocery": [
        "specialty grocery bd inbox order site:facebook.com",
        "\u09ac\u09bf\u09b6\u09c7\u09b7 \u09ae\u09c1\u09a6\u09bf\u0996\u09be\u09a8\u09be \u09ac\u09be\u0982\u09b2\u09be\u09a6\u09c7\u09b6 site:facebook.com",
        "organic grocery dhaka whatsapp site:facebook.com",
        "\u09a6\u09c7\u09b6\u09bf \u09aa\u09a3\u09cd\u09af bangladesh inbox site:facebook.com",
        "specialty food bd cash on delivery site:facebook.com",
    ],
}

ALL_CATEGORIES = sorted(CATEGORY_QUERIES.keys())

# Map common aliases to actual category keys in CATEGORY_QUERIES
CATEGORY_ALIASES = {
    'beauty': ['skincare', 'cosmetics', 'health_beauty', 'personal_care', 'cosmetics_store'],
    'beauty salon': ['skincare', 'cosmetics', 'health_beauty', 'personal_care', 'cosmetics_store'],
    'clothing': ['fashion', 'boutique', 'clothing_brand'],
    'grocery': ['food_beverage', 'specialty_grocery', 'food', 'fruit'],
    'makeup': ['cosmetics', 'cosmetics_store', 'health_beauty'],
    'decor': ['home_decor', 'home', 'patio_garden'],
    'electronics': ['electronics', 'games_toys'],
}

# \u2500\u2500 URL helpers \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

BANNED_PATTERNS = [
    '/groups/', '/profile.php', '/people/', '/watch/',
    '/events/', '/marketplace/', '/pages/category',
    '/posts/', '/photos/', '/videos/', '/reel/',
    '/stories/', '/share/', '/story.php', '/photo.php',
]


def normalize_url(url):
    url = url.replace('m.facebook.com', 'www.facebook.com')
    for ch in ('?', '#'):
        idx = url.find(ch)
        if idx != -1:
            url = url[:idx]
    return url.rstrip('/')


def extract_slug(url):
    idx = url.find('facebook.com')
    if idx == -1:
        return None
    path = url[idx + len('facebook.com'):].lstrip('/')
    return path.split('/')[0] if path else None


def clean_url(url):
    url = normalize_url(url)
    slug = extract_slug(url)
    if slug:
        return f'https://www.facebook.com/{slug}/'
    return url


def is_valid_page(url):
    url_lower = url.lower()
    for pat in BANNED_PATTERNS:
        if pat in url_lower:
            return False
    slug = extract_slug(url)
    if not slug:
        return False
    if slug.lower() in ('login', 'signup', 'help', 'about', 'home', 'watch',
                        'gaming', 'marketplace', 'pages', 'groups', 'events',
                        'hashtag', 'media', 'photos', 'videos'):
        return False
    if not any(c.isalpha() for c in slug):
        return False
    if len(slug) < 3:
        return False
    return True


# \u2500\u2500 Step 1: Serper.dev Search \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

INBOX_KEYWORDS = [
    'inbox', 'whatsapp', '\u09ae\u09c7\u09b8\u09c7\u099c', '\u0985\u09b0\u09cd\u09a1\u09be\u09b0 \u0995\u09b0\u09c1\u09a8',
    'cash on delivery', '\u0995\u09cd\u09af\u09be\u09b6 \u0985\u09a8 \u09a1\u09c7\u09b2\u09bf\u09ad\u09be\u09b0\u09bf', '\u0987\u09a8\u09ac\u0995\u09cd\u09b8',
    'delivery all over bangladesh', 'home delivery available',
    'message to order', 'dm for price',
]


def extract_engagement(snippet):
    likes = 0
    talking_about = 0
    if not snippet:
        return likes, talking_about, False
    likes_match = re.search(r'([\d,.]+)\s*(?:likes|like)', snippet)
    if likes_match:
        try:
            likes = int(likes_match.group(1).replace(',', '').replace('.', ''))
        except ValueError:
            pass
    talking_match = re.search(r'([\d,.]+)\s*talking\s*about\s*(?:this|)', snippet)
    if talking_match:
        try:
            talking_about = int(talking_match.group(1).replace(',', '').replace('.', ''))
        except ValueError:
            pass
    if not likes:
        followers_match = re.search(r'([\d,.]+)\s*(?:followers|follows|follower)', snippet)
        if followers_match:
            try:
                likes = int(followers_match.group(1).replace(',', '').replace('.', ''))
            except ValueError:
                pass
    snippet_lower = snippet.lower()
    has_inbox_signal = any(kw in snippet_lower for kw in INBOX_KEYWORDS)
    return likes, talking_about, has_inbox_signal


def serper_search(query):
    if not SERPER_API_KEY:
        return []
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    payload = {'q': query, 'gl': 'bd', 'hl': 'en', 'num': 10}
    try:
        resp = requests.post(
            'https://google.serper.dev/search',
            headers=headers, json=payload, timeout=20
        )
        data = resp.json()
    except Exception as e:
        print(f"  Serper error: {e}")
        return []

    results = []
    seen = set()
    for r in data.get('organic', []):
        link = (r.get('link') or '').strip()
        if not link or 'facebook.com' not in link:
            continue
        clean = clean_url(link)
        if not is_valid_page(clean):
            continue
        if clean in seen:
            continue
        seen.add(clean)
        title = (r.get('title') or '').strip()
        snippet = (r.get('snippet') or '').strip()
        likes, talking, inbox_signal = extract_engagement(snippet)
        name = title.replace(' - Facebook', '').replace(' | Facebook', '').replace(' - Home | Facebook', '').strip()
        results.append({
            'url': clean,
            'name': name[:100],
            'likes': likes,
            'talking_about': talking,
            'snippet': snippet,
            'inbox_signal': inbox_signal,
        })
    return results


# \u2500\u2500 Step 2: Apify Facebook Pages Scraper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

APIFY_BASE = 'https://api.apify.com/v2'
ACTOR_ID = 'apify~facebook-pages-scraper'


def start_apify_run(page_urls):
    headers = {
        'Authorization': f'Bearer {APIFY_API_KEY}',
        'Content-Type': 'application/json',
    }
    payload = {
        'startUrls': [{'url': u} for u in page_urls],
        'maxPagesPerQuery': 1,
    }
    try:
        resp = requests.post(
            f'{APIFY_BASE}/acts/{ACTOR_ID}/runs',
            headers=headers, json=payload, timeout=30
        )
        data = resp.json()
        run_id = data.get('data', {}).get('id')
        return run_id
    except Exception as e:
        print(f"  Apify start error: {e}")
        return None


def poll_apify_run(run_id, timeout=600, interval=10):
    headers = {'Authorization': f'Bearer {APIFY_API_KEY}'}
    deadline = time.time() + timeout
    with _progress("Apify scraping", timeout) as pbar:
        while time.time() < deadline:
            try:
                resp = requests.get(
                    f'{APIFY_BASE}/actor-runs/{run_id}',
                    headers=headers, timeout=15
                )
                data = resp.json()
                status = data.get('data', {}).get('status', 'UNKNOWN')
                pbar.set_postfix_str(status.lower())
                if status == 'SUCCEEDED':
                    pbar.update(timeout)
                    return True
                if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
                    pbar.update(timeout)
                    return False
            except Exception:
                pass
            pbar.update(interval)
            time.sleep(interval)
    return False


def get_apify_results(run_id):
    headers = {'Authorization': f'Bearer {APIFY_API_KEY}'}
    try:
        resp = requests.get(
            f'{APIFY_BASE}/actor-runs/{run_id}/dataset/items',
            headers=headers, timeout=30
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def extract_apify_page(item):
    page_url = (item.get('pageUrl') or item.get('facebookUrl') or '').strip()
    page_name = (item.get('title') or '').strip()
    phone = (item.get('phone') or '').strip()
    email = (item.get('email') or '').strip()
    address = (item.get('address') or '').strip()
    website = (item.get('website') or '').strip()
    categories = item.get('categories') or []
    category_str = '; '.join(categories) if isinstance(categories, list) else str(categories)
    likes_raw = item.get('likes') or item.get('followers') or 0
    try:
        followers_int = int(re.sub(r'[^0-9]', '', str(likes_raw))) if likes_raw else 0
    except (ValueError, TypeError):
        followers_int = 0
    talking_raw = item.get('talkingAboutCount') or 0
    try:
        talking_about = int(re.sub(r'[^0-9]', '', str(talking_raw))) if talking_raw else 0
    except (ValueError, TypeError):
        talking_about = 0
    last_post = (item.get('lastPostDate') or item.get('creationDate') or '').strip()
    recent_posts = []
    for post in (item.get('recentPosts') or [])[:3]:
        recent_posts.append({
            'likes': post.get('likesCount') or post.get('likes', 0) or 0,
            'comments': post.get('commentsCount') or post.get('comments', 0) or 0,
            'shares': post.get('sharesCount') or post.get('shares', 0) or 0,
        })
    return {
        'page_url': page_url,
        'page_name': page_name,
        'followers': followers_int,
        'likes': followers_int,
        'talking_about': talking_about,
        'phone': phone,
        'email': email,
        'website': website,
        'address': address,
        'category': category_str,
        'last_post_date': last_post,
        'recent_posts': recent_posts,
    }


# \u2500\u2500 Step 3: Scoring \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

WEAK_WEBSITE_DOMAINS = [
    'blogspot.com', 'wordpress.com', 'wix.com', 'weebly.com',
    'site123.com', 'yolasite.com',
]


def is_weak_website(url):
    if not url:
        return False
    for d in WEAK_WEBSITE_DOMAINS:
        if d in url.lower():
            return True
    if url.startswith('http://') and not url.startswith('https://'):
        return True
    return False


def check_website(url, timeout=5):
    if not url:
        return 'none'
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            return 'none'
        return 'valid'
    except requests.RequestException:
        return 'none'


def extract_inbox_signals(text):
    if not text:
        return False
    tl = text.lower()
    return any(kw in tl for kw in INBOX_KEYWORDS)


def score_serper_only(entry):
    score = 0
    likes = entry.get('likes', 0)
    if likes >= 50000:
        score += 4
    elif likes >= 20000:
        score += 3
    elif likes >= 10000:
        score += 2
    elif likes >= 5000:
        score += 1
    talking = entry.get('talking_about', 0)
    if talking > 1000:
        score += 3
    elif talking >= 500:
        score += 2
    elif talking >= 100:
        score += 1
    if entry.get('inbox_signal'):
        score += 2
    return score


def score_lead_enriched(page, serper_entry, website_status):
    score = 0
    followers = page.get('followers', 0)
    if followers >= 50000:
        score += 4
    elif followers >= 20000:
        score += 3
    elif followers >= 10000:
        score += 2
    elif followers >= 5000:
        score += 1

    site = page.get('website', '')
    if website_status == 'none':
        score += 4
    elif is_weak_website(site):
        score += 2

    last_post = page.get('last_post_date', '')
    lpd_days = parse_post_recency(last_post)
    if lpd_days is not None:
        if lpd_days <= 3:
            score += 3
        elif lpd_days <= 7:
            score += 2
        elif lpd_days <= 14:
            score += 1

    talking = page.get('talking_about', 0)
    if talking > 1000:
        score += 3
    elif talking >= 500:
        score += 2
    elif talking >= 100:
        score += 1

    posts = page.get('recent_posts', [])
    if posts:
        avg_comments = sum(p.get('comments', 0) for p in posts) / len(posts)
        avg_likes = sum(p.get('likes', 0) for p in posts) / len(posts)
        avg_shares = sum(p.get('shares', 0) for p in posts) / len(posts)
        if avg_comments > 100:
            score += 2
        elif avg_comments > 20:
            score += 1
        if avg_likes > 500:
            score += 1
        if avg_shares > 50:
            score += 1
    else:
        avg_comments = 0

    if page.get('phone'):
        score += 1
    if page.get('email'):
        score += 1

    text_for_signals = ' '.join(filter(None, [
        serper_entry.get('snippet', '') if serper_entry else '',
        page.get('page_name', ''),
        page.get('category', ''),
    ]))
    if extract_inbox_signals(text_for_signals):
        score += 2

    return min(score, 22)


def parse_post_recency(date_str):
    if not date_str:
        return None
    date_str = str(date_str).lower()
    now = datetime.now()
    m = re.search(r'(\d+)\s*(hour|hours|h)\s*ago', date_str)
    if m:
        return int(m.group(1)) / 24
    m = re.search(r'(\d+)\s*(day|days|d)\s*ago', date_str)
    if m:
        return int(m.group(1))
    m = re.search(r'(\d+)\s*(week|weeks|w)\s*ago', date_str)
    if m:
        return int(m.group(1)) * 7
    m = re.search(r'(\d+)\s*(month|months|mon)\s*ago', date_str)
    if m:
        return int(m.group(1)) * 30
    if 'just now' in date_str or 'minute' in date_str:
        return 0
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return (now - dt).days
    except (ValueError, TypeError):
        pass
    try:
        dt = datetime.strptime(date_str, '%b %d, %Y')
        return (now - dt).days
    except (ValueError, TypeError):
        pass
    return None


def classify_priority(score):
    if score >= 18:
        return "PREMIUM"
    if score >= 14:
        return "HIGH"
    if score >= 10:
        return "MEDIUM"
    return "LOW"


# \u2500\u2500 Step 4: Save via server.py API \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

LEAD_COLUMNS = [
    'date', 'platform', 'business_name', 'page_url', 'category', 'followers',
    'email', 'phone', 'website', 'has_website', 'address', 'last_post_date',
    'qualification_score', 'status', 'notes', 'follow_up_date', 'open_state', 'hours_text',
]

_CACHE_FILE = os.path.join(os.path.dirname(__file__), 'collected_leads', 'pending_leads_cache.json')


def _load_lead_cache():
    if not os.path.exists(_CACHE_FILE):
        return []
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def _save_lead_cache(cached):
    os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
    with open(_CACHE_FILE, 'w') as f:
        json.dump(cached, f, indent=2)


def cache_lead(lead_dict):
    cached = _load_lead_cache()
    urls = {l['page_url'] for l in cached if l.get('page_url')}
    if lead_dict.get('page_url') in urls:
        return 'duplicate'
    cached.append(lead_dict)
    _save_lead_cache(cached)
    return 'cached'


def flush_lead_cache(verbose=True):
    cached = _load_lead_cache()
    if not cached:
        if verbose:
            print("  \u1f4ed No cached leads to flush.")
        return 0
    if verbose:
        print(f"  \u1f4e4 Flushing {len(cached)} cached leads to server...")
    flushed = 0
    remaining = []
    for lead in cached:
        result = post_lead(lead)
        if result == 'saved':
            flushed += 1
        elif result == 'duplicate':
            flushed += 1  # already in DB, count as processed
        else:
            remaining.append(lead)
    if remaining:
        _save_lead_cache(remaining)
    else:
        if os.path.exists(_CACHE_FILE):
            os.remove(_CACHE_FILE)
    if verbose:
        print(f"  \u2705 Flushed {flushed} leads ({len(remaining)} still cached)")
    return flushed


def post_lead(lead_dict):
    try:
        resp = requests.post(LEAD_GEN_API, json=lead_dict, timeout=10)
        result = resp.json()
        if result.get('status') == 'duplicate':
            return 'duplicate'
        if result.get('status') == 'saved':
            return 'saved'
        return f"error: {result}"
    except requests.ConnectionError:
        return 'server_offline'
    except Exception as e:
        return f"error: {e}"


def build_lead(page, category_name, score, priority, serper_entry, notes_extra=''):
    fud = (date.today() + timedelta(days=3)).isoformat()
    page_url = page.get('page_url', '') or serper_entry.get('url', '')
    business_name = page.get('page_name', '') or serper_entry.get('name', '')
    followers = page.get('followers', 0) or 0
    followers_str = f"{followers:,}" if followers else ''
    has_web = page.get('website', '')
    has_website_str = 'true' if has_web else 'false'
    last_post = page.get('last_post_date', '') or ''
    posts = page.get('recent_posts', [])
    avg_comments = 0
    if posts:
        avg_comments = sum(p.get('comments', 0) for p in posts) / len(posts)
    inbox = "yes" if serper_entry.get('inbox_signal') or extract_inbox_signals(business_name + ' ' + page.get('category', '')) else "no"
    notes = (
        f"Smart hunt [{category_name}]. Score: {score}/22. "
        f"Talking about: {page.get('talking_about', 0)}. "
        f"Avg comments: {avg_comments:.0f}. "
        f"Inbox signals: {inbox}. "
        f"Priority: {priority}."
    )
    if notes_extra:
        notes += f" {notes_extra}"
    return {
        'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'platform': 'facebook_smart',
        'business_name': business_name,
        'page_url': page_url,
        'category': category_name,
        'followers': followers_str,
        'email': page.get('email', ''),
        'phone': page.get('phone', ''),
        'website': page.get('website', '') or '',
        'has_website': has_website_str,
        'address': page.get('address', ''),
        'last_post_date': last_post,
        'qualification_score': str(score),
        'status': 'new',
        'notes': notes,
        'follow_up_date': fud,
        'open_state': '',
        'hours_text': '',
    }


# \u2500\u2500 Telegram Summary \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def send_telegram_summary(summary_text):
    if not TELEGRAM_TOKEN:
        return
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "message_thread_id": TELEGRAM_THREAD_ID,
            "text": summary_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json=payload, timeout=10
        )
    except Exception:
        pass


# \u2500\u2500 Progress helper \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _progress(desc, total):
    if tqdm:
        return tqdm(total=total, desc=desc, unit='s', leave=False)
    class _Dummy:
        def __enter__(self):
            print(f"  {desc}...", end='', flush=True)
            return self
        def __exit__(self, *args):
            print(' done', flush=True)
        def set_postfix_str(self, s):
            pass
        def update(self, n):
            pass
    return _Dummy()


# \u2500\u2500 Main Pipeline \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def run_category(category_name, queries, min_score, dry_run, no_apify, count, stop_event):
    all_urls = []
    serper_data = {}
    results = []
    query_iter = tqdm(queries, desc=f"  Serper [{category_name}]") if tqdm else queries
    for query in query_iter:
        if stop_event and stop_event():
            break
        entries = serper_search(query)
        time.sleep(1)
        for e in entries:
            if e['url'] not in serper_data:
                serper_data[e['url']] = e
                all_urls.append(e['url'])
        if stop_event and stop_event():
            break
    if not all_urls:
        return results
    enriched_map = {}
    apify_used = False
    if not no_apify and APIFY_API_KEY:
        url_batches = [all_urls[i:i + 50] for i in range(0, len(all_urls), 50)]
        for batch in url_batches:
            if stop_event and stop_event():
                break
            print(f"\n    \u1f4e4 Sending {len(batch)} URLs to Apify...")
            run_id = start_apify_run(batch)
            if run_id and poll_apify_run(run_id):
                items = get_apify_results(run_id)
                for item in items:
                    p = extract_apify_page(item)
                    if p['page_url']:
                        enriched_map[p['page_url']] = p
                apify_used = True
    elif not no_apify and not APIFY_API_KEY:
        pass
    score_iter = tqdm(all_urls, desc=f"  Scoring [{category_name}]") if tqdm else all_urls
    for url in score_iter:
        if stop_event and stop_event():
            break
        se = serper_data.get(url, {})
        if url in enriched_map:
            page = enriched_map[url]
            site = page.get('website', '')
            ws = check_website(site) if site else 'none'
            score = score_lead_enriched(page, se, ws)
        else:
            followers = se.get('likes', 0)
            page = {
                'page_url': url,
                'page_name': se.get('name', ''),
                'followers': followers,
                'talking_about': se.get('talking_about', 0),
                'phone': '',
                'email': '',
                'website': '',
                'address': '',
                'category': '',
                'last_post_date': '',
                'recent_posts': [],
            }
            if not no_apify and APIFY_API_KEY:
                score = score_serper_only(se)
            else:
                score = score_serper_only(se)
        if score >= min_score:
            if url in enriched_map:
                page_data = enriched_map[url]
            else:
                page_data = page
            priority = classify_priority(score)
            notes_extra = "serper_only" if url not in enriched_map and (not no_apify and APIFY_API_KEY) else ""
            lead = build_lead(page_data, category_name, score, priority, se, notes_extra)
            results.append((score, priority, lead))
    return results


def main():
    parser = argparse.ArgumentParser(
        description='Smart Hunt \u2014 High-engagement Bangladesh F-Commerce lead finder'
    )
    parser.add_argument('--category', '-c', default='all',
                        help='Category or comma-separated list (default: all)')
    parser.add_argument('--count', type=int, default=50,
                        help='Stop after N leads saved (default: 50)')
    parser.add_argument('--min-score', type=int, default=10,
                        help='Minimum score threshold (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Score but do not save to server')
    parser.add_argument('--no-apify', action='store_true',
                        help='Skip Apify enrichment, use Serper data only')
    parser.add_argument('--flush-cache', action='store_true',
                        help='Flush any cached leads to server and exit')
    args = parser.parse_args()
    if args.flush_cache:
        saved = 0
        while True:
            n = flush_lead_cache(verbose=True)
            if n == 0:
                break
            saved += n
        print(f"Total flushed from cache: {saved}")
        return
    # Auto-flush any cached leads before starting new hunt
    cached = _load_lead_cache()
    if cached:
        print(f"\u1f4e4 Found {len(cached)} cached leads \u2014 flushing to server...")
        flush_lead_cache(verbose=True)
    if not SERPER_API_KEY:
        print("ERROR: SERPER_API_KEY not set in .env")
        sys.exit(1)
    if args.category.strip().lower() == 'all':
        categories = ALL_CATEGORIES
    else:
        raw_cats = [c.strip() for c in args.category.split(',')]
        categories = []
        missing = []
        for c in raw_cats:
            if c in CATEGORY_QUERIES:
                categories.append(c)
            elif c in CATEGORY_ALIASES:
                categories.extend(CATEGORY_ALIASES[c])
            else:
                missing.append(c)
        if missing:
            print(f"Unknown categories: {missing}. Available: {', '.join(ALL_CATEGORIES)}")
            sys.exit(1)
        # Deduplicate expanded aliases
        categories = list(dict.fromkeys(categories))
    if not categories:
        print("No valid categories selected.")
        sys.exit(1)
    print(f"\n{'='*60}")
    print(f"\u1f3af SMART HUNT STARTING")
    print(f"   Categories: {', '.join(categories)}")
    print(f"   Min score:  {args.min_score}/22")
    print(f"   Dry run:    {args.dry_run}")
    print(f"   Apify:      {'DISABLED' if args.no_apify else 'ENABLED'}")
    print(f"   Max leads:  {args.count}")
    print(f"{'='*60}\n")
    start_time = time.time()
    stop = False
    def stop_event():
        return stop
    all_results = []
    for cat in categories:
        if stop:
            break
        queries = CATEGORY_QUERIES.get(cat, [])
        print(f"\n\u1f4c2 Category: {cat} ({len(queries)} queries)")
        results = run_category(cat, queries, args.min_score, args.dry_run, args.no_apify, args.count, stop_event)
        all_results.extend(results)
        all_results.sort(key=lambda x: -x[0])
        if len([r for r in all_results if r[0] >= args.min_score]) >= args.count:
            stop = True
            break
    all_results.sort(key=lambda x: -x[0])
    saved_count = 0
    premium_count = 0
    high_count = 0
    medium_count = 0
    skip_dup_count = 0
    saved_leads = []
    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"\u1f50d DRY RUN \u2014 Would save {len(all_results)} leads")
    else:
        print(f"\n{'='*60}")
        print(f"\u1f4be SAVING to Lead Gen Dashboard...")
        print(f"{'='*60}\n")
        save_iter = tqdm(all_results, desc="  Saving") if tqdm else all_results
        for score, priority, lead in save_iter:
            if saved_count >= args.count:
                break
            result = post_lead(lead)
            if result == 'saved':
                saved_count += 1
                saved_leads.append((score, priority, lead))
                if priority == "PREMIUM":
                    premium_count += 1
                elif priority == "HIGH":
                    high_count += 1
                elif priority == "MEDIUM":
                    medium_count += 1
            elif result == 'duplicate':
                skip_dup_count += 1
            elif result == 'server_offline':
                print("\n  \u26a0\ufe0f Lead gen server offline \u2014 caching leads locally...")
                cached_count = 0
                for s, p, l in save_iter:
                    if saved_count >= args.count:
                        break
                    cr = cache_lead(l)
                    if cr == 'cached':
                        cached_count += 1
                print(f"  \u1f4e6 Cached {cached_count} leads locally (will auto-flush when server is back)")
                saved_count = cached_count
                break
    duration = time.time() - start_time
    dur_str = f"{duration:.0f}s"
    total_found = len(all_results)
    enriched = sum(1 for r in all_results if 'serper_only' not in r[2].get('notes', ''))
    print(f"\n{'='*60}")
    print(f"\u1f3af Smart Hunt Complete")
    print(f"   \u1f4c2 Categories: {', '.join(categories)}")
    print(f"   \u1f50d URLs found: {total_found}")
    print(f"   \u1f4ca Enriched via Apify: {enriched}")
    if skip_dup_count:
        print(f"   \u23ed Skipped (already in DB): {skip_dup_count}")
    if saved_count >= 0:
        print(f"   \u2705 Saved leads: {saved_count}")
        print(f"   \u1f525 PREMIUM: {premium_count}")
        print(f"   \u2b50 HIGH: {high_count}")
        print(f"   \u1f7e1 MEDIUM: {medium_count}")
    else:
        print(f"   \u274c Saved leads: 0 (server offline)")
    print(f"   \u23f1 Time: {dur_str}")
    print(f"{'='*60}\n")
    for score, priority, lead in saved_leads[:saved_count if saved_count > 0 else 10]:
        print(f"  [{score:2d}/22] {priority:7s} | {lead['business_name'][:40]:40s} | {lead['page_url']}")
    summary = (
        f"\u1f3af Smart Hunt Complete\n"
        f"\u1f4c2 Categories: {', '.join(categories)}\n"
        f"\u1f50d URLs found: {total_found}\n"
        f"\u1f4ca Enriched via Apify: {enriched}\n"
        f"\u2705 Saved leads: {saved_count if saved_count >= 0 else 0}\n"
        f"\u1f525 PREMIUM: {premium_count}\n"
        f"\u2b50 HIGH: {high_count}\n"
        f"\u1f7e1 MEDIUM: {medium_count}\n"
        f"\u23f1 Time: {dur_str}"
    )
    if skip_dup_count:
        summary += f"\n\u23ed Skipped existing: {skip_dup_count}"
    send_telegram_summary(summary)


if __name__ == '__main__':
    main()
