#!/usr/bin/env python3
"""Generate a Branded Demo PDF for Test Bakery & Cafe \u2014 ExecERP Inventory Module Trojan Horse."""

import os
from weasyprint import HTML

FONT_DIR = os.path.expanduser("~/.local/share/fonts")
OUT_DIR = os.path.expanduser("~/kb/lead-gen/demos")
os.makedirs(OUT_DIR, exist_ok=True)

def build_css():
    return f"""
@font-face {{
    font-family: 'Inter';
    src: url('file://{FONT_DIR}/Inter-Regular.ttf') format('truetype');
    font-weight: 400;
}}
@font-face {{
    font-family: 'Inter';
    src: url('file://{FONT_DIR}/Inter-Bold.ttf') format('truetype');
    font-weight: 700;
}}
@font-face {{
    font-family: 'Inter';
    src: url('file://{FONT_DIR}/Inter-Black.ttf') format('truetype');
    font-weight: 900;
}}
@font-face {{
    font-family: 'Inter';
    src: url('file://{FONT_DIR}/Inter-SemiBold.ttf') format('truetype');
    font-weight: 600;
}}
@font-face {{
    font-family: 'JetBrains Mono';
    src: url('file://{FONT_DIR}/JetBrainsMonoNerd/JetBrainsMonoNerdFont-Regular.ttf') format('truetype');
}}

@page {{
    size: A4;
    margin: 62px 45px 50px 45px;
    @bottom-left {{
        content: "Skarbol Tech \\2022 https://skarboltech.com";
        font-family: 'Inter';
        font-size: 7.5pt;
        color: #94A3B8;
    }}
    @bottom-right {{
        content: counter(page);
        font-family: 'Inter';
        font-size: 8pt;
        font-weight: 700;
        color: #94A3B8;
    }}
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: 'Inter', sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #E2E8F0;
    background: #0B1221;
}}

.header {{
    position: fixed;
    top: -48px;
    left: -45px;
    right: -45px;
    height: 48px;
    background: #050A14;
    border-bottom: 1.5px solid #00E5FF;
    display: flex;
    align-items: center;
    padding: 0 45px;
}}
.header-brand {{
    font-family: 'Inter';
    font-weight: 700;
    font-size: 10pt;
    color: #F8FAFC;
}}
.header-tagline {{
    font-family: 'Inter';
    font-size: 7pt;
    color: #00E5FF;
    margin-left: 12px;
}}

.hero {{
    text-align: center;
    margin-top: 10px;
    margin-bottom: 4px;
}}
.hero h1 {{
    font-family: 'Inter';
    font-weight: 900;
    font-size: 30pt;
    color: #F8FAFC;
    line-height: 1.15;
    margin-bottom: 4px;
}}
.hero .subtitle {{
    font-size: 12pt;
    color: #00E5FF;
    font-weight: 600;
    margin-bottom: 6px;
}}
.hero .price-badge {{
    display: inline-block;
    margin-top: 6px;
    background: linear-gradient(135deg, #0A4FD9, #00E5FF);
    color: #FFFFFF;
    font-weight: 700;
    font-size: 14pt;
    padding: 10px 28px;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(10, 79, 217, 0.4);
}}

h2 {{
    font-family: 'Inter';
    font-weight: 700;
    font-size: 18pt;
    color: #0A4FD9;
    margin-top: 18px;
    margin-bottom: 10px;
    border-bottom: 1px solid #1E2D45;
    padding-bottom: 4px;
}}
h3 {{
    font-family: 'Inter';
    font-weight: 600;
    font-size: 14pt;
    color: #00E5FF;
    margin-top: 14px;
    margin-bottom: 8px;
}}

p {{
    font-size: 10pt;
    line-height: 1.5;
    color: #E2E8F0;
    text-align: justify;
    margin-bottom: 6px;
}}

strong {{ font-weight: 700; color: #F8FAFC; }}
em {{ font-style: italic; }}

.pricing-grid {{
    display: flex;
    gap: 10px;
    margin: 10px 0;
}}
.pricing-card {{
    flex: 1;
    background: rgba(14, 24, 37, 0.95);
    border: 1px solid rgba(226, 232, 240, 0.08);
    border-radius: 12px;
    padding: 14px 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    text-align: center;
}}
.pricing-card.featured {{
    border-color: #0A4FD9;
    position: relative;
}}
.pricing-card.featured::before {{
    content: "BEST VALUE";
    position: absolute;
    top: -8px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #0A4FD9, #00E5FF);
    color: #F8FAFC;
    font-size: 7pt;
    font-weight: 700;
    padding: 2px 12px;
    border-radius: 4px;
}}
.pricing-card h4 {{
    font-weight: 700;
    font-size: 13pt;
    color: #F8FAFC;
    margin-bottom: 2px;
}}
.pricing-card .price {{
    font-size: 20pt;
    font-weight: 900;
    color: #00E5FF;
    margin: 4px 0;
}}
.pricing-card .price span {{
    font-size: 10pt;
    font-weight: 400;
    color: #94A3B8;
}}
.pricing-card ul {{
    list-style: none;
    padding-left: 0;
    text-align: left;
    margin: 6px 0;
}}
.pricing-card li {{
    font-size: 9pt;
    line-height: 1.6;
    color: #E2E8F0;
    padding-left: 14px;
    position: relative;
}}
.pricing-card li::before {{
    content: "\\2713";
    position: absolute;
    left: 0;
    color: #00E5FF;
}}

.process-grid {{
    display: flex;
    gap: 8px;
    margin: 10px 0;
}}
.step {{
    flex: 1;
    background: rgba(14, 24, 37, 0.95);
    border: 1px solid rgba(226, 232, 240, 0.08);
    border-radius: 10px;
    padding: 12px 10px;
    text-align: center;
}}
.step .number {{
    display: inline-block;
    background: linear-gradient(135deg, #0A4FD9, #00E5FF);
    color: #F8FAFC;
    font-weight: 700;
    font-size: 12pt;
    width: 30px;
    height: 30px;
    line-height: 30px;
    border-radius: 50%;
    margin-bottom: 4px;
}}
.step .label {{
    font-weight: 700;
    font-size: 9pt;
    color: #F8FAFC;
    display: block;
    margin-bottom: 2px;
}}
.step .desc {{
    font-size: 8pt;
    color: #94A3B8;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 9pt;
}}
th {{
    background: #0A4FD9;
    color: #F8FAFC;
    font-weight: 700;
    text-align: left;
    padding: 6px 8px;
}}
td {{
    padding: 6px 8px;
    color: #E2E8F0;
}}
tr:nth-child(even) td {{
    background: #0E1825;
}}
tr:nth-child(odd) td {{
    background: #0B1221;
}}
table, th, td {{
    border: 0.3px solid #1E2D45;
}}

ul {{
    list-style: none;
    padding-left: 0;
    margin-bottom: 6px;
}}
li {{
    font-size: 10pt;
    line-height: 1.5;
    color: #E2E8F0;
    margin-bottom: 2px;
    padding-left: 14px;
    position: relative;
}}
li::before {{
    content: "\\2022";
    position: absolute;
    left: 0;
    color: #00E5FF;
}}

.tag {{
    display: inline-block;
    background: rgba(10, 79, 217, 0.2);
    border: 1px solid rgba(0, 229, 255, 0.3);
    color: #00E5FF;
    font-size: 8pt;
    font-weight: 600;
    padding: 4px 12px;
    border-radius: 20px;
    margin: 2px 3px;
}}

.tagline {{
    text-align: center;
    font-size: 8pt;
    color: #94A3B8;
    margin-top: 8px;
}}

hr {{
    border: none;
    border-top: 0.5px solid #1E2D45;
    margin: 10px 0;
}}

.trojan-box {{
    background: linear-gradient(135deg, rgba(10, 79, 217, 0.15), rgba(0, 229, 255, 0.08));
    border: 1px solid #00E5FF;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 10px 0;
    text-align: center;
}}
.trojan-box .icon {{
    font-size: 28pt;
    margin-bottom: 4px;
}}
.trojan-box h3 {{
    margin-top: 0;
    margin-bottom: 4px;
}}
.trojan-box p {{
    text-align: center;
    font-size: 10pt;
}}

.footer-contact {{
    text-align: center;
    margin-top: 16px;
    padding: 14px;
    background: rgba(14, 24, 37, 0.95);
    border: 1px solid rgba(226, 232, 240, 0.08);
    border-radius: 12px;
}}
"""

