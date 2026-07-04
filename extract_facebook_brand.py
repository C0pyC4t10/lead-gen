#!/usr/bin/env python3
"""extract_facebook_brand.py — Scrape a Facebook page for brand info.

Extracts: business name, logo URL, cover photo URL, brand category,
about text, email, phone, website, and dominant brand colors from
the cover image (via ColorThief if available).

Usage:
  python3 extract_facebook_brand.py "https://www.facebook.com/bellabd.bd"
  python3 extract_facebook_brand.py "bellabd.bd" --json
"""

import argparse
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from lead_gen_outreach import CATEGORY_PRODUCTS, CATEGORY_STORE_NAMES


UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)


def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not raw.startswith("http"):
        raw = "https://www.facebook.com/" + raw.lstrip("@").lstrip("/")
    parsed = urlparse(raw)
    if "facebook.com" not in parsed.netloc:
        raw = "https://www.facebook.com/" + parsed.path.lstrip("/")
    return raw


def fetch_page(url: str) -> str:
    """Try to fetch a Facebook page. Falls back to mbasic.facebook.com."""
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    ]
    for ua in uas:
        try:
            resp = requests.get(url, headers={"User-Agent": ua}, timeout=15)
            if resp.ok and "login" not in resp.url.lower():
                return resp.text
        except requests.RequestException:
            pass
    # Try mbasic fallback
    mbasic_url = url.replace("www.facebook.com", "mbasic.facebook.com")
    mbasic_url = mbasic_url.replace("facebook.com", "mbasic.facebook.com")
    try:
        resp = requests.get(mbasic_url, headers={"User-Agent": uas[1]}, timeout=15)
        if resp.ok and "login" not in resp.url.lower():
            return resp.text
    except requests.RequestException:
        pass
    raise ConnectionError("Facebook blocked the request. Try providing info manually.")


def extract_meta(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    return tag.get("content", "").strip() if tag else ""


def extract_og_image(soup: BeautifulSoup) -> str:
    return extract_meta(soup, "og:image")


def extract_from_script(soup: BeautifulSoup) -> dict:
    """Try to extract brand info from LD+JSON or application/json scripts."""
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, TypeError):
            pass
    return {}


def extract_colors_from_url(img_url: str, count: int = 4) -> list:
    """Download image and extract dominant colors. Returns hex strings."""
    if not img_url:
        return []
    try:
        from colorthief import ColorThief
        from io import BytesIO
        resp = requests.get(img_url, headers={"User-Agent": UA}, timeout=10)
        if not resp.ok:
            return []
        ct = ColorThief(BytesIO(resp.content))
        palette = ct.get_palette(color_count=count, quality=10)
        return ["#%02x%02x%02x" % c for c in palette]
    except ImportError:
        return []
    except Exception:
        return []


class FacebookBrandExtractor:
    def __init__(self, page_url: str):
        self.url = normalize_url(page_url)
        self.html = ""
        self.soup = None
        self.result = {
            "url": self.url,
            "name": "",
            "username": "",
            "category": "",
            "about": "",
            "logo_url": "",
            "cover_url": "",
            "email": "",
            "phone": "",
            "website": "",
            "canonical_category": "general",
            "brand_colors": [],
            "confidence": "low",
        }

    def run(self) -> dict:
        try:
            self.html = fetch_page(self.url)
        except Exception as e:
            self.result["error"] = str(e)
            return self.result

        self.soup = BeautifulSoup(self.html, "html.parser")

        # Business name — try og:title, then title tag
        self.result["name"] = extract_meta(self.soup, "og:title") or ""
        if not self.result["name"]:
            title_tag = self.soup.find("title")
            if title_tag:
                self.result["name"] = title_tag.get_text(strip=True)
        # Clean up Facebook suffix
        self.result["name"] = re.sub(
            r"\s*[|–-]\s*(Facebook|Home|Posts|Photos).*$", "", self.result["name"]
        ).strip()

        # Logo / profile picture
        og_img = extract_og_image(self.soup) or ""
        if og_img:
            self.result["logo_url"] = og_img

        # Cover photo from meta
        for tag in self.soup.find_all("meta", attrs={"name": "twitter:image"}):
            self.result["cover_url"] = tag.get("content", "")

        # If no cover, try to find image with cover-like class
        if not self.result["cover_url"]:
            for img in self.soup.find_all("img"):
                src = img.get("src", "")
                if "cover" in src.lower() and not self.result["cover_url"]:
                    self.result["cover_url"] = src
                cls = " ".join(img.get("class", []))
                if "cover" in cls.lower() and not self.result["cover_url"]:
                    self.result["cover_url"] = src

        # Username from URL path
        path = urlparse(self.url).path.strip("/").split("?")[0].split("/")[0]
        self.result["username"] = path

        # About text from meta description
        self.result["about"] = extract_meta(self.soup, "description") or ""

        # Detect category from name + about text
        text = (self.result["name"] + " " + self.result["about"]).lower()
        self.result["category"] = detect_category(text)

        # Extract canonical
        self.result["canonical_category"] = find_canonical(self.result["category"])

        # Try to extract structured data
        ld = extract_from_script(self.soup)
        if ld:
            self.result["email"] = ld.get("email", "")
            self.result["phone"] = ld.get("telephone", "")
            self.result["website"] = ""
            for same_as in ld.get("sameAs", []):
                if isinstance(same_as, str) and "facebook.com" not in same_as.lower():
                    self.result["website"] = same_as
                    break

        # Also scrape for contact info in text
        phones = re.findall(r"(?:01[3-9]\d{8}|\+8801[3-9]\d{8})", self.html)
        if phones:
            self.result["phone"] = phones[0]
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", self.html)
        valid_emails = [
            e for e in emails
            if not any(d in e.lower() for d in ["facebook", "example", "fb.com"])
        ]
        if valid_emails:
            self.result["email"] = valid_emails[0]

        # Extract brand colors from cover image
        cover = self.result.get("cover_url") or self.result.get("logo_url")
        if cover:
            colors = extract_colors_from_url(cover)
            if colors:
                self.result["brand_colors"] = colors

        # Confidence
        if self.result["name"] and self.result["logo_url"]:
            self.result["confidence"] = "high"
        elif self.result["name"]:
            self.result["confidence"] = "medium"

        return self.result


