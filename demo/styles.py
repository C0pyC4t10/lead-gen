"""styles.py \u2014 Per-category design tokens and CSS generation."""

from typing import Dict

# \u2500\u2500 Category Palettes \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
CATEGORY_PALETTES: Dict[str, Dict[str, str]] = {
    "fashion": {
        "primary": "#2c1810",
        "secondary": "#d4a853",
        "accent": "#c9a96e",
        "surface": "rgba(44,24,16,0.06)",
        "border": "rgba(44,24,16,0.2)",
        "bg": "#faf7f4",
        "bg_alt": "#f5ede4",
        "heading": "#2c1810",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #2c1810 0%, #d4a853 50%, #c9a96e 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(44,24,16,0.1)",
        "badge_text": "#7a3b0a",
    },
    "jewelry": {
        "primary": "#c9a96e",
        "secondary": "#ffffff",
        "accent": "#f1c40f",
        "surface": "rgba(201,169,110,0.06)",
        "border": "rgba(201,169,110,0.2)",
        "bg": "#1a1a1a",
        "bg_alt": "#0d0d0d",
        "heading": "#c9a96e",
        "text": "#ffffff",
        "text_muted": "#999999",
        "hero_overlay": "linear-gradient(135deg, #0d0d0d 0%, #1a1a1a 50%, #c9a96e 100%)",
        "card_bg": "#1a1a1a",
        "badge": "rgba(201,169,110,0.1)",
        "badge_text": "#c9a96e",
    },
    "skincare": {
        "primary": "#1a1a1a",
        "secondary": "#c9a96e",
        "accent": "#d4a853",
        "surface": "rgba(201,169,110,0.06)",
        "border": "rgba(201,169,110,0.2)",
        "bg": "#fdf6f0",
        "bg_alt": "#fdf0f5",
        "heading": "#1a1a1a",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #1a1a1a 0%, #c9a96e 50%, #fdf0f5 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(201,169,110,0.1)",
        "badge_text": "#8b1a4a",
    },
    "baby": {
        "primary": "#2d6a9f",
        "secondary": "#f7a8c4",
        "accent": "#4a90d9",
        "surface": "rgba(45,106,159,0.06)",
        "border": "rgba(45,106,159,0.2)",
        "bg": "#f0f8ff",
        "bg_alt": "#e8f4fd",
        "heading": "#2d6a9f",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #2d6a9f 0%, #f7a8c4 50%, #4a90d9 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(45,106,159,0.1)",
        "badge_text": "#1a4f7a",
    },
    "home": {
        "primary": "#2d4a3e",
        "secondary": "#e8b84b",
        "accent": "#4a7c6b",
        "surface": "rgba(45,74,62,0.06)",
        "border": "rgba(45,74,62,0.2)",
        "bg": "#f4f7f4",
        "bg_alt": "#edf4ee",
        "heading": "#2d4a3e",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #2d4a3e 0%, #e8b84b 50%, #4a7c6b 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(45,74,62,0.1)",
        "badge_text": "#1a3329",
    },
    "restaurant": {
    "restaurant": {
        "primary": "#D97706",
        "secondary": "#F59E0B",
        "accent": "#F97316",
        "surface": "rgba(217,119,6,0.06)",
        "border": "rgba(217,119,6,0.2)",
        "bg": "#FFFBEB",
        "bg_alt": "#FEF3C7",
        "heading": "#92400E",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #D97706 0%, #F59E0B 50%, #F97316 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(217,119,6,0.1)",
        "badge_text": "#D97706",
    },
    "beauty": {
        "primary": "#C08497",
        "secondary": "#E8B4C8",
        "accent": "#D48AB1",
        "surface": "rgba(192,132,151,0.06)",
        "border": "rgba(192,132,151,0.2)",
        "bg": "#FDF2F8",
        "bg_alt": "#FCE7F3",
        "heading": "#9D1754",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #C08497 0%, #E8B4C8 50%, #D48AB1 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(192,132,151,0.1)",
        "badge_text": "#C08497",
    },
    "retail": {
        "primary": "#059669",
        "secondary": "#34D399",
        "accent": "#10B981",
        "surface": "rgba(5,150,105,0.06)",
        "border": "rgba(5,150,105,0.2)",
        "bg": "#ECFDF5",
        "bg_alt": "#D1FAE5",
        "heading": "#065F46",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #059669 0%, #34D399 50%, #10B981 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(5,150,105,0.1)",
        "badge_text": "#059669",
    },
    "education": {
        "primary": "#7C3AED",
        "secondary": "#A78BFA",
        "accent": "#8B5CF6",
        "surface": "rgba(124,58,237,0.06)",
        "border": "rgba(124,58,237,0.2)",
        "bg": "#F5F3FF",
        "bg_alt": "#EDE9FE",
        "heading": "#5B21B6",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #7C3AED 0%, #A78BFA 50%, #8B5CF6 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(124,58,237,0.1)",
        "badge_text": "#7C3AED",
    },
    "healthcare": {
        "primary": "#2563EB",
        "secondary": "#60A5FA",
        "accent": "#3B82F6",
        "surface": "rgba(37,99,235,0.06)",
        "border": "rgba(37,99,235,0.2)",
        "bg": "#EFF6FF",
        "bg_alt": "#DBEAFE",
        "heading": "#1E40AF",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #2563EB 0%, #60A5FA 50%, #3B82F6 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(37,99,235,0.1)",
        "badge_text": "#2563EB",
    },
    "pharmacy": {
        "primary": "#0D9488",
        "secondary": "#5EEAD4",
        "accent": "#14B8A6",
        "surface": "rgba(13,148,136,0.06)",
        "border": "rgba(13,148,136,0.2)",
        "bg": "#F0FDFA",
        "bg_alt": "#CCFBF1",
        "heading": "#115E59",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #0D9488 0%, #5EEAD4 50%, #14B8A6 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(13,148,136,0.1)",
        "badge_text": "#0D9488",
    },
    "fitness": {
        "primary": "#DC2626",
        "secondary": "#F87171",
        "accent": "#EF4444",
        "surface": "rgba(220,38,38,0.06)",
        "border": "rgba(220,38,38,0.2)",
        "bg": "#FEF2F2",
        "bg_alt": "#FEE2E2",
        "heading": "#991B1B",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #DC2626 0%, #F87171 50%, #EF4444 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(220,38,38,0.1)",
        "badge_text": "#DC2626",
    },
    "automotive": {
        "primary": "#D97706",
        "secondary": "#FBBF24",
        "accent": "#F59E0B",
        "surface": "rgba(217,119,6,0.06)",
        "border": "rgba(217,119,6,0.2)",
        "bg": "#FFFBEB",
        "bg_alt": "#FDE68A",
        "heading": "#92400E",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #B45309 0%, #D97706 50%, #F59E0B 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(217,119,6,0.1)",
        "badge_text": "#D97706",
    },
    "manufacturing": {
        "primary": "#4F46E5",
        "secondary": "#818CF8",
        "accent": "#6366F1",
        "surface": "rgba(79,70,229,0.06)",
        "border": "rgba(79,70,229,0.2)",
        "bg": "#EEF2FF",
        "bg_alt": "#E0E7FF",
        "heading": "#3730A3",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #4F46E5 0%, #818CF8 50%, #6366F1 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(79,70,229,0.1)",
        "badge_text": "#4F46E5",
    },
    "agriculture": {
        "primary": "#16A34A",
        "secondary": "#4ADE80",
        "accent": "#22C55E",
        "surface": "rgba(22,163,74,0.06)",
        "border": "rgba(22,163,74,0.2)",
        "bg": "#F0FDF4",
        "bg_alt": "#DCFCE7",
        "heading": "#166534",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #16A34A 0%, #4ADE80 50%, #22C55E 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(22,163,74,0.1)",
        "badge_text": "#16A34A",
    },
    "hotel": {
        "primary": "#7C3AED",
        "secondary": "#C4B5FD",
        "accent": "#A78BFA",
        "surface": "rgba(124,58,237,0.06)",
        "border": "rgba(124,58,237,0.2)",
        "bg": "#F5F3FF",
        "bg_alt": "#EDE9FE",
        "heading": "#5B21B6",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #7C3AED 0%, #C4B5FD 50%, #A78BFA 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(124,58,237,0.1)",
        "badge_text": "#7C3AED",
    },
    "realestate": {
        "primary": "#1D4ED8",
        "secondary": "#60A5FA",
        "accent": "#3B82F6",
        "surface": "rgba(29,78,216,0.06)",
        "border": "rgba(29,78,216,0.2)",
        "bg": "#EFF6FF",
        "bg_alt": "#DBEAFE",
        "heading": "#1E3A8A",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #1D4ED8 0%, #60A5FA 50%, #3B82F6 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(29,78,216,0.1)",
        "badge_text": "#1D4ED8",
    },
    "services": {
        "primary": "#0891B2",
        "secondary": "#67E8F9",
        "accent": "#06B6D4",
        "surface": "rgba(8,145,178,0.06)",
        "border": "rgba(8,145,178,0.2)",
        "bg": "#ECFEFF",
        "bg_alt": "#CFFAFE",
        "heading": "#155E75",
        "text": "#1C1917",
        "text_muted": "#78716C",
        "hero_overlay": "linear-gradient(135deg, #0891B2 0%, #67E8F9 50%, #06B6D4 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(8,145,178,0.1)",
        "badge_text": "#0891B2",
    },
    "general": {
        "primary": "#2563EB",
        "secondary": "#60A5FA",
        "accent": "#3B82F6",
        "surface": "rgba(37,99,235,0.06)",
        "border": "rgba(37,99,235,0.2)",
        "bg": "#F8FAFC",
        "bg_alt": "#F1F5F9",
        "heading": "#1E293B",
        "text": "#1C1917",
        "text_muted": "#64748B",
        "hero_overlay": "linear-gradient(135deg, #2563EB 0%, #60A5FA 50%, #3B82F6 100%)",
        "card_bg": "#FFF",
        "badge": "rgba(37,99,235,0.1)",
        "badge_text": "#2563EB",
    },
}

CATEGORY_FONTS: Dict[str, Dict[str, str]] = {
    "fashion": {
        "heading": "'Cormorant Garamond', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "jewelry": {
        "heading": "'Cormorant Garamond', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "skincare": {
        "heading": "'Playfair Display', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "baby": {
        "heading": "'Nunito', sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "48px",
    },
    "home": {
        "heading": "'Lora', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "52px",
    },
    "restaurant": {
        "heading": "'Playfair Display', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap",
        "hero_size": "64px",
    },
    "beauty": {
        "heading": "'Playfair Display', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700;800;900&family=Inter:wght@400;500;600;700&display=swap",
        "hero_size": "60px",
    },
    "retail": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "education": {
        "heading": "'Poppins', sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800;900&family=Inter:wght@400;500;600;700&display=swap",
        "hero_size": "56px",
    },
    "healthcare": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "pharmacy": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "fitness": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "64px",
    },
    "automotive": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "manufacturing": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "agriculture": {
        "heading": "'Merriweather', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "https://fonts.googleapis.com/css2?family=Merriweather:wght@400;700;900&family=Inter:wght@400;500;600;700&display=swap",
        "hero_size": "56px",
    },
    "hotel": {
        "heading": "'Cormorant Garamond', serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap",
        "hero_size": "64px",
    },
    "realestate": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "services": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
    "general": {
        "heading": "'Inter', -apple-system, sans-serif",
        "body": "'Inter', -apple-system, sans-serif",
        "import": "",
        "hero_size": "56px",
    },
}


