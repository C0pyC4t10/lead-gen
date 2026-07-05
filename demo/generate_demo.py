#!/usr/bin/env python3
"""generate_demo.py \u2014 Category-specific lead demo website generator.

Generates fresh, client-facing demo websites with per-category design tokens,
process steps, reviews, and zero Skarbol Tech sales content.

Usage:
  python3 generate_demo.py --name "Araki Restaurant" --phone "01812-442044" \
      --category "restaurant" --address "Gulshan, Dhaka" --out /tmp/demo.html
  python3 generate_demo.py --name "Araki Restaurant" --phone "01812-442044" \
      --category "restaurant" --address "Gulshan, Dhaka" --out /tmp/demo.html --pdf
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from category_lib import classify_category
from styles import build_base_css, build_font_links, CATEGORY_PALETTES
from template_config import get_config


def clean_phone(phone: str):
    """Normalize phone number for display and WhatsApp link."""
    raw = re.sub(r"[^\d+]", "", phone)
    if raw.startswith("+880"):
        raw = raw[4:]
    elif raw.startswith("880"):
        raw = raw[3:]
    raw = raw.lstrip("0")
    formatted = f"0{raw[:4]}-{raw[4:]}" if len(raw) >= 10 else f"0{raw}"
    return formatted, raw


def build_services_html(cfg: dict) -> str:
    services = cfg["services"]
    return "\n      ".join(
        f'<div class="service-card fade">'
        f'<span class="service-icon">{s[0]}</span>'
        f'<h4>{s[1]}</h4><p>{s[2]}</p></div>'
        for s in services
    )


def build_process_html(cfg: dict) -> str:
    steps = cfg["process"]
    return "\n      ".join(
        f'<div class="step-card fade">'
        f'<span class="step-num">{i + 1}</span>'
        f'<h4>{step[0]}</h4><p>{step[1]}</p></div>'
        for i, step in enumerate(steps)
    )


def build_reviews_html(cfg: dict) -> str:
    reviews = cfg["reviews"]
    return "\n      ".join(
        f'<div class="review-card fade">'
        f'<div class="review-stars">\u2605\u2605\u2605\u2605\u2605</div>'
        f'<blockquote>\u201c{r[2]}\u201d</blockquote>'
        f'<div class="review-author">\u2014 {r[0]}</div>'
        f'<div class="review-location">{r[1]}</div></div>'
        for r in reviews
    )


def generate_html(args, canonical: str, cfg: dict) -> str:
    phone_formatted, phone_raw = clean_phone(args.phone)
    css = build_base_css(canonical)
    fonts = build_font_links(canonical)
    palette = CATEGORY_PALETTES.get(canonical, CATEGORY_PALETTES["general"])

    template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template_master.html")
    if not os.path.exists(template_path):
        print(f"Error: Template not found: {template_path}", file=sys.stderr)
        sys.exit(1)

    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()

    about_title, about_p1, about_p2 = cfg["about"]

    replacements = {
        "{{FONTS}}": fonts,
        "{{STYLES}}": css,
        "{{BUSINESS_NAME}}": args.name,
        "{{TAGLINE}}": cfg["tagline"],
        "{{PHONE}}": phone_formatted,
        "{{PHONE_RAW}}": phone_raw,
        "{{ADDRESS}}": args.address,
        "{{HERO_BADGE}}": cfg["hero_badge"],
        "{{ICON}}": cfg["icon"],
        "{{ABOUT_TITLE}}": about_title,
        "{{ABOUT_P1}}": about_p1,
        "{{ABOUT_P2}}": about_p2,
        "{{ABOUT_SIDEBAR}}": f"Trusted {canonical} provider serving the local community with quality and dedication.",
        "{{SERVICES}}": build_services_html(cfg),
        "{{PROCESS}}": build_process_html(cfg),
        "{{REVIEWS}}": build_reviews_html(cfg),
    }

    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    return html


def generate_pdf(html: str, output_path: str) -> None:
    try:
        from weasyprint import HTML
        HTML(string=html).write_pdf(output_path)
        print(f"  PDF: {output_path}")
    except ImportError:
        print("  PDF: WeasyPrint not installed. Run: pip install weasyprint", file=sys.stderr)
    except Exception as e:
        print(f"  PDF error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Generate category-specific lead demo website")
    parser.add_argument("--name", required=True)
    parser.add_argument("--phone", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--address", default="Dhaka, Bangladesh")
    parser.add_argument("--out", required=True)
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    canonical = classify_category(args.category)
    cfg = get_config(canonical)

    html = generate_html(args, canonical, cfg)

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Demo generated: {out_path}")

    if args.pdf:
        pdf_path = out_path.rsplit(".", 1)[0] + ".pdf"
        generate_pdf(html, pdf_path)

    if args.json:
        json_path = out_path.rsplit(".", 1)[0] + ".json"
        meta = {
            "business_name": args.name,
            "phone": clean_phone(args.phone)[0],
            "category": args.category,
            "canonical_category": canonical,
            "address": args.address,
            "tagline": cfg["tagline"],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        print(f"Metadata: {json_path}")


if __name__ == "__main__":
    main()
