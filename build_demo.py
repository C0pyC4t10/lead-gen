#!/usr/bin/env python3
"""build_demo.py \u2014 CLI wrapper to generate any category demo.

Usage:
  python3 build_demo.py --category fashion --name "My Store" --phone 01712345678
  python3 build_demo.py --category beauty --name "Bella-BD" --phone 01712345678 --address "Gulshan" --deploy

Run with --help for all options.
"""

import argparse
import json
import os
import sys
import zipfile

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lead_gen_outreach import (
    CATEGORY_PRODUCTS,
    CATEGORY_BENGALI_NAMES,
    CATEGORY_STORE_NAMES,
    generate_site,
    clean_phone_for_whatsapp,
)


def normalize_category(raw: str) -> str:
    raw = raw.strip().lower().replace(" ", "_")
    # Direct match
    if raw in CATEGORY_PRODUCTS:
        return raw
    # Try canonical name match
    canonical_map = {
        v.lower().replace(" ", "_"): k for k, v in CATEGORY_STORE_NAMES.items()
    }
    if raw in canonical_map:
        return canonical_map[raw]
    # Try partial match
    for key in CATEGORY_PRODUCTS:
        if raw in key or key in raw:
            return key
        store = CATEGORY_STORE_NAMES.get(key, "")
        if raw in store.lower().replace(" ", ""):
            return key
    print(f"Unknown category '{raw}'. Available: {', '.join(sorted(CATEGORY_PRODUCTS.keys()))}")
    sys.exit(1)


def deploy_to_netlify(out_dir: str, token: str, site_id: str) -> str:
    zip_path = "/tmp/site-deploy.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(out_dir):
            for fn in files:
                fp = os.path.join(root, fn)
                arcname = os.path.relpath(fp, out_dir)
                zf.write(fp, arcname)

    import requests
    url = f"https://api.netlify.com/api/v1/sites/{site_id}/deploys"
    headers = {
        "Content-Type": "application/zip",
        "Authorization": f"Bearer {token}",
    }
    with open(zip_path, "rb") as f:
        resp = requests.post(url, headers=headers, data=f)
    if resp.ok:
        data = resp.json()
        return data.get("ssl_url", "") or data.get("url", "")
    print(f"Deploy failed: {resp.status_code} {resp.text[:200]}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Build a category demo site")
    parser.add_argument("--category", "-c", default="", help="Business category (fashion, beauty, etc.)")
    parser.add_argument("--name", "-n", default="", help="Store/business name")
    parser.add_argument("--phone", "-p", default="", help="Phone number")
    parser.add_argument("--address", "-a", default="Dhaka, Bangladesh", help="Business address")
    parser.add_argument("--primary-color", default="", help="Override primary brand color (e.g. #ff6b35)")
    parser.add_argument("--accent-color", default="", help="Override accent brand color (e.g. #004e89)")
    parser.add_argument("--facebook-page", help="Facebook page URL to auto-extract brand info")
    parser.add_argument("--facebook", default="", help="Facebook page URL or handle")
    parser.add_argument("--instagram", default="", help="Instagram handle")
    parser.add_argument("--out", "-o", default="", help="Output directory (default: demos/outreach_<category>)")
    parser.add_argument("--deploy", action="store_true", help="Deploy to Netlify after building")
    parser.add_argument("--netlify-token", help="Netlify personal access token (default: from .env)")
    parser.add_argument("--netlify-site-id", default="d5d97913-680a-4aba-98ca-5355e8af55d1", help="Netlify site ID")
    args = parser.parse_args()

    # Auto-extract from Facebook page if provided
    if args.facebook_page and (not args.name or not args.category or not args.phone):
        from extract_facebook_brand import FacebookBrandExtractor
        print(f"Extracting brand info from: {args.facebook_page}")
        ext = FacebookBrandExtractor(args.facebook_page)
        result = ext.run()
        if result.get("name"):
            print(f"  Found: {result['name']} ({result['canonical_category']})")
            if not args.name:
                args.name = result["name"]
            if not args.category:
                args.category = result["canonical_category"]
            if not args.phone:
                args.phone = result.get("phone", "") or input("  Phone number: ")
            if not args.facebook:
                args.facebook = args.facebook_page
            if result.get("brand_colors"):
                print(f"  Brand colors: {', '.join(result['brand_colors'][:3])}")
        else:
            print(f"  Could not extract. Error: {result.get('error', 'unknown')}")
            if not args.name:
                args.name = input("  Business name: ")
            if not args.category:
                args.category = input("  Category: ")
            if not args.phone:
                args.phone = input("  Phone number: ")

    if not args.name:
        args.name = input("  Business name: ")
    if not args.category:
        args.category = input("  Category (fashion, beauty, etc.): ")
    if not args.phone:
        args.phone = input("  Phone number: ")

    canonical = normalize_category(args.category)

    out_dir = args.out or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "demos",
        f"outreach_{canonical}",
    )

    # Clean output dir
    if os.path.exists(out_dir):
        import shutil
        shutil.rmtree(out_dir)

    print(f"Building: {args.name}")
    print(f"Category: {args.category} -> {canonical}")
    print(f"Output:   {out_dir}")
    print()

    generate_site(
        out_dir=out_dir,
        name=args.name,
        phone=clean_phone_for_whatsapp(args.phone),
        canonical=canonical,
        address=args.address,
        facebook_url=args.facebook,
        instagram=args.instagram,
        primary_color=args.primary_color or None,
        accent_color=args.accent_color or None,
    )

    print(f"\nDone! Site generated at: {out_dir}")
    print(f"Open: {out_dir}/index.html")

    if args.deploy:
        token = args.netlify_token or os.environ.get("NETLIFY_TOKEN") or ""
        if not token:
            # Try loading from .env
            env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
            if os.path.exists(env_path):
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("NETLIFY_TOKEN="):
                            token = line.split("=", 1)[1]
                            break
        if not token:
            print("No Netlify token found. Set --netlify-token or NETLIFY_TOKEN in .env")
            sys.exit(1)
        url = deploy_to_netlify(out_dir, token, args.netlify_site_id)
        print(f"Deployed:  {url}")
    else:
        print(f"Tip: add --deploy to auto-deploy to Netlify")


if __name__ == "__main__":
    main()
