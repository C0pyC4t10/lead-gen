#!/usr/bin/env python3
"""Apply all 8 fixes to lead_gen_outreach.py - redesign with Shopify 2026 specs"""

import re

FILEPATH = '/home/skarbolt/kb/lead-gen/lead_gen_outreach.py'

with open(FILEPATH) as f:
    source = f.read()

# ============================================================
# FIX 2: _build_css - New design tokens
# ============================================================

NEW_BUILD_CSS = """\
def _build_css(canonical: str, primary_color: str) -> str:
    _TOKENS = {
        'general': {'bg':'#0f172a','primary':'#2563eb','accent':'#f59e0b','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)','btn_primary':'#2563eb','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#2563eb','badge_text':'#ffffff','heading_font':"'Inter'",'body_font':"'Inter'"},
        'restaurant': {'bg':'#0f0f0f','primary':'#d4a373','accent':'#faedcd','surface':'#1a1a1a','hero_bg':'linear-gradient(135deg, #0f0f0f 0%, #2a1f1a 100%)','btn_primary':'#d4a373','btn_text':'#0f0f0f','card_bg':'#1a1a1a','border':'#333333','badge_bg':'#d4a373','badge_text':'#0f0f0f','heading_font':"'Playfair Display'",'body_font':"'Lora'"},
        'salon': {'bg':'#fff5f5','primary':'#e8a0b4','accent':'#fef0f0','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #fff5f5 0%, #fce4ec 100%)','btn_primary':'#e8a0b4','btn_text':'#ffffff','card_bg':'#ffffff','border':'#fce4ec','badge_bg':'#e8a0b4','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Nunito'"},
        'photography': {'bg':'#1a1a1a','primary':'#f5f5f5','accent':'#d4a373','surface':'#2a2a2a','hero_bg':'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)','btn_primary':'#f5f5f5','btn_text':'#1a1a1a','card_bg':'#2a2a2a','border':'#404040','badge_bg':'#d4a373','badge_text':'#1a1a1a','heading_font':"'Cormorant Garamond'",'body_font':"'Nunito'"},
        'education': {'bg':'#f8fafc','primary':'#1e40af','accent':'#fbbf24','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #1e40af 0%, #3b82f6 100%)','btn_primary':'#1e40af','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#fbbf24','badge_text':'#1e293b','heading_font':"'Inter'",'body_font':"'Nunito'"},
        'real_estate': {'bg':'#f8fafc','primary':'#0f766e','accent':'#d4a373','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)','btn_primary':'#0f766e','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#d4a373','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Nunito'"},
        'fashion': {'bg':'#faf5ff','primary':'#7c3aed','accent':'#f0abfc','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)','btn_primary':'#7c3aed','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e9d5ff','badge_bg':'#7c3aed','badge_text':'#ffffff','heading_font':"'Poppins'",'body_font':"'Nunito'"},
        'jewelry': {'bg':'#0d0d0d','primary':'#fbbf24','accent':'#fef3c7','surface':'#1a1a1a','hero_bg':'linear-gradient(135deg, #0d0d0d 0%, #1a1a2e 100%)','btn_primary':'#fbbf24','btn_text':'#0d0d0d','card_bg':'#1a1a1a','border':'#333333','badge_bg':'#fbbf24','badge_text':'#0d0d0d','heading_font':"'Playfair Display'",'body_font':"'Cormorant Garamond'"},
        'skincare': {'bg':'#fff0f5','primary':'#db2777','accent':'#fdf2f8','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #db2777 0%, #f472b6 100%)','btn_primary':'#db2777','btn_text':'#ffffff','card_bg':'#ffffff','border':'#fce7f3','badge_bg':'#db2777','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Nunito'"},
        'baby': {'bg':'#e0f2fe','primary':'#f59e0b','accent':'#fef3c7','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)','btn_primary':'#fbbf24','btn_text':'#1e293b','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#fbbf24','badge_text':'#1e293b','heading_font':"'Nunito'",'body_font':"'Inter'"},
        'home': {'bg':'#f8fafc','primary':'#b45309','accent':'#fef3c7','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #b45309 0%, #d97706 100%)','btn_primary':'#b45309','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#b45309','badge_text':'#ffffff','heading_font':"'Inter'",'body_font':"'Nunito'"},
        'legal': {'bg':'#f8fafc','primary':'#1e293b','accent':'#cbd5e1','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #1e293b 0%, #334155 100%)','btn_primary':'#1e293b','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#1e293b','badge_text':'#ffffff','heading_font':"'Merriweather'",'body_font':"'Inter'"},
        'healthcare': {'bg':'#f0fdf4','primary':'#16a34a','accent':'#dcfce7','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #16a34a 0%, #22c55e 100%)','btn_primary':'#16a34a','btn_text':'#ffffff','card_bg':'#ffffff','border':'#dcfce7','badge_bg':'#16a34a','badge_text':'#ffffff','heading_font':"'Merriweather'",'body_font':"'Nunito'"},
        'fitness': {'bg':'#0a0a0a','primary':'#ef4444','accent':'#fecaca','surface':'#1a1a1a','hero_bg':'linear-gradient(135deg, #0a0a0a 0%, #1f1f1f 100%)','btn_primary':'#ef4444','btn_text':'#ffffff','card_bg':'#1a1a1a','border':'#333333','badge_bg':'#ef4444','badge_text':'#ffffff','heading_font':"'Barlow Condensed'",'body_font':"'Inter'"},
        'automotive': {'bg':'#0a0a0a','primary':'#3b82f6','accent':'#dbeafe','surface':'#1a1a1a','hero_bg':'linear-gradient(135deg, #0a0a0a 0%, #1e3a5f 100%)','btn_primary':'#3b82f6','btn_text':'#ffffff','card_bg':'#1a1a1a','border':'#333333','badge_bg':'#3b82f6','badge_text':'#ffffff','heading_font':"'Barlow'",'body_font':"'Inter'"},
        'furniture': {'bg':'#f5f0eb','primary':'#8b5e3c','accent':'#d4c5b5','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #8b5e3c 0%, #a67c52 100%)','btn_primary':'#8b5e3c','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#8b5e3c','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Inter'"},
        'grocery': {'bg':'#f0fdf4','primary':'#22c55e','accent':'#fef9c3','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)','btn_primary':'#22c55e','btn_text':'#ffffff','card_bg':'#ffffff','border':'#dcfce7','badge_bg':'#22c55e','badge_text':'#ffffff','heading_font':"'Inter'",'body_font':"'Nunito'"},
        'beauty': {'bg':'#fff5f5','primary':'#e8a0b4','accent':'#fef0f0','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #fff5f5 0%, #fce4ec 100%)','btn_primary':'#e8a0b4','btn_text':'#ffffff','card_bg':'#ffffff','border':'#fce4ec','badge_bg':'#e8a0b4','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Nunito'"},
        'retail': {'bg':'#faf5ff','primary':'#7c3aed','accent':'#f0abfc','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #7c3aed 0%, #a855f7 100%)','btn_primary':'#7c3aed','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e9d5ff','badge_bg':'#7c3aed','badge_text':'#ffffff','heading_font':"'Inter'",'body_font':"'Nunito'"},
        'manufacturing': {'bg':'#f8fafc','primary':'#1e293b','accent':'#cbd5e1','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #1e293b 0%, #334155 100%)','btn_primary':'#1e293b','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#1e293b','badge_text':'#ffffff','heading_font':"'Inter'",'body_font':"'Inter'"},
        'agriculture': {'bg':'#f0fdf4','primary':'#22c55e','accent':'#fef9c3','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)','btn_primary':'#22c55e','btn_text':'#ffffff','card_bg':'#ffffff','border':'#dcfce7','badge_bg':'#22c55e','badge_text':'#ffffff','heading_font':"'Merriweather'",'body_font':"'Inter'"},
        'hotel': {'bg':'#f8fafc','primary':'#0f766e','accent':'#d4a373','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)','btn_primary':'#0f766e','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#d4a373','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Nunito'"},
        'realestate': {'bg':'#f8fafc','primary':'#0f766e','accent':'#d4a373','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #0f766e 0%, #14b8a6 100%)','btn_primary':'#0f766e','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#d4a373','badge_text':'#ffffff','heading_font':"'Playfair Display'",'body_font':"'Nunito'"},
        'services': {'bg':'#0f172a','primary':'#2563eb','accent':'#f59e0b','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%)','btn_primary':'#2563eb','btn_text':'#ffffff','card_bg':'#ffffff','border':'#e2e8f0','badge_bg':'#2563eb','badge_text':'#ffffff','heading_font':"'Inter'",'body_font':"'Inter'"},
        'pharmacy': {'bg':'#f0fdf4','primary':'#16a34a','accent':'#dcfce7','surface':'#ffffff','hero_bg':'linear-gradient(135deg, #16a34a 0%, #22c55e 100%)','btn_primary':'#16a34a','btn_text':'#ffffff','card_bg':'#ffffff','border':'#dcfce7','badge_bg':'#16a34a','badge_text':'#ffffff','heading_font':"'Merriweather'",'body_font':"'Nunito'"},
    }
    t = _TOKENS.get(canonical, _TOKENS['general'])
    return f'''@import url("https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800;900|Cormorant+Garamond:wght@400;600;700|Nunito:wght@400;600;700;800|Lora:wght@400;600;700|Poppins:wght@400;600;700;800|Merriweather:wght@400;700;900|Barlow+Condensed:wght@400;600;700;800|Barlow:wght@400;500;600;700|Inter:wght@400;500;600;700;800;900&display=swap");

:root {{
  --bg: {t['bg']};
  --primary: {t['primary']};
  --accent: {t['accent']};
  --surface: {t['surface']};
  --hero-bg: {t['hero_bg']};
  --btn-primary: {t['btn_primary']};
  --btn-text: {t['btn_text']};
  --card-bg: {t['card_bg']};
  --border: {t['border']};
  --badge-bg: {t['badge_bg']};
  --badge-text: {t['badge_text']};
  --font-heading: {t['heading_font']};
  --font-body: {t['body_font']};
  --text: #1C1917;
  --text-muted: #78716C;
  --radius: 12px;
  --radius-sm: 8px;
  --radius-full: 9999px;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-hover: 0 10px 25px rgba(0,0,0,0.08);
  --transition: 0.25s ease;
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior:smooth; scroll-padding-top:76px; }}
body {{
  font-family:var(--font-body);
  background:var(--bg);
  color:var(--text);
  line-height:1.6;
  -webkit-font-smoothing:antialiased;
}}
::selection {{ background:color-mix(in srgb, var(--primary) 20%, transparent); }}
img {{ max-width:100%; height:auto; display:block; }}
a {{ color:var(--primary); text-decoration:none; transition:color var(--transition); }}
a:hover {{ color:var(--accent); }}
.container {{ max-width:1120px; margin:0 auto; padding:0 24px; }}

/* ── Language Toggle ── */
.lang-en {{ display:inline; }}
.lang-bn {{ display:none; }}
html[lang="bn"] .lang-bn {{ display:inline; }}
html[lang="bn"] .lang-en {{ display:none; }}

/* ── Header ── */
.header {{
  position:fixed; top:0; left:0; right:0; z-index:100;
  height:72px;
  background:rgba(255,255,255,0.92);
  backdrop-filter:blur(14px);
  -webkit-backdrop-filter:blur(14px);
  border-bottom:1px solid var(--border);
}}
.header-inner {{
  display:flex; align-items:center; justify-content:space-between; height:100%;
}}
.logo {{
  display:flex; align-items:center; gap:12px; text-decoration:none;
}}
.logo-img {{ width:36px; height:36px; border-radius:var(--radius-sm); object-fit:cover; }}
.logo-text {{
  width:36px; height:36px; border-radius:var(--radius-sm);
  background:var(--primary); color:#fff;
  display:flex; align-items:center; justify-content:center;
  font-weight:700; font-size:18px; font-family:var(--font-heading); flex-shrink:0;
}}
.logo-name {{
  font-family:var(--font-heading); font-weight:700; font-size:18px;
  color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:180px;
}}
.nav {{ display:flex; align-items:center; gap:8px; }}
.nav a {{
  padding:8px 16px; border-radius:var(--radius-full); font-size:14px; font-weight:500;
  color:var(--text-muted); transition:all var(--transition); text-decoration:none;
}}
.nav a:hover, .nav a.active {{ background:var(--primary); color:#fff; }}
.nav-toggle {{ display:none; background:none; border:none; font-size:24px; cursor:pointer; color:var(--text); padding:8px; }}
.header-actions {{ display:flex; align-items:center; gap:8px; }}
.lang-toggle {{
  padding:6px 14px; border:1px solid var(--border); border-radius:var(--radius-full);
  background:transparent; font-size:13px; font-weight:600; cursor:pointer;
  color:var(--text-muted); transition:all var(--transition); font-family:var(--font-body);
}}
.lang-toggle:hover {{ border-color:var(--primary); color:var(--primary); }}

/* ── Announcement Bar ── */
.announcement-bar {{
  margin-top:72px;
  background:var(--primary); color:#fff; text-align:center; padding:10px 0;
  font-size:14px; font-weight:500; letter-spacing:0.3px;
}}
.announcement-bar span {{ color:#fff; }}

/* ── Hero ── */
.hero {{
  position:relative; overflow:hidden; padding:80px 0 60px;
  background:var(--hero-bg);
}}
.hero-content {{ position:relative; z-index:2; text-align:center; max-width:800px; margin:0 auto; }}
.hero-badge {{
  display:inline-block; padding:6px 20px; border-radius:var(--radius-full);
  background:rgba(255,255,255,0.15); backdrop-filter:blur(8px);
  color:#fff; font-size:13px; font-weight:600; letter-spacing:1px; text-transform:uppercase;
  margin-bottom:20px; font-family:var(--font-heading);
}}
.hero h1 {{
  font-family:var(--font-heading); font-size:48px; font-weight:800; line-height:1.15;
  color:#fff; margin-bottom:16px;
}}
.hero-sub {{
  font-size:18px; color:rgba(255,255,255,0.85); margin-bottom:16px; line-height:1.5;
}}
.hero-address {{ font-size:15px; color:rgba(255,255,255,0.7); margin-bottom:24px; }}
.hero-actions {{ display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }}

/* ── Buttons ── */
.btn {{
  display:inline-flex; align-items:center; gap:8px; padding:12px 28px;
  border-radius:var(--radius-full); font-size:15px; font-weight:600;
  text-decoration:none; cursor:pointer; transition:all var(--transition);
  border:none; font-family:var(--font-body);
}}
.btn-primary {{ background:var(--btn-primary); color:var(--btn-text); }}
.btn-primary:hover {{ transform:translateY(-2px); box-shadow:0 8px 24px color-mix(in srgb, var(--btn-primary) 30%, transparent); }}
.btn-outline {{
  background:transparent; border:2px solid rgba(255,255,255,0.4);
  color:#fff; backdrop-filter:blur(4px);
}}
.btn-outline:hover {{ border-color:#fff; background:rgba(255,255,255,0.1); }}
.btn-lg {{ padding:14px 36px; font-size:16px; }}
.btn-dark {{ background:var(--text); color:#fff; }}
.btn-dark:hover {{ background:var(--primary); }}

/* ── Trust Bar ── */
.trust-bar {{
  padding:24px 0; background:var(--bg); border-bottom:1px solid var(--border);
}}
.trust-grid {{ display:flex; justify-content:center; gap:32px; flex-wrap:wrap; }}
.trust-item {{
  display:flex; align-items:center; gap:8px; font-size:14px; font-weight:500; color:var(--text-muted);
}}

/* ── Section ── */
.section {{ padding:60px 0; }}
.section-shaded {{ background:var(--surface); }}
.section-head {{ text-align:center; margin-bottom:40px; }}
.eyebrow {{
  display:inline-block; font-size:13px; font-weight:600; text-transform:uppercase;
  letter-spacing:2px; color:var(--primary); margin-bottom:8px; font-family:var(--font-heading);
}}
.section-head h2 {{
  font-family:var(--font-heading); font-size:32px; font-weight:700;
  color:var(--text); margin-bottom:12px;
}}
.hr {{ width:60px; height:3px; background:var(--primary); border-radius:4px; margin:0 auto; }}

/* ── Products Grid ── */
.products-grid {{
  display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr));
  gap:24px; margin-top:8px;
}}
.product-card {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius);
  overflow:hidden; transition:all var(--transition);
}}
.product-card:hover {{ transform:translateY(-4px); box-shadow:var(--shadow-hover); }}
.product-card-img {{ width:100%; height:200px; object-fit:cover; }}
.product-card-body {{ padding:16px; }}
.product-name {{
  font-family:var(--font-heading); font-size:16px; font-weight:600;
  color:var(--text); margin-bottom:6px;
}}
.product-desc {{ font-size:13px; color:var(--text-muted); margin-bottom:8px; line-height:1.4; }}
.product-footer {{ display:flex; justify-content:space-between; align-items:center; }}
.product-price {{ font-size:18px; font-weight:700; color:var(--primary); font-family:var(--font-heading); }}
.product-btn {{
  padding:8px 16px; background:var(--btn-primary); color:var(--btn-text);
  border:none; border-radius:var(--radius-sm); font-size:13px; font-weight:600; cursor:pointer;
  text-decoration:none; transition:all var(--transition);
}}
.product-btn:hover {{ transform:translateY(-1px); opacity:0.9; }}

/* ── About Grid ── */
.about-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:48px; align-items:center; }}
.about-text h3 {{
  font-family:var(--font-heading); font-size:28px; font-weight:700; color:var(--text); margin-bottom:16px;
}}
.about-text p {{ font-size:15px; color:var(--text-muted); line-height:1.6; }}
.about-card {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius);
  padding:32px; text-align:center;
}}
.about-icon {{ font-size:48px; display:block; margin-bottom:16px; }}
.about-card p {{ font-size:14px; color:var(--text-muted); line-height:1.5; }}

/* ── Services / Why Grid ── */
.services-grid, .why-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:24px; }}
.service-card, .why-card {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius);
  padding:28px 20px; text-align:center; transition:all var(--transition);
}}
.service-card:hover, .why-card:hover {{ transform:translateY(-2px); box-shadow:var(--shadow-hover); }}
.service-icon, .why-icon {{ font-size:36px; display:block; margin-bottom:12px; }}
.service-card h4, .why-card h4 {{
  font-family:var(--font-heading); font-size:16px; font-weight:600;
  color:var(--text); margin-bottom:6px;
}}
.service-card p, .why-card p {{ font-size:13px; color:var(--text-muted); line-height:1.5; }}

/* ── Process Grid ── */
.process-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:32px; }}
.step-card {{ text-align:center; }}
.step-num {{
  width:56px; height:56px; border-radius:50%; background:var(--primary);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-size:22px; font-weight:700; margin:0 auto 12px; font-family:var(--font-heading);
}}
.step-card h4 {{
  font-family:var(--font-heading); font-size:15px; font-weight:600;
  color:var(--text); margin-bottom:4px;
}}
.step-card p {{ font-size:13px; color:var(--text-muted); line-height:1.4; }}

/* ── Testimonials ── */
.testimonials-grid {{
  display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:24px;
}}
.testimonial-card {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius);
  padding:24px; transition:all var(--transition);
}}
.testimonial-card:hover {{ transform:translateY(-2px); box-shadow:var(--shadow-hover); }}
.testimonial-stars {{ color:#f59e0b; font-size:16px; margin-bottom:8px; }}
.testimonial-card blockquote {{ font-size:14px; color:var(--text-muted); font-style:italic; line-height:1.5; margin-bottom:16px; }}
.testimonial-author {{ display:flex; align-items:center; gap:12px; }}
.testimonial-avatar {{
  width:40px; height:40px; border-radius:50%; background:var(--primary);
  color:#fff; display:flex; align-items:center; justify-content:center;
  font-weight:600; font-size:16px; flex-shrink:0; font-family:var(--font-heading);
}}
.testimonial-name {{ font-size:14px; font-weight:600; color:var(--text); }}
.testimonial-location {{ font-size:12px; color:var(--text-muted); }}

/* ── Stats ── */
.stats-section {{ background:var(--primary); padding:48px 0; }}
.stats-grid {{ display:flex; justify-content:center; gap:48px; flex-wrap:wrap; }}
.stat-card {{ text-align:center; }}
.stat-icon {{ font-size:36px; display:block; margin-bottom:8px; }}
.stat-val {{
  font-family:var(--font-heading); font-size:36px; font-weight:800; color:#fff; line-height:1;
}}
.stat-label {{ font-size:14px; color:rgba(255,255,255,0.8); margin-top:4px; }}

/* ── CTA Banner ── */
.cta-banner {{
  background:linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
  padding:60px 0; text-align:center;
}}
.cta-content h2 {{
  font-family:var(--font-heading); font-size:36px; font-weight:800;
  color:#fff; margin-bottom:12px;
}}
.cta-content p {{ font-size:16px; color:rgba(255,255,255,0.85); margin-bottom:24px; }}

/* ── Footer ── */
.footer {{
  background:var(--text); color:rgba(255,255,255,0.8); padding:48px 0 24px;
}}
.footer-grid {{ display:grid; grid-template-columns:2fr 1fr 1fr 1fr; gap:32px; margin-bottom:32px; }}
.footer-brand h3 {{
  font-family:var(--font-heading); font-size:20px; font-weight:700; color:#fff; margin-bottom:12px;
}}
.footer-brand p {{ font-size:14px; line-height:1.6; }}
.footer-col h4 {{ font-size:14px; font-weight:600; color:#fff; margin-bottom:12px; text-transform:uppercase; letter-spacing:1px; }}
.footer-col a {{ display:block; font-size:14px; color:rgba(255,255,255,0.7); margin-bottom:8px; }}
.footer-col a:hover {{ color:#fff; }}
.footer-col p {{ font-size:14px; color:rgba(255,255,255,0.7); margin-bottom:6px; }}
.footer-bottom {{
  border-top:1px solid rgba(255,255,255,0.1); padding-top:16px; margin-top:16px;
  text-align:center; font-size:13px; color:rgba(255,255,255,0.5);
}}

/* ── Floating WhatsApp ── */
.wa-float {{
  position:fixed; bottom:24px; right:24px; z-index:999;
  width:56px; height:56px; border-radius:50%; background:#25D366;
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 4px 16px rgba(37,211,102,0.4);
  transition:all var(--transition); cursor:pointer; text-decoration:none;
}}
.wa-float:hover {{ transform:scale(1.1); box-shadow:0 6px 24px rgba(37,211,102,0.5); }}
.wa-float svg {{ width:28px; height:28px; fill:#fff; }}

/* ── Page Hero ── */
.page-hero {{
  margin-top:72px; padding:48px 0; background:var(--hero-bg); text-align:center;
}}
.page-hero-sm {{ padding:32px 0; }}
.page-hero h1 {{
  font-family:var(--font-heading); font-size:36px; font-weight:800;
  color:#fff; margin-bottom:8px;
}}
.page-hero p {{ font-size:16px; color:rgba(255,255,255,0.8); }}

/* ── Products Page ── */
.filter-bar {{ display:flex; gap:12px; margin-bottom:24px; flex-wrap:wrap; align-items:center; }}
.filter-btn {{
  padding:8px 20px; border:1px solid var(--border); border-radius:var(--radius-full);
  background:var(--card-bg); font-size:13px; font-weight:500; cursor:pointer;
  transition:all var(--transition); color:var(--text-muted); font-family:var(--font-body);
}}
.filter-btn:hover {{ border-color:var(--primary); color:var(--primary); }}
.filter-btn.active {{ background:var(--primary); color:#fff; border-color:var(--primary); }}
.filter-sort {{
  margin-left:auto; padding:8px 16px; border:1px solid var(--border);
  border-radius:var(--radius-sm); font-size:13px; background:var(--card-bg);
  color:var(--text); font-family:var(--font-body);
}}

/* ── About Page ── */
.about-page {{ display:grid; grid-template-columns:2fr 1fr; gap:48px; }}
.about-page-content h2 {{
  font-family:var(--font-heading); font-size:24px; font-weight:700; color:var(--text); margin-bottom:12px; margin-top:24px;
}}
.about-page-content p {{ font-size:15px; color:var(--text-muted); line-height:1.6; }}
.about-features {{ list-style:none; padding:0; }}
.about-features li {{ padding:8px 0; font-size:14px; color:var(--text-muted); border-bottom:1px solid var(--border); }}

/* ── Contact Page ── */
.contact-page {{ display:grid; grid-template-columns:1fr 1fr; gap:48px; }}
.contact-form-card, .contact-info-card {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius); padding:32px;
}}
.contact-form-card h3, .contact-info-card h4 {{
  font-family:var(--font-heading); font-size:18px; font-weight:600; color:var(--text); margin-bottom:16px;
}}
.form-group {{ margin-bottom:16px; }}
.form-group label {{ display:block; font-size:14px; font-weight:500; color:var(--text); margin-bottom:4px; }}
.form-group input, .form-group textarea, .form-group select {{
  width:100%; padding:10px 14px; border:1px solid var(--border); border-radius:var(--radius-sm);
  font-size:14px; background:var(--card-bg); color:var(--text); transition:border var(--transition);
  font-family:var(--font-body);
}}
.form-group input:focus, .form-group textarea:focus, .form-group select:focus {{
  outline:none; border-color:var(--primary); box-shadow:0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}}
.form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
.required {{ color:var(--accent); }}
.info-item {{ display:flex; gap:12px; align-items:flex-start; margin-bottom:16px; }}
.info-icon {{ font-size:20px; flex-shrink:0; }}
.info-item h4 {{ font-size:14px; margin-bottom:2px; }}
.info-item p, .info-item a {{ font-size:14px; color:var(--text-muted); }}

/* ── Checkout Page ── */
.checkout-grid {{ display:grid; grid-template-columns:3fr 2fr; gap:40px; align-items:start; }}
.checkout-form-col .checkout-section {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius); padding:24px; margin-bottom:20px;
}}
.checkout-section-title {{ font-family:var(--font-heading); font-size:18px; font-weight:600; color:var(--text); margin-bottom:16px; padding-bottom:12px; border-bottom:1px solid var(--border); }}
.checkout-summary-card {{
  background:var(--card-bg); border:1px solid var(--border); border-radius:var(--radius); padding:24px; position:sticky; top:96px;
}}
.summary-table {{ width:100%; border-collapse:collapse; font-size:14px; }}
.summary-table th {{ text-align:left; padding:8px 4px; font-weight:600; color:var(--text-muted); font-size:12px; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid var(--border); }}
.summary-table td {{ padding:8px 4px; border-bottom:1px solid var(--border); }}
.summary-product-name {{ display:block; font-weight:500; color:var(--text); }}
.summary-product-desc {{ font-size:12px; color:var(--text-muted); }}
.summary-qty, .summary-price {{ text-align:center; }}
.summary-free {{ color:var(--primary); font-weight:600; }}
.summary-total td {{ font-weight:700; font-size:16px; border-bottom:none; padding-top:12px; }}
.summary-total-price {{ text-align:right; font-weight:700; }}
.summary-payment-info {{ font-size:13px; color:var(--text-muted); margin-top:12px; text-align:center; }}
.checkout-btn {{ width:100%; justify-content:center; margin-top:16px; }}
.summary-footer {{ font-size:12px; color:var(--text-muted); margin-top:12px; text-align:center; line-height:1.4; }}

/* ── Responsive ── */
@media (max-width:768px) {{
  .nav {{ display:none; position:fixed; top:72px; left:0; right:0; background:var(--card-bg); flex-direction:column; padding:16px; box-shadow:0 4px 16px rgba(0,0,0,0.1); }}
  .nav.open {{ display:flex; }}
  .nav-toggle {{ display:block; }}
  .hero h1 {{ font-size:32px; }}
  .about-grid, .contact-page, .footer-grid, .checkout-grid, .about-page {{ grid-template-columns:1fr; gap:24px; }}
  .products-grid {{ grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:16px; }}
  .filter-bar {{ flex-direction:column; }}
  .filter-sort {{ margin-left:0; width:100%; }}
}}
@media (max-width:480px) {{
  .hero h1 {{ font-size:26px; }}
  .section-head h2 {{ font-size:24px; }}
  .products-grid {{ grid-template-columns:1fr 1fr; gap:12px; }}
  .hero-actions {{ flex-direction:column; align-items:center; }}
}}

/* ── AOS Animation ── */
[data-aos] {{ opacity:0; transform:translateY(24px); transition:opacity 0.5s ease, transform 0.5s ease; }}
[data-aos].aos-animate {{ opacity:1; transform:translateY(0); }}
"""  # <-- closing NEW_BUILD_CSS