def build_html():
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>{build_css()}</style>
</head>
<body>

<div class="header">
    <span class="header-brand">SKARBOL TECH</span>
    <span class="header-tagline">Building Tomorrow&rsquo;s Intelligence Today</span>
</div>

<!-- ====== HERO ====== -->
<div class="hero">
    <div class="subtitle">&#127860; Digital Transformation for Test Bakery &amp; Cafe</div>
    <h1>From Kitchen to<br>Digital Empire</h1>
    <p style="text-align:center; max-width:460px; margin:4px auto;">
        A complete digital ecosystem for your restaurant &mdash; inventory intelligence, 
        online presence, and AI-powered operations. All built for Gulshan, Dhaka.
    </p>
    <div class="price-badge">Start from 15,000&#2547; BDT</div>
</div>

<hr>

<!-- ====== TROJAN HORSE \u2014 INVENTORY MODULE ====== -->
<h2>&#128220; The Strategy: ExecERP Inventory Module</h2>

<div class="trojan-box">
    <div class="icon">&#127859;</div>
    <h3>Start Here: Inventory Intelligence</h3>
    <p>
        The biggest hidden cost for any bakery or cafe is <strong>waste</strong> &mdash; 
        expired ingredients, overstocked items, theft, and manual counting errors. 
        We solve <em>one</em> problem first, then expand.
    </p>