def build_font_links(category: str) -> str:
    """Build Google Fonts <link> tags for category."""
    COMPREHENSIVE_URL = (
        "https://fonts.googleapis.com/css2?"
        "family=Playfair+Display:wght@400;600;700&"
        "family=Inter:wght@300;400;500;600&"
        "family=Cormorant+Garamond:wght@400;600;700&"
        "family=Nunito:wght@400;600;700&"
        "family=Lora:wght@400;600;700&"
        "family=Poppins:wght@400;500;600;700&"
        "family=Merriweather:wght@400;700&"
        "family=Barlow:wght@400;500;600;700&"
        "family=Barlow+Condensed:wght@500;700&"
        "display=swap"
    )
    return f'  <link href="{COMPREHENSIVE_URL}" rel="stylesheet" />'


def build_base_css(category: str) -> str:
    """Generate complete CSS for a given category."""
    p = CATEGORY_PALETTES.get(category, CATEGORY_PALETTES["general"])
    f = CATEGORY_FONTS.get(category, CATEGORY_FONTS["general"])

    heading = f["heading"]
    body = f["body"]
    hero_size = f["hero_size"]

    return f"""    :root {{
      --primary: {p['primary']};
      --secondary: {p['secondary']};
      --accent: {p['accent']};
      --surface: {p['surface']};
      --border: {p['border']};
      --bg: {p['bg']};
      --bg-alt: {p['bg_alt']};
      --heading: {p['heading']};
      --text: {p['text']};
      --text-muted: {p['text_muted']};
      --card-bg: {p['card_bg']};
      --badge: {p['badge']};
      --badge-text: {p['badge_text']};
      --hero-gradient: {p['hero_overlay']};
      --font-heading: {heading};
      --font-body: {body};
      --radius: 12px;
      --radius-sm: 8px;
      --radius-full: 9999px;
      --shadow-card: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
      --shadow-hover: 0 10px 25px rgba(0,0,0,0.08);
      --transition: 0.25s ease;
    }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; scroll-padding-top: 76px; }}
    body {{
      font-family: var(--font-body);
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: var(--primary); text-decoration: none; transition: color var(--transition); }}
    a:hover {{ color: var(--accent); }}
    img {{ max-width: 100%; }}
    .container {{ max-width: 1120px; margin: 0 auto; padding: 0 24px; }}

    /* \u2500\u2500 Navigation \u2500\u2500 */
    .navbar {{
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      height: 72px;
      background: rgba(255,255,255,0.92);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      border-bottom: 1px solid rgba(0,0,0,0.06);
    }}
    .navbar .container {{
      display: flex; align-items: center; justify-content: space-between; height: 100%;
    }}
    .nav-brand {{
      font-family: var(--font-heading);
      font-size: 22px; font-weight: 800;
      color: var(--heading); text-decoration: none;
    }}
    .nav-links {{ display: flex; gap: 28px; list-style: none; }}
    .nav-links a {{
      color: var(--text-muted); text-decoration: none;
      font-size: 14px; font-weight: 500;
      transition: color var(--transition);
    }}
    .nav-links a:hover {{ color: var(--primary); }}
    .nav-toggle {{ display: none; background: none; border: none; font-size: 26px; cursor: pointer; color: var(--heading); }}
    .nav-cta {{
      display: inline-flex; align-items: center;
      background: var(--primary); color: #FFF;
      padding: 10px 22px; border-radius: var(--radius-sm);
      font-size: 14px; font-weight: 600;
      transition: background var(--transition), transform var(--transition);
    }}
    .nav-cta:hover {{ background: var(--accent); color: #FFF; transform: translateY(-1px); }}

    /* \u2500\u2500 Hero \u2500\u2500 */
    .hero {{
      position: relative;
      min-height: 70vh;
      display: flex; align-items: center; justify-content: center;
      text-align: center;
      padding: 120px 24px 80px;
      overflow: hidden;
    }}
    .hero-bg {{
      position: absolute; inset: 0;
      background: var(--hero-gradient);
      opacity: 0.08;
      z-index: 0;
    }}
    .hero-bg::after {{
      content: '';
      position: absolute; inset: 0;
      background: radial-gradient(ellipse at 30% 40%, var(--primary) 0%, transparent 60%);
      opacity: 0.04;
    }}
    .hero-content {{ position: relative; z-index: 2; max-width: 800px; }}
    .hero-badge {{
      display: inline-block;
      background: var(--badge);
      color: var(--badge-text);
      font-size: 12px; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase;
      padding: 6px 16px; border-radius: var(--radius-full);
      margin-bottom: 20px;
    }}
    .hero h1 {{
      font-family: var(--font-heading);
      font-size: {hero_size}; font-weight: 900;
      line-height: 1.08; letter-spacing: -0.02em;
      color: var(--heading);
      margin-bottom: 16px;
    }}
    .hero-sub {{
      font-size: 18px; color: var(--text-muted);
      max-width: 520px; margin: 0 auto 24px;
    }}
    .hero-address {{
      font-size: 14px; color: var(--text-muted);
      max-width: 460px; margin: 0 auto 32px;
    }}
    .hero-actions {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }}
    .btn {{
      display: inline-flex; align-items: center; gap: 8px;
      padding: 14px 30px; border-radius: var(--radius-sm);
      font-size: 15px; font-weight: 600; text-decoration: none;
      border: none; cursor: pointer;
      transition: all var(--transition);
    }}
    .btn-primary {{
      background: var(--primary); color: #FFF;
      box-shadow: 0 4px 14px rgba(0,0,0,0.1);
    }}
    .btn-primary:hover {{ background: var(--accent); color: #FFF; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.15); }}
    .btn-outline {{
      background: transparent; color: var(--primary);
      border: 1.5px solid var(--primary);
    }}
    .btn-outline:hover {{ background: var(--surface); color: var(--heading); border-color: var(--accent); }}

    /* \u2500\u2500 Section \u2500\u2500 */
    .section {{ padding: 80px 0; }}
    .section-shaded {{ background: var(--bg-alt); }}
    .section-head {{ text-align: center; margin-bottom: 48px; }}
    .eyebrow {{
      display: inline-block;
      font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
      color: var(--primary); margin-bottom: 8px;
    }}
    .section-head h2 {{
      font-family: var(--font-heading);
      font-size: 34px; font-weight: 800;
      color: var(--heading); letter-spacing: -0.02em;
      margin-bottom: 12px;
    }}
    .hr {{
      width: 50px; height: 3px;
      background: var(--hero-gradient); border-radius: 2px;
      margin: 0 auto;
      opacity: 0.6;
    }}

    /* \u2500\u2500 About \u2500\u2500 */
    .about-grid {{
      display: grid; grid-template-columns: 1.4fr 1fr; gap: 40px; align-items: start;
    }}
    .about-text h3 {{
      font-family: var(--font-heading);
      font-size: 26px; font-weight: 700;
      color: var(--heading); margin-bottom: 14px;
    }}
    .about-text p {{
      color: var(--text-muted); line-height: 1.7; margin-bottom: 12px;
    }}
    .about-card {{
      background: var(--card-bg); border-radius: var(--radius);
      padding: 36px 28px; text-align: center;
      box-shadow: var(--shadow-card);
      border: 1px solid rgba(0,0,0,0.05);
    }}
    .about-icon {{ font-size: 48px; display: block; margin-bottom: 16px; }}
    .about-card p {{ color: var(--text-muted); font-size: 14px; line-height: 1.6; }}

    /* \u2500\u2500 Services \u2500\u2500 */
    .services-grid {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
    }}
    .service-card {{
      background: var(--card-bg); border-radius: var(--radius);
      padding: 32px 24px; text-align: center;
      box-shadow: var(--shadow-card);
      border: 1px solid rgba(0,0,0,0.04);
      transition: all var(--transition);
    }}
    .service-card:hover {{
      transform: translateY(-4px);
      box-shadow: var(--shadow-hover);
      border-color: var(--border);
    }}
    .service-icon {{
      display: inline-flex; align-items: center; justify-content: center;
      width: 56px; height: 56px; font-size: 26px;
      background: var(--surface); border-radius: var(--radius-sm);
      margin-bottom: 16px;
    }}
    .service-card h4 {{
      font-family: var(--font-heading);
      font-size: 17px; font-weight: 700; margin-bottom: 8px; color: var(--heading);
    }}
    .service-card p {{ font-size: 14px; color: var(--text-muted); line-height: 1.6; }}

    /* \u2500\u2500 Process \u2500\u2500 */
    .process-grid {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px;
    }}
    .step-card {{
      background: var(--card-bg); border-radius: var(--radius);
      padding: 32px 24px; text-align: center;
      box-shadow: var(--shadow-card);
      border: 1px solid rgba(0,0,0,0.04);
      position: relative;
    }}
    .step-num {{
      display: inline-flex; align-items: center; justify-content: center;
      width: 40px; height: 40px; border-radius: 50%;
      background: var(--primary); color: #FFF;
      font-size: 16px; font-weight: 700;
      margin-bottom: 14px;
    }}
    .step-card h4 {{
      font-family: var(--font-heading);
      font-size: 16px; font-weight: 700; margin-bottom: 6px; color: var(--heading);
    }}
    .step-card p {{ font-size: 14px; color: var(--text-muted); line-height: 1.6; }}

    /* \u2500\u2500 Why Choose Us \u2500\u2500 */
    .why-grid {{
      display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;
    }}
    .why-card {{
      background: var(--card-bg); border-radius: var(--radius);
      padding: 28px 20px; text-align: center;
      box-shadow: var(--shadow-card);
      border: 1px solid rgba(0,0,0,0.04);
      transition: border-color var(--transition);
    }}
    .why-card:hover {{ border-color: var(--border); }}
    .why-icon {{ font-size: 32px; display: block; margin-bottom: 12px; }}
    .why-card h4 {{
      font-size: 15px; font-weight: 700; margin-bottom: 6px; color: var(--heading);
    }}
    .why-card p {{ font-size: 13px; color: var(--text-muted); line-height: 1.6; }}

    /* \u2500\u2500 Reviews \u2500\u2500 */
    .reviews-grid {{
      display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;
    }}
    .review-card {{
      background: var(--card-bg); border-radius: var(--radius);
      padding: 28px 22px;
      box-shadow: var(--shadow-card);
      border: 1px solid rgba(0,0,0,0.04);
    }}
    .review-stars {{ color: #F59E0B; font-size: 16px; margin-bottom: 10px; letter-spacing: 2px; }}
    .review-card blockquote {{
      font-size: 14px; color: var(--text-muted); line-height: 1.7;
      font-style: italic; margin-bottom: 14px;
    }}
    .review-author {{ font-size: 13px; font-weight: 600; color: var(--heading); }}
    .review-location {{ font-size: 12px; color: var(--text-muted); }}

    /* \u2500\u2500 Contact \u2500\u2500 */
    .contact-grid {{
      display: grid; grid-template-columns: 1fr 1fr; gap: 32px;
    }}
    .contact-card {{
      background: var(--card-bg); border-radius: var(--radius);
      padding: 32px 28px;
      box-shadow: var(--shadow-card);
      border: 1px solid rgba(0,0,0,0.04);
    }}
    .contact-card h3 {{
      font-family: var(--font-heading);
      font-size: 20px; font-weight: 700; margin-bottom: 20px; color: var(--heading);
    }}
    .contact-form {{ display: flex; flex-direction: column; gap: 12px; }}
    .contact-form input,
    .contact-form textarea {{
      padding: 12px 16px; border: 1px solid rgba(0,0,0,0.1);
      border-radius: var(--radius-sm); font-size: 14px;
      font-family: var(--font-body); outline: none;
      background: var(--bg); transition: border-color var(--transition);
    }}
    .contact-form input:focus,
    .contact-form textarea:focus {{
      border-color: var(--primary); box-shadow: 0 0 0 3px var(--surface);
    }}
    .contact-form textarea {{ min-height: 100px; resize: vertical; }}
    .info-row {{
      display: flex; align-items: center; gap: 12px;
      padding: 12px 0; border-bottom: 1px solid rgba(0,0,0,0.04);
    }}
    .info-row:last-child {{ border-bottom: none; }}
    .info-icon {{ font-size: 18px; width: 24px; text-align: center; }}
    .info-row div {{ font-size: 14px; color: var(--text-muted); }}
    .info-row a {{ color: var(--primary); font-weight: 500; }}
    .info-row a:hover {{ color: var(--accent); }}

    /* \u2500\u2500 Footer \u2500\u2500 */
    .footer {{
      background: var(--heading); color: rgba(255,255,255,0.7);
      padding: 40px 24px 32px; text-align: center;
    }}
    .footer h3 {{
      font-family: var(--font-heading);
      font-size: 20px; font-weight: 800; color: #FFF; margin-bottom: 6px;
    }}
    .footer p {{ font-size: 14px; margin-bottom: 16px; opacity: 0.7; }}
    .footer-credit {{ font-size: 13px; opacity: 0.6; }}

    /* \u2500\u2500 WhatsApp Float \u2500\u2500 */
    .wa-float {{
      position: fixed; bottom: 24px; right: 24px; z-index: 999;
      width: 54px; height: 54px; border-radius: 50%;
      background: #25D366;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 16px rgba(37,211,102,0.4);
      text-decoration: none;
      transition: transform var(--transition);
    }}
    .wa-float:hover {{ transform: scale(1.1); }}
    .wa-float svg {{ width: 24px; height: 24px; fill: #FFF; }}

    /* \u2500\u2500 Animations \u2500\u2500 */
    .fade {{
      opacity: 0; transform: translateY(24px);
      transition: all 0.6s cubic-bezier(0.22,1,0.36,1);
    }}
    .fade.show {{ opacity: 1; transform: translateY(0); }}

    /* \u2500\u2500 Responsive \u2500\u2500 */
    @media (max-width: 768px) {{
      .nav-links, .nav-cta {{ display: none; }}
      .nav-toggle {{ display: block; }}
      .nav-links.open {{
        display: flex; flex-direction: column; position: absolute; top: 72px; left: 0; right: 0;
        background: rgba(255,255,255,0.98);
        backdrop-filter: blur(14px);
        padding: 20px 24px; gap: 16px; border-bottom: 1px solid rgba(0,0,0,0.06);
      }}
      .hero h1 {{ font-size: 36px; }}
      .hero-sub {{ font-size: 16px; }}
      .section {{ padding: 56px 0; }}
      .section-head h2 {{ font-size: 26px; }}
      .about-grid {{ grid-template-columns: 1fr; }}
      .services-grid, .process-grid, .why-grid, .reviews-grid {{ grid-template-columns: 1fr; gap: 16px; }}
      .contact-grid {{ grid-template-columns: 1fr; }}
    }}
    @media (max-width: 480px) {{
      .hero h1 {{ font-size: 30px; }}
      .hero-actions {{ flex-direction: column; align-items: center; }}
      .hero {{ padding: 100px 16px 60px; }}
      .why-grid {{ grid-template-columns: 1fr 1fr; }}
    }}

    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
      }}
    }}"""