def replace_function(source: str, func_name: str, new_body: str) -> str:
    pattern = re.compile(
        r'^(def ' + re.escape(func_name) + r'\()'
        r'.*?(?=\n\ndef |\n# ── |\n\n\ndef |\Z)',
        re.DOTALL | re.MULTILINE
    )
    # Alternative approach: find start line with "def func_name" and end with next "def " or end
    lines = source.split('\n')
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith(f'def {func_name}(') or line.startswith(f'def {func_name} ('):
            start_idx = i
            break
    if start_idx is None:
        print(f"WARNING: Could not find function '{func_name}'")
        return source

    # Find end: next def at column 0, or next comment block "# ──", or end of file
    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith('def ') and not stripped.startswith('def ' + func_name):
            end_idx = i
            break
        # Also stop at section headers that are not indented
        if stripped.startswith('# ──') or stripped.startswith('# FIX'):
            # Only stop if this is a standalone comment line (not indented)
            if lines[i].startswith('#'):
                end_idx = i
                break

    # Build new source
    new_lines = new_body.split('\n')
    result_parts = lines[:start_idx] + new_lines + lines[end_idx:]
    print(f"  Replaced '{func_name}' ({start_idx+1}-{end_idx}) -> {len(new_lines)} lines")
    return '\n'.join(result_parts) if isinstance(result_parts, list) else result_parts


# ============================================================
# Apply all replacements
# ============================================================

print("Applying fixes to lead_gen_outreach.py...")

source = replace_function(source, '_build_css', NEW_BUILD_CSS)

# Write result
with open(FILEPATH, 'w') as f:
    f.write(source)

print("Done! All fixes applied.")