</div>

<h3>Your Pain Points (Bakery &amp; Cafe Edition)</h3>
<ul>
    <li><strong>Ingredient tracking:</strong> How much flour, sugar, butter did you use today? Last week? No idea without manual counting</li>
    <li><strong>Expiry management:</strong> Dairy, eggs, fresh produce &mdash; without tracking, you&rsquo;re throwing money in the bin</li>
    <li><strong>Recipe costing:</strong> Do you know the exact cost of each pastry, cake, or coffee you sell?</li>
    <li><strong>Supplier chaos:</strong> Multiple vendors, inconsistent delivery schedules, no central view of what&rsquo;s arriving when</li>
    <li><strong>Manual processes:</strong> Spreadsheets, notebook scribbles, WhatsApp orders &mdash; none of it talks to each other</li>
</ul>

<h3>ExecERP Inventory Module Solves This</h3>
<table>
    <tr><th style="width:38%">Feature</th><th>How It Helps Your Bakery</th></tr>
    <tr><td>Real-time stock tracking</td><td>Know exactly how many bags of flour, packs of butter, and cartons of milk you have &mdash; from your phone</td></tr>
    <tr><td>Expiry date alerts</td><td>Get notified 3 days before dairy or produce expires &mdash; stop waste before it happens</td></tr>
    <tr><td>Recipe costing engine</td><td>Enter your recipes once &mdash; see profit margin per item automatically</td></tr>
    <tr><td>Supplier management</td><td>Track all vendors, compare prices, auto-generate purchase orders</td></tr>
    <tr><td>Waste analytics</td><td>Daily/ weekly reports: what&rsquo;s being wasted, by how much, and what it&rsquo;s costing you</td></tr>
    <tr><td>Barcode / QR scanning</td><td>Scan incoming stock, scan sold items &mdash; zero manual entry</td></tr>
    <tr><td>AI demand forecasting</td><td>Predict tomorrow&rsquo;s sales based on history, weather, day of week &mdash; order exactly what you need</td></tr>
    <tr><td>Multi-branch ready</td><td>Expand to 2nd location? All inventory data lives in one place</td></tr>
</table>

<hr>

