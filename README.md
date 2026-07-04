# Lead Generation System — Skarbol Tech

## Overview

This lead-gen system is a structured approach to finding, qualifying, and nurturing business prospects for Skarbol Tech — Bangladesh's first fully integrated AI + Automation + IoT ecosystem company.

The system covers three social platforms (Facebook, Instagram, LinkedIn) with platform-specific search strategies, qualification criteria, and outreach templates. Collected leads are tracked in a standardized CSV format.

## Folder Structure

```
lead-gen/
├── facebook/
│   ├── search_queries.md        # 30 Facebook search queries (copy-pasteable)
│   ├── qualification_checklist.md # Lead scoring, green/red flags, contact extraction
│   └── outreach_messages.md      # 10 message templates for different prospect types
├── instagram/
│   └── .gitkeep                  # Placeholder for future Instagram strategy
├── linkedin/
│   └── .gitkeep                  # Placeholder for future LinkedIn strategy
├── collected_leads/
│   └── leads_template.csv        # Standardized lead tracking template
└── README.md                     # This file
```

## Target Prospect Categories

1. **No Website Businesses** — SMEs operating without any web presence; prime candidates for custom websites, ExecERP, and digital transformation.
2. **Beauty Product Sellers** — Boutiques, parlors, and cosmetic retailers needing inventory management, e-commerce, and digital storefronts.
3. **Businesses Needing Automation/ERP** — SMEs running on manual processes ripe for ExecERP, workflow automation, and AI integration.
4. **General SME Prospects** — Broad-scope small and medium enterprises across Bangladesh.

## Workflow

1. Search → Run platform-specific queries to find prospects
2. Qualify → Score each lead 1-10 using the qualification checklist
3. Reach Out → Use templates matched to prospect type
4. Track → Log every lead in the CSV template with status and follow-up dates

## Notes

- All outreach must reflect Skarbol Tech's brand voice: professional, confident, and helpful — never desperate or pushy.
- Leads that score below 5 should be deprioritized or discarded.
- Follow-up within 72 hours of initial outreach.

## Smart Hunt — Automated F-Commerce Lead Finder

`smart_hunt.py` finds high-engagement Bangladesh Facebook businesses selling physical products via inbox/WhatsApp without proper e-commerce websites.

**Pipeline:** Serper.dev search → Apify enrichment → Scoring (0-22) → Save to dashboard

```bash
# Hunt a single category
python3 smart_hunt.py --category beauty

# Hunt multiple categories
python3 smart_hunt.py --category beauty,fashion,bags

# Hunt all 28 categories
python3 smart_hunt.py --category all

# Skip Apify (Serper data only)
python3 smart_hunt.py --category home --no-apify

# Dry run — score without saving
python3 smart_hunt.py --category beauty --dry-run

# Stop after N saves
python3 smart_hunt.py --category all --count 30

# Only HIGH+ leads (score >= 14)
python3 smart_hunt.py --category beauty --min-score 14
```

### Arguments

| Flag | Default | Description |
|------|---------|-------------|
| `--category` / `-c` | `all` | Category name or comma-separated (28 options: skincare, cosmetics, fashion, boutique, jewelry, perfume, baby, bags, home, food, fruit, nursery, clothing_brand, jewelry_watches, bags_luggage, health_beauty, cosmetics_store, personal_care, home_decor, kitchen_cooking, furniture_store, patio_garden, electronics, games_toys, outdoor_sporting, food_beverage, bakery, specialty_grocery) |
| `--count` | `50` | Maximum leads to save |
| `--min-score` | `10` | Minimum score threshold (18-22 PREMIUM, 14-17 HIGH, 10-13 MEDIUM, <10 skipped) |
| `--dry-run` | off | Score leads but do not save |
| `--no-apify` | off | Skip Apify, use Serper engagement data only |

**Env vars used:** `SERPER_API_KEY`, `APIFY_API_KEY`, `TELEGRAM_TOKEN`