CATEGORY_KEYWORDS = {
    "restaurant": ["restaurant", "cafe", "bakery", "grill", "pizza", "biryani", "catering", "food", "dining", "coffee"],
    "beauty": ["beauty", "parlor", "salon", "cosmetic", "skincare", "makeup", "spa", "nail", "barber", "hair"],
    "pharmacy": ["pharmacy", "drug", "chemist", "medicine", "pharmaceutical"],
    "fitness": ["gym", "fitness", "yoga", "zumba", "workout", "crossfit"],
    "automotive": ["auto", "car", "mechanic", "garage", "automobile", "car wash", "spare parts"],
    "agriculture": ["farm", "agriculture", "agro", "dairy", "poultry", "seed", "fertilizer", "nursery"],
    "hotel": ["hotel", "resort", "motel", "guest house", "accommodation"],
    "healthcare": ["hospital", "clinic", "diagnostic", "medical", "doctor", "dental", "physiotherapy", "lab"],
    "education": ["school", "college", "university", "coaching", "tutorial", "training", "academy", "institute"],
    "manufacturing": ["manufacturing", "factory", "garment", "textile", "industry", "wholesale", "supplier"],
    "realestate": ["real estate", "property", "apartment", "flat", "land", "builder", "developer", "construction"],
    "services": ["electrician", "plumber", "carpenter", "repair", "maintenance", "cleaning", "laundry", "tailor", "photography", "event", "courier", "travel", "consultant", "security"],
    "retail": ["store", "shop", "fashion", "boutique", "grocery", "supermarket", "electronics", "furniture", "clothing", "jewelry"],
    "home": ["home", "decor", "furniture", "interior", "kitchen", "bedding", "ceramic"],
    "jewelry": ["jewelry", "jewellery", "necklace", "earring", "bangle", "ring", "gold"],
    "baby": ["baby", "kids", "children", "toy", "diaper", "stroller"],
    "skincare": ["skincare", "skin care", "serum", "moisturizer", "sunscreen", "face wash"],
    "fashion": ["fashion", "kameez", "saree", "panjabi", "hijab", "salwar", "kurta", "lehenga", "dupatta"],
}


def detect_category(text: str) -> str:
    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for k in keywords if k in text_lower)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)
    return "general"


def find_canonical(raw: str) -> str:
    raw = raw.strip().lower().replace(" ", "_")
    if raw in CATEGORY_PRODUCTS:
        return raw
    for key in CATEGORY_PRODUCTS:
        if raw in key or key in raw:
            return key
        store = CATEGORY_STORE_NAMES.get(key, "").lower()
        if raw in store:
            return key
    return "general"


def main():
    parser = argparse.ArgumentParser(description="Extract brand info from a Facebook page")
    parser.add_argument("page_url", help="Facebook page URL or username")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--extract-colors", action="store_true", default=True,
                        help="Extract brand colors from cover image (default: on)")
    args = parser.parse_args()

    ext = FacebookBrandExtractor(args.page_url)
    result = ext.run()

    if args.json:
        print(json.dumps(result, indent=2))
        return

    print(f"\n  URL:       {result['url']}")
    print(f"  Name:      {result['name']}")
    print(f"  Category:  {result.get('category', '?')}")
    print(f"  Canonical: {result['canonical_category']}")
    print(f"  Logo:      {result.get('logo_url', 'N/A')[:80]}")
    print(f"  Colors:    {', '.join(result.get('brand_colors', [])) or 'N/A'}")
    print(f"  Phone:     {result.get('phone', 'N/A')}")
    print(f"  Email:     {result.get('email', 'N/A')}")
    if "error" in result:
        print(f"  Error:     {result['error']}")

    print(f"\n  Suggested command:")
    print(f"  python3 build_demo.py --category \"{result['canonical_category']}\" "
          f"--name \"{result['name']}\" --phone \"{result.get('phone', '017XXXXXXXX')}\" --deploy")


if __name__ == "__main__":
    main()