<!-- ====== FULL ECOSYSTEM ====== -->
<h2>&#128640; The Full Digital Ecosystem</h2>
<p>
    Start with inventory. Then grow into your complete digital presence. 
    Here&rsquo;s the full stack we recommend for Test Bakery &amp; Cafe:
</p>

<div class="pricing-grid">

<div class="pricing-card">
    <h4>Phase 1</h4>
    <div class="price">15,000&#2547; <span>one-time</span></div>
    <ul>
        <li>Starter website (1 page)</li>
        <li>Menu / catalogue display</li>
        <li>Contact + WhatsApp button</li>
        <li>Google Maps location</li>
        <li>Free domain + 1yr hosting</li>
        <li>Delivery: 24 hours</li>
    </ul>
</div>

<div class="pricing-card featured">
    <h4>Phase 2</h4>
    <div class="price">25,000&#2547; <span>one-time</span></div>
    <ul>
        <li><strong>ExecERP Inventory Module</strong></li>
        <li>Real-time stock tracking</li>
        <li>Expiry alerts</li>
        <li>Recipe costing engine</li>
        <li>Supplier management</li>
        <li>Waste analytics dashboard</li>
        <li>AI demand forecasting</li>
        <li>Setup + training included</li>
    </ul>
</div>

<div class="pricing-card">
    <h4>Phase 3</h4>
    <div class="price">45,000&#2547; <span>one-time</span></div>
    <ul>
        <li>Full business website (up to 10 pages)</li>
        <li>Online ordering / booking system</li>
        <li>Customer reviews &amp; gallery</li>
        <li>AI chatbot (ExecMate)</li>
        <li>Social media integration</li>
        <li>Advanced SEO + Analytics</li>
        <li>ExecERP Inventory + Sales sync</li>
        <li>Free hosting (2 years)</li>
        <li>3 months free maintenance</li>
    </ul>
</div>

</div>

<hr>

<!-- ====== WHY INVENTORY FIRST ====== -->
<h2>&#128200; The Trojan Horse Approach</h2>

<p>
    <strong>Why start with inventory?</strong> Because it&rsquo;s the one problem every 
    restaurant owner <em>feels</em> every single day. You wake up wondering: 
    <em>&ldquo;Do I have enough eggs for today&rsquo;s orders? How much did I spend on 
    supplies last month? Why is my wastage so high?&rdquo;</em>
</p>

<p>
    Once ExecERP Inventory is running, you&rsquo;ll see the savings immediately. 
    Then the question becomes natural: <em>&ldquo;Can we add sales tracking? Can customers 
    order online? Can I manage this from my phone?&rdquo;</em> &mdash; and we&rsquo;re there 
    with the next phase.
</p>

<table>
    <tr><th style="width:25%">Phase</th><th style="width:30%">What They Get</th><th>Why It Works</th></tr>
    <tr><td><strong>1. Inventory</strong></td><td>Stop waste, know your costs, order smarter</td><td>Solves daily pain &mdash; immediate ROI visible in weeks</td></tr>
    <tr><td><strong>2. Website</strong></td><td>Customers find you on Google, see your menu, order online</td><td>Business development &mdash; they see the inventory works, now grow revenue</td></tr>
    <tr><td><strong>3. Full ERP</strong></td><td>Sales, HR, finance, AI forecasting &mdash; everything connected</td><td>Complete transformation &mdash; they&rsquo;re already dependent on the system</td></tr>
</table>

<hr>

<!-- ====== WHY SKARBOL TECH ====== -->
<h2>Why Skarbol Tech?</h2>

<p>
    Skarbol Tech is Bangladesh&rsquo;s first fully integrated AI + Automation + IoT ecosystem company. 
    We don&rsquo;t just sell software &mdash; we build complete digital ecosystems for Bangladeshi SMEs. 
    ExecERP is built for the local market: bKash/Nagad integration, Bengali language support, 
    mobile-first interfaces, and pricing that makes sense for local businesses.
</p>

<ul>
    <li><strong>Local Expertise:</strong> We understand Gulshan, Dhaka &mdash; the market, the challenges, the opportunities</li>
    <li><strong>Bangladeshi Pricing:</strong> One-time payments, no subscription traps. Free hosting included</li>
    <li><strong>Fast Implementation:</strong> Inventory module live in 48 hours. Website in 24 hours</li>
    <li><strong>AI-Powered:</strong> Every product ships with AI capabilities &mdash; demand forecasting, chatbot, analytics</li>
    <li><strong>End-to-End Support:</strong> Setup, training, and ongoing assistance &mdash; we don&rsquo;t disappear after the sale</li>
    <li><strong>Full Ecosystem:</strong> Inventory &rarr; Website &rarr; Online Orders &rarr; ERP &rarr; AI &mdash; we grow with you</li>
</ul>

<hr>

<!-- ====== HOW IT WORKS ====== -->
<h2>How It Works</h2>

<div class="process-grid">
    <div class="step">
        <div class="number">1</div>
        <div class="label">Free Consultation</div>
        <div class="desc">20-minute visit to your cafe &mdash; we see your current process, identify quick wins</div>
    </div>
    <div class="step">
        <div class="number">2</div>
        <div class="label">Inventory Setup</div>
        <div class="desc">We install ExecERP Inventory Module, input your stock, configure expiry alerts &amp; suppliers</div>
    </div>
    <div class="step">
        <div class="number">3</div>
        <div class="label">Go Live</div>
        <div class="desc">You start tracking inventory in real-time &mdash; training included, results visible immediately</div>
    </div>
    <div class="step">
        <div class="number">4</div>
        <div class="label">Growth</div>
        <div class="desc">Add website, online ordering, full ERP &mdash; whenever you&rsquo;re ready</div>
    </div>
</div>

<hr>

<!-- ====== FOR TEST BAKERY & CAFE ====== -->
<h2>&#127968; For Test Bakery &amp; Cafe &mdash; Gulshan, Dhaka</h2>
<p>
    Located in Gulshan, you&rsquo;re in one of Dhaka&rsquo;s busiest business districts. 
    Your customers are professionals, families, and food lovers who search online before 
    choosing where to eat. A digital presence isn&rsquo;t optional anymore &mdash; it&rsquo;s 
    how you get found, trusted, and chosen.
</p>
<p>
    This proposal is tailored specifically for your bakery and cafe. Every recommendation 
    is based on what works for restaurants in your area. No generic templates &mdash; just 
    practical solutions for <strong>Test Bakery &amp; Cafe</strong>.
</p>

<div style="text-align:center; margin:6px 0;">
    <span class="tag">&#127860; Restaurant</span>
    <span class="tag">&#127859; Bakery</span>
    <span class="tag">&#9749; Cafe</span>
    <span class="tag">&#128221; Inventory</span>
    <span class="tag">&#127760; Website</span>
    <span class="tag">&#129302; AI-Powered</span>
</div>

<hr>

<!-- ====== CONTACT / CTA ====== -->
<div class="footer-contact">
    <p style="text-align:center; font-size:11pt; color:#F8FAFC; margin-bottom:4px;">
        <strong>Ready to stop the waste and start growing?</strong>
    </p>
    <p style="text-align:center; font-size:9pt; color:#94A3B8; margin-bottom:6px;">
        Free consultation &mdash; we&rsquo;ll visit your cafe and show you exactly how much you can save.
    </p>
    <p style="text-align:center; font-size:10pt; color:#E2E8F0;">
        <strong>Call / WhatsApp:</strong> +880 1710 322794 &nbsp;&#124;&nbsp;
        <strong>Email:</strong> hello@skarboltech.com
    </p>
    <p style="text-align:center; font-size:8pt; color:#94A3B8; margin-top:4px;">
        Skarbol Tech &mdash; Gulshan, Dhaka &mdash; https://skarboltech.com
    </p>
</div>

</body>
</html>
"""

if __name__ == '__main__':
    html_content = build_html()
    out_path = os.path.join(OUT_DIR, "Test_Bakery_Cafe_Demo.pdf")
    HTML(string=html_content).write_pdf(out_path)
    print(f"\u2705 Demo PDF generated: {out_path}")
