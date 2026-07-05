import csv, html, io, json, os, sys, re, subprocess, threading, time, signal, sqlite3
import hashlib, secrets, smtplib, string
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import requests
import openpyxl
from openpyxl.styles import Alignment

# MongoDB + Cloudinary storage layer
try:
    import mongo_db
    import cloudinary_storage
    USE_MONGO = bool(os.environ.get('MONGODB_URI'))
except ImportError:
    mongo_db = None
    cloudinary_storage = None
    USE_MONGO = False

# Load .env (force override shell env so .env values always win)
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ[k.strip()] = v.strip()

GMAIL_USER = os.environ.get('GMAIL_USER', '')
GMAIL_APP_PASS = os.environ.get('GMAIL_APP_PASS', '')

def send_verification_email(to_email, code):
    if not GMAIL_USER or not GMAIL_APP_PASS:
        print(f"[email] SMTP not configured, skipping verification to {to_email}", flush=True)
        return False
    msg = MIMEText(f'''<div style="font-family:Inter,sans-serif;background:#050A14;padding:32px;text-align:center">
<div style="max-width:400px;margin:0 auto;background:rgba(14,24,37,0.95);border-radius:16px;padding:32px;border:1px solid rgba(226,232,240,0.08)">
<div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,#0A4FD9,#00E5FF);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;color:#fff;margin:0 auto 16px">S</div>
<h2 style="color:#F8FAFC;font-size:18px;margin:0 0 8px">Verify your email</h2>
<p style="color:#94A3B8;font-size:14px;margin:0 0 20px">Use this code to complete your registration</p>
<div style="background:#0E1825;border-radius:12px;padding:20px;font-size:36px;font-weight:800;color:#00E5FF;letter-spacing:8px">{code}</div>
<p style="color:#475569;font-size:12px;margin-top:20px">This code expires in 10 minutes</p>
</div></div>''', 'html')
    msg['Subject'] = 'Verify your Scraven account'
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"[email] Failed to send to {to_email}: {e}", flush=True)
        return False

def send_reset_email(to_email, token, host=None):
    if not GMAIL_USER or not GMAIL_APP_PASS:
        print(f"[email] SMTP not configured, skipping reset to {to_email}", flush=True)
        return False
    base = f'http://{host}' if host else 'http://localhost:8800'
    base = base.rstrip('/')
    reset_link = f'{base}/reset-password?token={token}'
    msg = MIMEText(f'''<div style="font-family:Inter,sans-serif;background:#050A14;padding:32px;text-align:center">
<div style="max-width:400px;margin:0 auto;background:rgba(14,24,37,0.95);border-radius:16px;padding:32px;border:1px solid rgba(226,232,240,0.08)">
<div style="width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,#0A4FD9,#00E5FF);display:flex;align-items:center;justify-content:center;font-size:24px;font-weight:800;color:#fff;margin:0 auto 16px">S</div>
<h2 style="color:#F8FAFC;font-size:18px;margin:0 0 8px">Reset your password</h2>
<p style="color:#94A3B8;font-size:14px;margin:0 0 20px">Click the button below to reset your password. This link expires in 1 hour.</p>
<a href="{reset_link}" style="display:inline-block;background:linear-gradient(135deg,#0A4FD9,#00E5FF);color:#fff;text-decoration:none;padding:14px 32px;border-radius:10px;font-size:16px;font-weight:700;margin:8px 0">Reset Password</a>
<p style="color:#475569;font-size:12px;margin-top:20px">If you didn't request this, ignore this email.</p>
</div></div>''', 'html')
    msg['Subject'] = 'Reset your Scraven password'
    msg['From'] = GMAIL_USER
    msg['To'] = to_email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.send_message(msg)
        return True
    except Exception as e:
        print(f"[email] Failed to send reset to {to_email}: {e}", flush=True)
        return False

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'demo'))
from category_lib import classify_category, detect_trojan_horse

import lead_gen_outreach
from smart_hunt import CATEGORY_QUERIES, CATEGORY_ALIASES

CATEGORY_DISPLAY_NAMES = {
    'baby': 'Baby Products',
    'bags': 'Bags & Handbags',
    'bags_luggage': 'Bags & Luggage',
    'bakery': 'Bakery',
    'boutique': 'Boutique',
    'clothing_brand': 'Clothing Brand',
    'cosmetics': 'Cosmetics',
    'cosmetics_store': 'Cosmetics Store',
    'electronics': 'Electronics',
    'fashion': 'Fashion',
    'food': 'Food',
    'food_beverage': 'Food & Beverage',
    'fruit': 'Fruit',
    'furniture_store': 'Furniture',
    'games_toys': 'Games & Toys',
    'health_beauty': 'Health & Beauty',
    'home': 'Home',
    'home_decor': 'Home Decor',
    'jewelry': 'Jewelry',
    'jewelry_watches': 'Jewelry & Watches',
    'kitchen_cooking': 'Kitchen & Cooking',
    'nursery': 'Nursery',
    'outdoor_sporting': 'Outdoor & Sporting',
    'patio_garden': 'Patio & Garden',
    'perfume': 'Perfume',
    'personal_care': 'Personal Care',
    'skincare': 'Skincare',
    'specialty_grocery': 'Specialty Grocery',
}

CSV_PATH = os.path.join(os.path.dirname(__file__), 'collected_leads', 'leads.csv')
LEADS_DIR = os.path.dirname(CSV_PATH)

def user_csv_path(user_id):
    """Per-user CSV for fully-isolated lead storage. Returns a path inside collected_leads/users/<id>/leads.csv"""
    if not user_id:
        return CSV_PATH
    user_dir = os.path.join(LEADS_DIR, 'users', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, 'leads.csv')

QUALIFIED_DIR = os.path.join(os.path.dirname(__file__), 'qualified_leads')
QUALIFIED_CSV_PATH = os.path.join(QUALIFIED_DIR, 'qualified_leads.csv')

CSV_COLUMNS = [
    'date', 'platform', 'business_name', 'page_url', 'category', 'followers',
    'email', 'phone', 'website', 'has_website', 'address', 'last_post_date',
    'qualification_score', 'status', 'notes', 'follow_up_date', 'open_state', 'hours_text',
    'deleted_at', 'saved_by_user_id', 'saved_by_user_name',
]

QUALIFIED_COLUMNS = CSV_COLUMNS + ['qualified_at', 'qualified_by']

VALID_STATUSES = ['new', 'contacted', 'qualified', 'meeting', 'proposal', 'won', 'lost']

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = "-1004334910291"
TELEGRAM_THREAD_ID = 354

DEMO_DIR = os.path.join(os.path.dirname(__file__), 'demo')
MAPS_CSV_PATH = os.path.join(os.path.dirname(__file__), 'collected_leads', 'maps_leads.csv')

# \u2500\u2500 F-Commerce Configuration \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
FCOMMERCE_CSV_PATH = os.path.join(os.path.dirname(__file__), 'collected_leads', 'fcommerce_leads.csv')

LINKEDIN_CSV_PATH = os.path.join(os.path.dirname(__file__), 'collected_leads', 'linkedin_leads.csv')

LINKEDIN_COLUMNS = ['date', 'name', 'headline', 'company', 'location', 'url', 'kb_score', 'kb_category', 'matched_products', 'status', 'source']

FCOMMERCE_COLUMNS = [
    'date', 'source', 'business_name', 'page_url', 'followers_int',
    'has_website', 'order_method', 'last_post_date', 'product_categories',
    'discovery_source', 'qualification_score', 'priority',
    'opportunity_flags', 'email', 'phone', 'address', 'status', 'notes', 'created_at',
]

FCOMMERCE_PRODUCT_CATEGORIES = [
    'Beauty & Cosmetics', 'Skincare', 'Fashion & Boutique', 'Jewelry',
    'Perfume', 'Bags & Accessories', 'Baby Products', 'Home & Kitchen Products',
]

FCOMMERCE_OPPORTUNITY_FLAGS = [
    'No Website', 'Weak Website', 'E-commerce Upgrade',
    'Weak Branding', 'No Google Presence',
]

FCOMMERCE_DISCOVERY_SOURCES = ['Facebook Ads Library', 'Facebook Search']

FCOMMERCE_SALES_PITCH = (
    "PITCH: E-commerce Website | Online Orders 24/7 | Customer Database "
    "Collection | Better Facebook Ad Performance | Higher Trust & Branding | "
    "Delivery Within 1 Business Day | Starting From \u09F310,000"
)

_last_lead_url = None

SOCIAL_DOMAINS = ['tiktok.com', 'instagram.com', 'facebook.com', 'twitter.com', 'x.com', 'linkedin.com', 'youtube.com', 'youtu.be', 'pinterest.com', 'snapchat.com', 'threads.net']

def set_last_lead_url(url):
    global _last_lead_url
    _last_lead_url = url

def get_last_lead_url():
    global _last_lead_url
    return _last_lead_url

def ensure_csv(path=None):
    if path is None: path = CSV_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_COLUMNS)
    else:
        with open(path, 'r', newline='') as f:
            existing_cols = [c.strip() for c in f.readline().strip().split(',')]
        if existing_cols != CSV_COLUMNS:
            rows = []
            with open(path, 'r', newline='') as f:
                next(f)
                for line in f:
                    vals = [v.strip() for v in line.strip().split(',')]
                    row = {}
                    for i, col in enumerate(existing_cols):
                        if i < len(vals):
                            row[col] = vals[i]
                        else:
                            row[col] = ''
                    for col in CSV_COLUMNS:
                        if col not in row:
                            row[col] = ''
                    rows.append(row)
            with open(path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)


def read_csv_rows(path):
    if not os.path.exists(path):
        return []
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def write_csv_rows(path, rows):
    ensure_csv(path)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

def ensure_qualified_csv():
    os.makedirs(QUALIFIED_DIR, exist_ok=True)
    if not os.path.exists(QUALIFIED_CSV_PATH):
        with open(QUALIFIED_CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(QUALIFIED_COLUMNS)

AUTH_DB_PATH = os.path.join(os.path.dirname(__file__), 'auth.db')
AVATAR_DIR = os.path.join(os.path.dirname(__file__), 'avatars')

# \u2500\u2500 Rate limiting \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_login_attempts = {}  # ip -> [attempt_count, first_attempt_time]
LOGIN_RATE_LIMIT = 999     # max attempts (effectively disabled)
LOGIN_RATE_WINDOW = 900    # window in seconds (15 min)

# \u2500\u2500 Session config \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
SESSION_EXPIRY_DAYS = 30

def init_auth_db():
    from db import init_auth_db as _init
    _init()
    try:
        conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.close()
    except Exception:
        pass

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return h, salt

def verify_password(password, hash_val, salt):
    return hash_password(password, salt)[0] == hash_val

def create_session(user_id, conn=None):
    token = secrets.token_hex(32)
    try:
        if conn is None:
            conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
            own_conn = True
        else:
            own_conn = False
        c = conn.cursor()
        c.execute('INSERT INTO sessions (user_id, token, created_at) VALUES (?, ?, ?)',
                  (user_id, token, datetime.now().isoformat()))
        if own_conn:
            conn.commit()
            conn.close()
        print(f"[auth] Session created: user={user_id} token={token[:16]}... path={AUTH_DB_PATH}", flush=True)
    except Exception as e:
        print(f"[auth] Session CREATE failed: {e}", flush=True)
        return None
    return token

def get_user_from_token(token):
    if not token:
        return None
    try:
        conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        print(f"[auth] get_user_from_token: path={AUTH_DB_PATH} exists={os.path.exists(AUTH_DB_PATH)}", flush=True)
        c.execute("SELECT user_id, created_at FROM sessions WHERE token = ?", (token,))
        srow = c.fetchone()
        if srow is None:
            conn.close()
            print(f"[auth] Session NOT FOUND for token={token[:16]}...", flush=True)
            return None
        print(f"[auth] Session FOUND: user_id={srow['user_id']} created_at={srow['created_at']}", flush=True)
        c.execute('''SELECT id, name, email, role, created_at,
                     COALESCE(email_verified, 0) AS email_verified,
                     COALESCE(leads_used, 0) AS leads_used,
                     COALESCE(subscription_tier, 'free') AS subscription_tier
                     FROM users WHERE id = ?''', (srow['user_id'],))
        row = c.fetchone()
        conn.close()
        if row is None:
            print(f"[auth] User NOT FOUND for id={srow['user_id']}", flush=True)
            return None
        r = dict(row)
        print(f"[auth] User FOUND: {r['name']} role={r['role']}", flush=True)
        return {'id': r['id'], 'name': r['name'], 'email': r['email'], 'role': r['role'], 'created_at': r['created_at'],
                'email_verified': bool(r['email_verified']), 'leads_used': r['leads_used'], 'subscription_tier': r['subscription_tier']}
    except Exception as e:
        print(f"[auth] EXCEPTION in session query: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return None

def get_lead_limit(user):
    if not user:
        return 10
    if user.get('role') in ('admin', 'super_admin', 'pro'):
        return 999999
    if user.get('subscription_tier') == 'pro':
        return 999999
    return 20

def can_extract_lead(user):
    if user and user.get('role') in ('admin', 'super_admin', 'pro'):
        return True, 999999
    limit = get_lead_limit(user)
    used = user['leads_used'] if user else 0
    remaining = limit - used
    if remaining <= 0:
        return False, 0
    return True, remaining

def require_auth(self):
    token = None
    auth = self.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
    if not token:
        params = parse_qs(urlparse(self.path).query)
        token = params.get('token', [None])[0]
    user = get_user_from_token(token)
    if not user:
        self._json(401, {'error': 'Unauthorized'})
        return None
    return user

def csv_to_xlsx_bytes(csv_content):
    wb = openpyxl.Workbook()
    ws = wb.active
    center = Alignment(horizontal='center', vertical='center')
    reader = csv.reader(io.StringIO(csv_content))
    for row_idx, row in enumerate(reader, 1):
        for col_idx, val in enumerate(row, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = center
    for col_cells in ws.columns:
        col_letter = col_cells[0].column_letter
        max_len = max((len(str(c.value or '')) for c in col_cells), default=0)
        ws.column_dimensions[col_letter].width = min(max_len + 4, 55)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


DAILY_QUALIFIED_COLUMNS = [
    'date', 'platform', 'business_name', 'page_url', 'category', 'followers',
    'email', 'phone', 'website', 'has_website', 'address', 'last_post_date',
    'qualification_score', 'status', 'notes', 'follow_up_date', 'qualified_at', 'qualified_by',
]

def get_daily_qualified_path():
    today = datetime.now()
    day_name = today.strftime('%A')
    return os.path.join(QUALIFIED_DIR, f"{today.strftime('%Y-%m-%d')}_{day_name}.csv")

def append_to_daily_qualified_csv(lead, qualified_by='extension-flow'):
    path = get_daily_qualified_path()
    os.makedirs(QUALIFIED_DIR, exist_ok=True)

    qrow = {}
    for col in DAILY_QUALIFIED_COLUMNS:
        val = lead.get(col, '')
        qrow[col] = str(val) if val is not None else ''

    qrow['qualified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    qrow['qualified_by'] = qualified_by

    rows = []
    if os.path.exists(path):
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

    rows.append(qrow)

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=DAILY_QUALIFIED_COLUMNS, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)

    date_str = datetime.now().strftime('%Y-%m-%d')
    print(f"  Daily qualified saved: {path} ({len(rows)} leads)", flush=True)

def is_social_website(url):
    if not url: return False
    return any(d in url.lower() for d in SOCIAL_DOMAINS)

def send_telegram_notification(lead, action='saved'):
    token = TELEGRAM_TOKEN
    if not token:
        print("  TELEGRAM_TOKEN not set, skipping notification", flush=True)
        return None

    try:
        score = int(lead.get('qualification_score', 0))
    except (ValueError, TypeError):
        score = 0
    if score >= 8: star = "\u2b50\u2b50\u2b50"
    elif score >= 6: star = "\u2b50\u2b50"
    else: star = "\u2b50"

    if action == 'duplicate':
        action_emoji, action_text = "\u26a0\ufe0f", "Duplicate Lead Skipped"
    elif action == 'status_update':
        action_emoji, action_text = "\U0001F4CC", "Lead Status Updated"
    elif action == 'qualified':
        action_emoji, action_text = "\U0001F525\U0001F525\U0001F525", "HOT LEAD QUALIFIED"
    else:
        action_emoji, action_text = "\U0001F195", "New Lead Saved"

    fb = lead.get('followers', '') or '-'
    lpd = lead.get('last_post_date', '') or '-'
    open_state = lead.get('open_state', '') or ''
    hours_text = lead.get('hours_text', '') or ''
    website = lead.get('website', '') or ''
    has_site_raw = lead.get('has_website', '')
    is_social = is_social_website(website)
    if has_site_raw == 'true' and is_social: has_site = 'Social'
    elif has_site_raw == 'true': has_site = 'Yes'
    else: has_site = 'No'
    addr = lead.get('address', '') or '-'
    notes = lead.get('notes', '') or ''
    fud = lead.get('follow_up_date', '') or ''

    trojan = detect_trojan_horse(lead.get('business_name', ''), lead.get('category', ''))
    trojan_line = ''
    if trojan and action not in ('status_update', 'qualified'):
        trojan_line = f'\n\U0001F3AF Trojan Horse: <b>{trojan["product"]}</b> ({trojan["entry"]})'
    elif trojan and action in ('status_update', 'qualified'):
        if lead.get('status') == 'qualified':
            trojan_line = f'\n\U0001F3AF Trojan Horse: <b>{trojan["product"]}</b> \u2014 pain: {trojan["pain"]}'

    st = lead.get('status', 'new')

    def h(val):
        return html.escape(str(val) if val is not None else '')

    file_info = f'\n\U0001F4C1 File: {CSV_PATH}' if action == 'duplicate' else ''
    qualified_footer = '\n\n\U0001F4C2 Saved to: <b>qualified_leads/qualified_leads.csv</b>\n\U0001F4DE <b>Contact this lead NOW</b>' if action == 'qualified' else ''

    platform_emoji = {'google_maps': '\U0001F5FA\ufe0f', 'facebook': '\U0001F4D8', 'instagram': '\U0001F4F8', 'linkedin': '\U0001F4BC'}.get(lead.get('platform', ''), '\U0001F50D')
    source_line = f'\n{platform_emoji} Source: <b>{h(lead.get("platform", "unknown"))}</b>'
    saved_by = (lead.get('saved_by_user_name') or '').strip()
    _em_dash = '\u2014'
    saved_by_line = f'\n\U0001F464 Saved by: <b>{h(saved_by) or _em_dash}</b>' if saved_by else ''
    _open_hours_prefix = '\U0001F550 '
    _last_post_prefix = '\U0001F4C5 Last Post: '

    message = f"""{action_emoji} <b>{h(action_text)}</b>{source_line}{saved_by_line}
\U0001F3E2 <b>{h(lead.get('business_name', 'Unknown'))}</b>
\U0001F4CA Score: {score}/10 {star} | Status: <b>{h(st)}</b>
\U0001F4C2 Category: {h(lead.get('category', '-'))}
\U0001F465 Followers: {h(fb)}
\U0001F4DE Phone: {h(lead.get('phone', 'Not found'))}
\U0001F4E7 Email: {h(lead.get('email', 'Not found'))}
\U0001F310 Website: {h(has_site)}{f' ({h(website)})' if website else ''}
\U0001F4CD Address: {h(addr)}
{_open_hours_prefix + h(open_state) + (' (' + h(hours_text) + ')' if hours_text else '') if lead.get('platform') == 'google_maps' and open_state else _last_post_prefix + h(lpd)}
\U0001F4DD Notes: {h(notes)}
\U0001F4CC Follow-up: {h(fud if fud else 'Not set')}
\U0001F517 {h(lead.get('page_url', ''))}{trojan_line}{file_info}{qualified_footer}"""

    if action == 'saved':
        message += "\n\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\u26a1 <b>Quick actions</b> \u2192 tell me: <i>qualify</i> / <i>disqualify</i> / <i>demo</i>"

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_thread_id": TELEGRAM_THREAD_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    def _do_send():
        bot_url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            resp = requests.post(bot_url, json=payload, timeout=10)
            result = resp.json()
            if result.get('ok'):
                page_url = lead.get('page_url', '')
                set_last_lead_url(page_url)
                print(f"  Telegram notified: {lead.get('business_name')}", flush=True)
            else:
                print(f"  Telegram API error: {result}", flush=True)
        except Exception as e:
            print(f"  Telegram notification failed: {e}", flush=True)
    threading.Thread(target=_do_send, daemon=True).start()


def append_lead(data, notify_telegram=True, user_id=None):
    page_url = data.get('page_url', '').strip()
    if not page_url:
        return False, 'page_url is required'
    data['_notify_telegram'] = bool(notify_telegram)

    if USE_MONGO:
        result = mongo_db.save_lead(data, user_id)
        if result and isinstance(result, dict) and result.get('duplicate'):
            existing = mongo_db.find_lead_by_url(page_url, user_id)
            if data.get('_notify_telegram', True):
                send_telegram_notification(existing, 'duplicate')
            return False, 'duplicate'
        if result:
            row = mongo_db.serialize(result)
            row['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if data.get('_notify_telegram', True):
                send_telegram_notification(row, 'saved')
            return True, 'Lead saved'
        return False, 'Failed to save lead'

    target_path = user_csv_path(user_id)

    rows = []
    found_idx = -1
    rows = read_csv_rows(target_path)
    for i, row in enumerate(rows):
        for col in CSV_COLUMNS:
            if col not in row:
                row[col] = ''
        if row.get('page_url', '').strip() == page_url:
            found_idx = i
            break

    if found_idx >= 0:
        existing = rows[found_idx]
        print(f"DUPLICATE: {existing.get('business_name') or 'Unknown'} | {page_url}", flush=True)
        if data.get('_notify_telegram', True):
            send_telegram_notification(existing, 'duplicate')
        return False, 'duplicate'

    row = {col: '' for col in CSV_COLUMNS}
    row['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if not row.get('platform'):
        row['platform'] = 'facebook'
    row['status'] = 'new'
    for key in CSV_COLUMNS:
        if key in data and data[key] not in (None, ''):
            row[key] = str(data[key])

    row['category'] = classify_category(row.get('category', ''))

    rows.append(row)
    msg = 'Lead saved'
    notify = data.get('_notify_telegram', True)
    user_name = (data.get('_saved_by_name') or '').strip()
    saved_by_id = data.get('_saved_by_id', 0)
    by = f" by {user_name}#{saved_by_id}" if user_name else ""
    print(f"LEAD SAVED{by}: {row['business_name'] or 'Unknown'} | Score: {row['qualification_score'] or 'N/A'} | {page_url} | telegram={notify}", flush=True)
    if notify:
        send_telegram_notification(row, 'saved')
    append_to_daily_qualified_csv(row, qualified_by='extension-flow')

    write_csv_rows(target_path, rows)

    return True, msg


def delete_lead(page_url, user_id=None):
    """Hard delete (legacy). Prefer trash_lead()."""
    if USE_MONGO:
        ok = mongo_db.bulk_purge([page_url], user_id)
        if ok:
            print(f"LEAD DELETED: {page_url}", flush=True)
        return ok, 'Lead deleted' if ok else 'Lead not found'
    target_path = user_csv_path(user_id) if user_id else CSV_PATH
    rows = read_csv_rows(target_path)
    found = False
    new_rows = []
    for row in rows:
        for col in CSV_COLUMNS:
            if col not in row: row[col] = ''
        if row.get('page_url', '').strip() == page_url:
            found = True
        else:
            new_rows.append(row)
    if not found:
        return False, 'Lead not found'
    write_csv_rows(target_path, new_rows)
    print(f"LEAD DELETED: {page_url} (file={target_path})", flush=True)
    return True, 'Lead deleted'


def _mutate_lead(page_url, mutator, user_id=None):
    target_path = user_csv_path(user_id) if user_id else CSV_PATH
    if not os.path.exists(target_path):
        return False, 'No leads file found'
    rows = read_csv_rows(target_path)
    for row in rows:
        for col in CSV_COLUMNS:
            if col not in row: row[col] = ''
    found = False
    for row in rows:
        if row.get('page_url', '').strip() == page_url:
            mutator(row)
            found = True
            break
    if not found:
        return False, 'Lead not found'
    write_csv_rows(target_path, rows)
    return True, 'ok'


def trash_lead(page_url, user_id=None):
    def _set(r):
        r['deleted_at'] = datetime.now().isoformat()
        r['status'] = 'trashed'
    return _mutate_lead(page_url, _set, user_id=user_id)


def restore_lead(page_url, user_id=None):
    if USE_MONGO:
        ok = mongo_db.restore_lead(page_url, user_id)
        return (ok, 'restored') if ok else (False, 'Lead not found')
    def _set(r):
        r['deleted_at'] = ''
        if r.get('status', '').strip().lower() == 'trashed':
            r['status'] = 'new'
    return _mutate_lead(page_url, _set, user_id=user_id)


def purge_lead(page_url, user_id=None):
    if USE_MONGO:
        ok = mongo_db.purge_lead(page_url, user_id)
        return (ok, 'purged') if ok else (False, 'Lead not found')
    target_path = user_csv_path(user_id) if user_id else CSV_PATH
    rows = read_csv_rows(target_path)
    new_rows = []
    found = False
    for row in rows:
        for col in CSV_COLUMNS:
            if col not in row: row[col] = ''
        if row.get('page_url', '').strip() == page_url:
            found = True
            continue
        new_rows.append(row)
    if not found:
        return False, 'Lead not found'
    write_csv_rows(target_path, new_rows)
    return True, 'purged'


def read_trashed_leads(user_id=None, include_all_users=False):
    """Read trashed leads. By default returns the current user's trash.
    Admins with include_all_users=True get trash across all users."""
    if USE_MONGO:
        is_admin = bool(include_all_users)
        rows = mongo_db.list_trashed_leads(user_id, is_admin=is_admin)
        return [mongo_db.serialize(r) for r in rows]
    if user_id and not include_all_users:
        rows = read_csv_rows(user_csv_path(user_id))
        rows = [r for r in rows if (r.get('deleted_at') or '').strip() and _is_valid_lead(r)]
        rows.sort(key=lambda r: r.get('deleted_at', ''), reverse=True)
        return rows
    all_rows = []
    if os.path.exists(CSV_PATH):
        for r in read_csv_rows(CSV_PATH):
            if (r.get('deleted_at') or '').strip() and _is_valid_lead(r):
                all_rows.append(r)
    users_dir = os.path.join(LEADS_DIR, 'users')
    if os.path.isdir(users_dir):
        for uid in os.listdir(users_dir):
            user_dir = os.path.join(users_dir, uid)
            if not os.path.isdir(user_dir): continue
            p = os.path.join(user_dir, 'leads.csv')
            if not os.path.exists(p): continue
            for r in read_csv_rows(p):
                if (r.get('deleted_at') or '').strip() and _is_valid_lead(r):
                    all_rows.append(r)
    all_rows.sort(key=lambda r: r.get('deleted_at', ''), reverse=True)
    return all_rows


def append_qualified_lead(lead):
    if USE_MONGO:
        mongo_db.save_qualified_lead(lead, lead.get('_saved_by_id', 0))
        mongo_db.save_daily_qualified(lead, lead.get('_saved_by_id', 0))
        print(f"QUALIFIED: {lead.get('business_name')} -> MongoDB", flush=True)
        return
    ensure_qualified_csv()
    qrows = []
    if os.path.exists(QUALIFIED_CSV_PATH):
        with open(QUALIFIED_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            qrows = [r for r in reader]

    qrow = {col: lead.get(col, '') for col in CSV_COLUMNS}
    for col in ['qualified_at', 'qualified_by']:
        qrow[col] = ''
    qrow['qualified_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    qrow['qualified_by'] = 'telegram-bot'

    qrows.append(qrow)
    with open(QUALIFIED_CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=QUALIFIED_COLUMNS)
        writer.writeheader()
        writer.writerows(qrows)

    append_to_daily_qualified_csv(qrow, qualified_by='telegram-bot')

    print(f"QUALIFIED: {lead.get('business_name')} -> {QUALIFIED_CSV_PATH}", flush=True)


def update_lead_status(page_url, new_status, follow_up_date=None, user_id=None):
    if new_status not in VALID_STATUSES:
        return False, f"Invalid status. Valid: {', '.join(VALID_STATUSES)}"

    if USE_MONGO:
        ok = mongo_db.update_lead_status(page_url, user_id, new_status, follow_up_date)
        if not ok:
            return False, 'Lead not found'
        if new_status == 'qualified':
            lead = mongo_db.find_lead_by_url(page_url, user_id)
            if lead:
                mongo_db.save_qualified_lead(mongo_db.serialize(lead), user_id)
                mongo_db.save_daily_qualified(mongo_db.serialize(lead), user_id)
                send_telegram_notification(mongo_db.serialize(lead), 'qualified')
        else:
            lead = mongo_db.find_lead_by_url(page_url, user_id, include_trashed=True)
            if lead:
                send_telegram_notification(mongo_db.serialize(lead), 'status_update')
        return True, f"Status updated to {new_status}"

    target_path = user_csv_path(user_id) if user_id else CSV_PATH
    rows = read_csv_rows(target_path)
    for row in rows:
        for col in CSV_COLUMNS:
            if col not in row: row[col] = ''
    found = False
    for row in rows:
        if row.get('page_url', '').strip() == page_url:
            row['status'] = new_status
            if follow_up_date:
                row['follow_up_date'] = follow_up_date
            found = True
            break

    if not found:
        return False, 'Lead not found'

    write_csv_rows(target_path, rows)

    for r in rows:
        if r.get('page_url', '').strip() == page_url:
            if new_status == 'qualified':
                append_qualified_lead(r)
                send_telegram_notification(r, 'qualified')
            else:
                send_telegram_notification(r, 'status_update')
            return True, f"Status updated to {new_status}"
    return False, 'Error updating lead'


def get_funnel_stats(user_id=None, include_all_users=False):
    if USE_MONGO:
        is_admin = bool(include_all_users)
        return mongo_db.funnel_stats(user_id, is_admin=is_admin)
    leads = read_all_leads(user_id=user_id, include_all_users=include_all_users)
    stats = {s: 0 for s in VALID_STATUSES}
    for row in leads:
        if (row.get('deleted_at') or '').strip(): continue
        st = row.get('status', 'new').strip().lower()
        if st in stats:
            stats[st] += 1
        else:
            stats['new'] = stats.get('new', 0) + 1
    return stats


def get_qualified_leads():
    if USE_MONGO:
        return [mongo_db.serialize(r) for r in mongo_db.list_qualified_leads()]
    if not os.path.exists(QUALIFIED_CSV_PATH):
        return []
    with open(QUALIFIED_CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def read_all_leads(filter_status=None, include_trashed=False, user_id=None, include_all_users=False):
    """Read leads.
    - user_id given \u2192 only that user's CSV.
    - include_all_users=True (admin) \u2192 merged view across all per-user CSVs AND global CSV.
    - neither \u2192 fall back to global CSV (legacy).
    """
    if USE_MONGO:
        is_admin = bool(include_all_users)
        rows = mongo_db.list_leads(
            user_id=user_id,
            is_admin=is_admin,
            status=filter_status,
            include_trashed=bool(include_trashed),
        )
        return [mongo_db.serialize(r) for r in rows]

    paths = []
    if user_id:
        paths = [user_csv_path(user_id)]
    elif include_all_users:
        paths = [CSV_PATH]
        users_dir = os.path.join(LEADS_DIR, 'users')
        if os.path.isdir(users_dir):
            for uid in os.listdir(users_dir):
                user_dir = os.path.join(users_dir, uid)
                if not os.path.isdir(user_dir): continue
                p = os.path.join(user_dir, 'leads.csv')
                if os.path.exists(p): paths.append(p)
    else:
        paths = [CSV_PATH]

    leads = []
    seen_urls = set() if include_all_users else None
    for p in paths:
        for row in read_csv_rows(p):
            if not _is_valid_lead(row):
                continue
            if include_all_users:
                url = row.get('page_url', '').strip()
                if url in seen_urls: continue
                seen_urls.add(url)
            if not include_trashed:
                if (row.get('deleted_at') or '').strip(): continue
            elif include_trashed == 'only':
                if not (row.get('deleted_at') or '').strip(): continue
            leads.append(row)
    if filter_status:
        leads = [l for l in leads if l.get('status', '').strip().lower() == filter_status.lower()]
    return leads


def _is_valid_lead(row):
    url = (row.get('page_url') or '').strip()
    name = (row.get('business_name') or '').strip()
    if not url:
        return False
    if not name:
        return False
    if not (url.startswith('http://') or url.startswith('https://') or url.startswith('www.')):
        return False
    return True


def h(val):
    return html.escape(str(val) if val is not None else '')


def _find_lead_by_url(page_url, user_id=None):
    """Find a lead by URL. user_id given \u2192 only that user's CSV. None \u2192 all CSVs (admin)."""
    if USE_MONGO:
        is_admin = user_id is None
        lead = mongo_db.find_lead_by_url(page_url, user_id, is_admin=is_admin)
        if lead:
            return mongo_db.serialize(lead)
        return None
    paths = []
    if user_id is not None:
        paths = [user_csv_path(user_id)]
    else:
        paths = [CSV_PATH]
        users_dir = os.path.join(LEADS_DIR, 'users')
        if os.path.isdir(users_dir):
            for uid in os.listdir(users_dir):
                user_dir = os.path.join(users_dir, uid)
                if not os.path.isdir(user_dir): continue
                p = os.path.join(user_dir, 'leads.csv')
                if os.path.exists(p): paths.append(p)
    for p in paths:
        for row in read_csv_rows(p):
            if row.get('page_url', '').strip() == page_url:
                return row
    if os.path.exists(MAPS_CSV_PATH):
        with open(MAPS_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('page_url', '').strip() == page_url:
                    return row
    return None


def _generate_and_send_demo(chat_id, thread_id, lead_info, name, phone, category, address, reply_to=None):
    token = TELEGRAM_TOKEN
    if not token:
        return
    api = f"https://api.telegram.org/bot{token}"
    slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')
    out_path = f"/tmp/demo_{slug}.html"
    pdf_path = f"/tmp/demo_{slug}.pdf"
    json_path = f"/tmp/demo_{slug}.json"
    cmd = [
        sys.executable,
        os.path.join(DEMO_DIR, 'generate_demo.py'),
        '--name', name,
        '--phone', phone or 'N/A',
        '--category', category or 'general',
        '--address', address or '',
        '--out', out_path,
        '--pdf',
        '--json',
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
    except subprocess.CalledProcessError as e:
        requests.post(f"{api}/sendMessage", json={"chat_id": chat_id, "message_thread_id": thread_id, "text": f"\u274c Demo failed:\n<code>{h(e.stderr)}</code>", "parse_mode": "HTML"}, timeout=10)
        return
    except Exception as e:
        requests.post(f"{api}/sendMessage", json={"chat_id": chat_id, "message_thread_id": thread_id, "text": f"\u274c Error: {h(str(e))}", "parse_mode": "HTML"}, timeout=10)
        return
    if not os.path.exists(out_path):
        requests.post(f"{api}/sendMessage", json={"chat_id": chat_id, "message_thread_id": thread_id, "text": "\u274c Demo file not created.", "parse_mode": "HTML"}, timeout=10)
        return

    # Read JSON metadata for enriched caption
    caption_html = (
        f"\u2705 <b>Demo Ready: {h(name)}</b>\n"
        f"\U0001F517 Open HTML in browser or share PDF with client"
    )

    # Send HTML file
    html_sent = False
    try:
        with open(out_path, 'rb') as f:
            doc_data = {"chat_id": chat_id, "caption": caption_html, "parse_mode": "HTML"}
            if thread_id:
                doc_data["message_thread_id"] = thread_id
            if reply_to:
                doc_data["reply_to_message_id"] = reply_to
            resp = requests.post(f"{api}/sendDocument", data=doc_data, files={"document": (f"demo_{slug}.html", f)}, timeout=30)
        html_sent = resp.json().get('ok', False)
    except Exception:
        pass

    # Send PDF file
    pdf_sent = False
    if os.path.exists(pdf_path):
        try:
            with open(pdf_path, 'rb') as f:
                doc_data = {"chat_id": chat_id, "caption": "\U0001F4C4 <b>PDF version</b> \u2014 ready to share with client", "parse_mode": "HTML"}
                if thread_id:
                    doc_data["message_thread_id"] = thread_id
                if reply_to:
                    doc_data["reply_to_message_id"] = reply_to
                resp = requests.post(f"{api}/sendDocument", data=doc_data, files={"document": (f"demo_{slug}.pdf", f)}, timeout=30)
            pdf_sent = resp.json().get('ok', False)
        except Exception:
            pass

    if not html_sent and not pdf_sent:
        requests.post(f"{api}/sendMessage", json={"chat_id": chat_id, "message_thread_id": thread_id, "text": f"\u26a0\ufe0f Files at:\n<code>{out_path}</code>\n<code>{pdf_path}</code>", "parse_mode": "HTML"}, timeout=10)


def _find_lead_by_name(name, user_id=None):
    """Find a lead by business_name. user_id given \u2192 only that user's CSV. None \u2192 all CSVs (admin)."""
    name_lower = name.strip().lower()
    if USE_MONGO:
        from db import get_db
        is_admin = user_id is None
        if is_admin:
            q = {'business_name': {'$regex': f'^{name.strip()}$', '$options': 'i'}, 'deleted_at': None}
        else:
            q = {'business_name': {'$regex': f'^{name.strip()}$', '$options': 'i'}, 'saved_by_user_id': to_object_id(user_id), 'deleted_at': None}
        lead = mongo_db.get_db().leads.find_one(q) if mongo_db else None
        return mongo_db.serialize(lead) if lead else None
    paths = []
    if user_id is not None:
        paths = [user_csv_path(user_id)]
    else:
        paths = [CSV_PATH]
        users_dir = os.path.join(LEADS_DIR, 'users')
        if os.path.isdir(users_dir):
            for uid in os.listdir(users_dir):
                user_dir = os.path.join(users_dir, uid)
                if not os.path.isdir(user_dir): continue
                p = os.path.join(user_dir, 'leads.csv')
                if os.path.exists(p): paths.append(p)
    for p in paths:
        for row in read_csv_rows(p):
            bn = (row.get('business_name', '') or '').strip().lower()
            if name_lower == bn or bn.startswith(name_lower) or name_lower in bn:
                return row
    return None


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
#  F-COMMERCE LEAD HUNTER
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550


def _ensure_fcommerce_csv():
    os.makedirs(os.path.dirname(FCOMMERCE_CSV_PATH), exist_ok=True)
    if not os.path.exists(FCOMMERCE_CSV_PATH):
        with open(FCOMMERCE_CSV_PATH, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(FCOMMERCE_COLUMNS)


def _fcommerce_is_recent_7days(date_str):
    if not date_str:
        return False
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return (datetime.now() - dt).days <= 7
    except ValueError:
        pass
    t = str(date_str).lower()
    if 'just now' in t or 'minute' in t or 'hour' in t:
        return True
    if 'day' in t:
        m = re.search(r'(\d+)', t)
        return m and int(m.group(1)) <= 7
    if 'today' in t or 'yesterday' in t:
        return True
    return False


def _score_fcommerce_lead(lead):
    s = 0
    hw = str(lead.get('has_website', '')).strip().lower()
    if hw == 'no':
        s += 4
    elif hw == 'weak':
        s += 2
    try:
        f = int(str(lead.get('followers_int', '0') or '0'))
    except (ValueError, TypeError):
        f = 0
    if f >= 50000:
        s += 3
    elif f >= 20000:
        s += 2
    if _fcommerce_is_recent_7days(lead.get('last_post_date', '')):
        s += 2
    om = str(lead.get('order_method', '')).strip()
    if om in ('Inbox', 'WhatsApp', 'Both'):
        s += 1
    return min(s, 10)


def _fcommerce_auto_flags(lead):
    flags = []
    hw = str(lead.get('has_website', '')).strip().lower()
    if hw == 'no':
        flags.append('No Website')
    elif hw == 'weak':
        flags.append('Weak Website')
    if hw in ('weak', 'no'):
        flags.append('E-commerce Upgrade')
    return '|'.join(flags) if flags else ''


def _send_fcommerce_telegram(lead):
    token = TELEGRAM_TOKEN
    if not token:
        return
    api = f"https://api.telegram.org/bot{token}"

    def hh(val):
        return html.escape(str(val) if val is not None else '')

    score = int(lead.get('qualification_score', 0))
    priority = lead.get('priority', '')
    star = "\U0001F525\U0001F525\U0001F525" if priority == 'HIGH' else ("\U0001F525\U0001F525" if priority == 'MEDIUM' else "\u2b50")
    priority_box = (
        "\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
        f"<b>\U0001F525 HIGH PRIORITY \u2014 CONTACT NOW</b>\n"
        f"<code>{FCOMMERCE_SALES_PITCH}</code>\n"
        "\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
    ) if priority == 'HIGH' else ''

    message = f"""\U0001F6D2 <b>F-Commerce Lead</b>
\U0001F3E2 <b>{hh(lead.get('business_name', 'Unknown'))}</b>
\U0001F4CA Score: {score}/10 {star} | Priority: <b>{hh(priority)}</b>
\U0001F4C2 Product: {hh(lead.get('product_categories', '-'))}
\U0001F465 Followers: {hh(lead.get('followers_int', '-'))}
\U0001F310 Has Website: {hh(lead.get('has_website', '-'))}
\U0001F4E6 Order Method: {hh(lead.get('order_method', '-'))}
\U0001F50D Source: {hh(lead.get('discovery_source', '-'))}
\U0001F4CD Address: {hh(lead.get('address', '-'))}
\U0001F4DE Phone: {hh(lead.get('phone', 'Not found'))}
\U0001F4E7 Email: {hh(lead.get('email', 'Not found'))}
\U0001F3F7\ufe0f Opportunities: {hh(lead.get('opportunity_flags', '-'))}
\U0001F4DD Notes: {hh(lead.get('notes', ''))}
\U0001F517 {hh(lead.get('page_url', ''))}{priority_box}"""

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "message_thread_id": TELEGRAM_THREAD_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(f"{api}/sendMessage", json=payload, timeout=10)
        if resp.json().get('ok'):
            set_last_lead_url(lead.get('page_url', ''))
            print(f"  F-Commerce Telegram notified: {lead.get('business_name')}", flush=True)
            return resp.json()['result'].get('message_id')
    except Exception as e:
        print(f"  F-Commerce Telegram failed: {e}", flush=True)
    return None


def _save_fcommerce_lead(data):
    page_url = str(data.get('page_url', '')).strip()
    if not page_url:
        return False, 'page_url is required', {}

    _ensure_fcommerce_csv()
    rows = []
    found = False
    if os.path.exists(FCOMMERCE_CSV_PATH):
        with open(FCOMMERCE_CSV_PATH, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for col in FCOMMERCE_COLUMNS:
                    if col not in row:
                        row[col] = ''
                if row.get('page_url', '').strip() == page_url:
                    found = True
                rows.append(row)

    if found:
        return False, 'duplicate', {}

    lead = {col: '' for col in FCOMMERCE_COLUMNS}
    lead['date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lead['source'] = 'fcommerce'
    lead['status'] = 'new'
    lead['created_at'] = datetime.now().isoformat()

    for key in FCOMMERCE_COLUMNS:
        if key in data and data[key] not in (None, ''):
            lead[key] = str(data[key])

    score = _score_fcommerce_lead(lead)
    lead['qualification_score'] = str(score)

    if score >= 9:
        lead['priority'] = 'HIGH'
    elif score >= 6:
        lead['priority'] = 'MEDIUM'
    else:
        return False, f'score_too_low ({score}/10 \u2014 below threshold)', lead

    if not lead.get('opportunity_flags', '').strip():
        lead['opportunity_flags'] = _fcommerce_auto_flags(lead)

    rows.append(lead)

    with open(FCOMMERCE_CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FCOMMERCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"F-COMMERCE SAVED: {lead['business_name']} | Score: {score}/10 | Priority: {lead['priority']}", flush=True)
    _send_fcommerce_telegram(lead)
    return True, f'saved (score={score}, priority={lead["priority"]})', lead


def _read_fcommerce_leads(filters=None):
    if not os.path.exists(FCOMMERCE_CSV_PATH):
        return []
    with open(FCOMMERCE_CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        leads = [row for row in reader]

    if not filters:
        # Append sales pitch to HIGH priority leads in output
        for lead in leads:
            if lead.get('priority') == 'HIGH':
                existing = lead.get('notes', '') or ''
                if 'PITCH:' not in existing:
                    lead['notes'] = (existing + '\n' + FCOMMERCE_SALES_PITCH).strip()
        return leads

    filtered = []
    for lead in leads:
        match = True
        if 'priority' in filters and filters['priority']:
            if lead.get('priority', '').strip().upper() != filters['priority'].strip().upper():
                match = False
        if 'source' in filters and filters['source']:
            if lead.get('discovery_source', '').strip().lower() != filters['source'].strip().lower():
                match = False
        if 'category' in filters and filters['category']:
            cats = (lead.get('product_categories', '') or '').lower()
            if filters['category'].strip().lower() not in cats:
                match = False
        if match:
            if lead.get('priority') == 'HIGH':
                existing = lead.get('notes', '') or ''
                if 'PITCH:' not in existing:
                    lead['notes'] = (existing + '\n' + FCOMMERCE_SALES_PITCH).strip()
            filtered.append(lead)
    return filtered


def _delete_fcommerce_lead(page_url):
    if not os.path.exists(FCOMMERCE_CSV_PATH):
        return False, 'No F-Commerce leads found'
    rows = []
    found = False
    with open(FCOMMERCE_CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col in FCOMMERCE_COLUMNS:
                if col not in row:
                    row[col] = ''
            if row.get('page_url', '').strip() == page_url:
                found = True
            else:
                rows.append(row)
    if not found:
        return False, 'F-Commerce lead not found'
    with open(FCOMMERCE_CSV_PATH, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FCOMMERCE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return True, 'deleted'


def _fcommerce_stats():
    stats = {
        'total': 0,
        'by_priority': {'HIGH': 0, 'MEDIUM': 0},
        'by_source': {},
        'by_product_category': {},
    }
    if not os.path.exists(FCOMMERCE_CSV_PATH):
        return stats
    with open(FCOMMERCE_CSV_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for lead in reader:
            stats['total'] += 1
            p = lead.get('priority', '')
            if p in stats['by_priority']:
                stats['by_priority'][p] += 1
            ds = lead.get('discovery_source', '') or 'Unknown'
            stats['by_source'][ds] = stats['by_source'].get(ds, 0) + 1
            for cat in (lead.get('product_categories', '') or '').split('|'):
                cat = cat.strip()
                if cat:
                    stats['by_product_category'][cat] = stats['by_product_category'].get(cat, 0) + 1
    return stats


# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

_PLAYWRIGHT_BROWSER = None


def _get_browser():
    global _PLAYWRIGHT_BROWSER
    if _PLAYWRIGHT_BROWSER is None:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        _PLAYWRIGHT_BROWSER = p.chromium.launch(headless=True)
    return _PLAYWRIGHT_BROWSER


_FB_COOKIES_CACHE = None


def _load_fb_cookies():
    """Load FB cookies from fb_cookies.json if present. Returns Playwright-format cookie list or None."""
    global _FB_COOKIES_CACHE
    if _FB_COOKIES_CACHE is not None:
        return _FB_COOKIES_CACHE
    cookies_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fb_cookies.json')
    if not os.path.exists(cookies_path):
        _FB_COOKIES_CACHE = False
        return None
    try:
        with open(cookies_path, 'r') as f:
            raw = json.load(f)
        out = []
        for c in raw:
            pc = {
                'name': c.get('name'),
                'value': c.get('value', ''),
                'domain': c.get('domain', '.facebook.com'),
                'path': c.get('path', '/'),
            }
            exp = c.get('expirationDate')
            if exp:
                pc['expires'] = exp
            if c.get('httpOnly'):
                pc['httpOnly'] = True
            if c.get('secure'):
                pc['secure'] = True
            ss = (c.get('sameSite') or '').lower()
            if ss == 'lax':
                pc['sameSite'] = 'Lax'
            elif ss == 'no_restriction':
                pc['sameSite'] = 'None'
            elif ss == 'strict':
                pc['sameSite'] = 'Strict'
            out.append(pc)
        _FB_COOKIES_CACHE = out
        print(f"[cookies] loaded {len(out)} FB cookies", flush=True)
        return out
    except Exception as e:
        print(f"[cookies] load failed: {e}", flush=True)
        _FB_COOKIES_CACHE = False
        return None


def _apply_fb_cookies(ctx):
    """Apply loaded FB cookies to a Playwright context (best-effort)."""
    cookies = _load_fb_cookies()
    if not cookies:
        return
    try:
        ctx.add_cookies(cookies)
    except Exception as e:
        print(f"[cookies] add failed: {e}", flush=True)




# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550
# Apify Facebook Pages Scraper \u2014 primary extractor (uses FB-internal access)
# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

APIFY_API_KEY = os.environ.get('APIFY_API_KEY', '')
APIFY_ACTOR_ID = 'apify~facebook-pages-scraper'
APIFY_BASE = 'https://api.apify.com/v2'


def _extract_via_apify(fb_url, timeout=300):
    """Call Apify Facebook Pages Scraper. Returns dict matching _extract_facebook_page shape or None on failure."""
    if not APIFY_API_KEY:
        print('[apify] APIFY_API_KEY not set \u2014 skipping', flush=True)
        return None
    try:
        headers = {'Authorization': f'Bearer {APIFY_API_KEY}', 'Content-Type': 'application/json'}
        # Normalize URL to canonical FB page form
        norm = fb_url.replace('m.facebook.com', 'www.facebook.com').rstrip('/').split('?')[0].split('#')[0]
        # Start the run
        payload = {'startUrls': [{'url': norm}], 'maxPagesPerQuery': 1}
        resp = requests.post(f'{APIFY_BASE}/acts/{APIFY_ACTOR_ID}/runs', headers=headers, json=payload, timeout=60)
        data = resp.json()
        run_id = data.get('data', {}).get('id')
        if not run_id:
            print(f'[apify] start failed: {data.get("error", {})}', flush=True)
            return None
        # Poll for completion
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}', headers=headers, timeout=60)
            status = r.json().get('data', {}).get('status', 'UNKNOWN')
            if status == 'SUCCEEDED':
                break
            if status in ('FAILED', 'TIMED-OUT', 'ABORTED'):
                print(f'[apify] run ended: {status}', flush=True)
                return None
            time.sleep(3)
        else:
            print('[apify] timeout', flush=True)
            return None
        # Get results
        r = requests.get(f'{APIFY_BASE}/actor-runs/{run_id}/dataset/items', headers=headers, timeout=60)
        items = r.json()
        if not items:
            return None
        item = items[0]
        # Map Apify fields to our shape
        name = (item.get('title') or item.get('name') or '').strip()
        # Strip "Verified account" suffix and trailing whitespace
        name = re.sub(r'\s*[\u00a0\s]Verified\s*(?:account|page)?\s*$', '', name, flags=re.I).strip()
        # Strip trailing "| City" pipe-suffix (e.g. "Diamond World DNM | Dhaka" \u2014 keep the brand part)
        # Actually keep it as-is; user might want the location info too
        phone = (item.get('phone') or '').strip()
        email = (item.get('email') or '').strip()
        website = (item.get('website') or '').strip()
        address = (item.get('address') or '').strip()
        categories = item.get('categories') or []
        category = categories[0] if categories else (item.get('category') or '').strip()
        followers = item.get('likes') or item.get('followers') or ''
        page_url = item.get('pageUrl') or item.get('facebookUrl') or norm
        # Normalize phone to +880XXXXXXXXX format (strip spaces, dashes, parens)
        if phone:
            p_clean = re.sub(r'[\s\-\(\)\.]', '', phone)
            if re.match(r'^01[3-9]\d{8}$', p_clean):
                phone = '+880' + p_clean[1:]
            elif re.match(r'^\+?8801[3-9]\d{8}$', p_clean):
                phone = '+' + p_clean.lstrip('+')
            elif re.match(r'^\+880[1-9]\d{8,9}$', p_clean):
                phone = p_clean
        # Normalize email to lowercase
        if email: email = email.lower().strip()
        # Clean up category \u2014 skip generic "Page" if there's a more specific one
        if category and category.lower().strip() == 'page' and categories and len(categories) > 1:
            for c in categories:
                if c and c.lower().strip() != 'page':
                    category = c
                    break
        return {
            'url': page_url or fb_url,
            'business_name': name,
            'category': category,
            'followers': str(followers) if followers else '',
            'email': email,
            'phone': phone,
            'website': website,
            'has_website': bool(website),
            'address': address,
            'last_post_date': '',
            'qualification_score': 5,
        }
    except Exception as e:
        print(f'[apify] error: {e}', flush=True)
        return None



def _extract_fb_json_data(html):
    """Parse Facebook page HTML for JSON-embedded business data (phone, email, website, address).
    Only uses narrow, targeted patterns \u2014 avoids broad key searches that pick up random data."""
    out = {}
    # Normalize escaped JSON slashes for matching
    norm_html = html.replace('\\/', '/').replace('\\u0040', '@')
    # Phone: scan for any WhatsApp send URL (api.whatsapp.com/send?phone=NUMBER) \u2014 FB embeds real business phone here
    for wa in re.finditer(r'api\.whatsapp\.com/send\?phone=(\d+)', norm_html):
        num = wa.group(1)
        if num.startswith('880') and len(num) >= 13:
            n = '+' + num
            # Validate BD mobile
            stripped = num.lstrip('880')
            if re.match(r'^1[3-9]\d{8}$', stripped):
                out['phone'] = n
                break
    # Phone that appears in the same JSON block as the email \u2014 likely the real business phone
    if not out.get('phone') and out.get('email'):
        # Email in HTML might use \u0040 instead of @ \u2014 try both forms
        em_pos = norm_html.find('"' + out['email'] + '"')
        if em_pos < 0:
            esc_email = out['email'].replace('@', '\\u0040')
            em_pos = norm_html.find('"' + esc_email + '"')
        if em_pos > 0:
            window = norm_html[max(0, em_pos - 3000):em_pos + 3000]
            clean = re.sub(r'[\s\-\(\)\.]', '', window)
            for m in re.finditer(r'(?:01[3-9]\d{8}|\+?8801[3-9]\d{8})', clean):
                n = m.group(0)
                if n.startswith('01') and len(n) == 11: n = '+880' + n[1:]
                elif n.startswith('880') and not n.startswith('+'): n = '+' + n
                if re.match(r'^\+?8801[3-9]\d{8}$', n):
                    out['phone'] = n
                    break
    # REMOVED frequency-based phone fallback \u2014 was returning wrong phones from FB internal data
    # REMOVED raw-HTML phone scan \u2014 was picking random 11-digit sequences from FB's internal SVG/CSS data
    # Look for email in JSON context (reliable \u2014 email addresses are specific enough to avoid false positives)
    em = re.search(r'"(?:email|email_address|contact_email)"\s*:\s*"([^"]+@[^"]+\.[a-zA-Z]{2,})"', norm_html)
    if em:
        e = em.group(1).replace('\\/', '/').lower()
        if not any(x in e for x in ['facebook', 'fb.com', 'sentry', 'example', 'noreply']):
            out['email'] = e
    if not out.get('email'):
        em2 = re.findall(r'"([a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"', norm_html)
        for e in em2:
            el = e.lower()
            if not any(x in el for x in ['facebook', 'fb.com', 'sentry', 'example', 'noreply']):
                out['email'] = el
                break
    # Look for website in JSON context (specific keys)
    site_excl = ['facebook.com', 'fb.com', 'instagram.com', 'instagram', 'fbcdn', 'maps.google.com', 'google.com/maps', 'youtube.com', 'twitter.com', 'x.com', 'w3.org', 'schema.org', 'dms.net', 'messenger.com', 'm.me', 'mng.com', 'doubleclick.net', 'googleadservices.com', 'googlesyndication.com', 'msn.com', 'live.com', 'bing.com']
    # Hard media/news blocklist \u2014 these are NEVER valid business websites
    media_block = ['msn.com', 'yahoo.com', 'cnn.com', 'bbc.com', 'bbc.co.uk', 'nytimes.com', 'washingtonpost.com', 'foxnews.com', 'nbcnews.com', 'cbsnews.com', 'abcnews.go.com', 'reuters.com', 'apnews.com', 'theguardian.com', 'huffpost.com', 'buzzfeed.com', 'dailymail.co.uk', 'nypost.com', 'usatoday.com', 'forbes.com', 'businessinsider.com', 'techcrunch.com', 'theverge.com', 'engadget.com', 'wired.com', 'mashable.com', 'cnet.com', 'zdnet.com', 'news.google.com', 'news.yahoo.com', 'apple.com', 'microsoft.com', 'google.com', 'support.google', 'policies.google', 'play.google.com', 'developers.facebook', 'about.meta']
    # First try keys that always have protocol \u2014 narrow keys only (link/url are too noisy)
    ws = re.findall(r'"(?:website|website_url|external_url|site_url|vanity_url|display_url)"\s*:\s*"(https?://[^"]+)"', norm_html)
    for u in ws:
        u = u.replace('\\/', '/').lower()
        if not any(e in u for e in site_excl) and not any(m in u for m in media_block) and len(u) < 100:
            out['website'] = u
            break
    # Try page_url separately \u2014 only accept if it looks like the page's own domain (not news/media)
    if not out.get('website'):
        page_urls = re.findall(r'"page_url"\s*:\s*"(https?://[^"]+)"', norm_html)
        for u in page_urls:
            u = u.replace('\\/', '/').lower()
            if not any(e in u for e in site_excl) and not any(m in u for m in media_block) and len(u) < 100:
                if not any(noise in u for noise in ['/article/', '/news/', '/story/', '/post/', '/blog/', '/video/', '/watch/', '/wiki/']):
                    out['website'] = u
                    break
    # Try protocol-less website values (drop page_url from this list \u2014 too noisy)
    if not out.get('website'):
        ws2 = re.findall(r'"(?:website|website_url|external_url|site_url|vanity_url|display_url)"\s*:\s*"((?:[a-zA-Z0-9\-]+\.)+(?:com|bd|net|org|shop|store|app)(?:/[^"]*)?)"', norm_html)
        for u in ws2:
            u = u.replace('\\/', '/').lower()
            if not any(e in u for e in site_excl) and not any(m in u for m in media_block) and len(u) < 80:
                out['website'] = 'https://' + u
                break

    # Look for address in JSON context
    addr = re.search(r'"(?:address|location|street_address|full_address|display_address)"\s*:\s*"([^"]{10,200})"', norm_html)
    if addr:
        a = addr.group(1).replace('\\/', '/').replace('\\n', ', ').replace('\\u00e0', '\u00e0')
        out['address'] = a
    # Look for category in JSON context
    cat = re.search(r'"(?:category|page_category|category_name)"\s*:\s*"([^"]{2,80})"', norm_html)
    if cat: out['category'] = cat.group(1)
    return out


def _extract_facebook_page(fb_url):
    result = {
        'url': fb_url,
        'business_name': '', 'category': '', 'followers': '',
        'email': '', 'phone': '', 'website': '', 'has_website': False,
        'address': '', 'last_post_date': '', 'qualification_score': 5,
    }
    browser = _get_browser()
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en_US',
    )
    _apply_fb_cookies(ctx)
    page = ctx.new_page()
    try:
        page.goto(fb_url, timeout=20000, wait_until='domcontentloaded')

        # Try to wait for actual page content (not the "browser not supported" wall)
        try:
            page.wait_for_selector('[data-pagelet], time, abbr, [role="main"]', timeout=8000)
        except Exception:
            pass  # Page didn't render useful content; we'll try anyway

        # Extract JSON-LD structured data first (often has full info without login)
        try:
            ld_raw = page.evaluate('''() => {
              var out = {};
              var scripts = document.querySelectorAll('script[type="application/ld+json"]');
              for (var si = 0; si < scripts.length; si++) {
                try {
                  var d = JSON.parse(scripts[si].textContent);
                  if (d.name && !out.name) out.name = d.name;
                  if (d.description && !out.description) out.description = d.description;
                  if (d.telephone && !out.telephone) out.telephone = d.telephone;
                  if (d.email && !out.email) out.email = d.email;
                  if (d.url && !out.url) out.url = d.url;
                  if (d.address) {
                    var a = d.address;
                    if (typeof a === 'object') {
                      var parts = [];
                      if (a.streetAddress) parts.push(a.streetAddress);
                      if (a.addressLocality) parts.push(a.addressLocality);
                      if (a.addressRegion) parts.push(a.addressRegion);
                      if (a.postalCode) parts.push(a.postalCode);
                      if (a.addressCountry) parts.push(a.addressCountry);
                      if (parts.length) out.address = parts.join(', ');
                    }
                  }
                  if (d.sameAs && Array.isArray(d.sameAs)) {
                    for (var si2 = 0; si2 < d.sameAs.length; si2++) {
                      var u = d.sameAs[si2];
                      if (/^(https?:\\/\\/)?(?!.*facebook)/i.test(u) && !out.website) out.website = u;
                    }
                  }
                } catch(e) {}
              }
              return JSON.stringify(out);
            }''')
            ld_data = json.loads(ld_raw)
            if ld_data.get('name'): result['business_name'] = ld_data['name']
            if ld_data.get('telephone'): result['phone'] = ld_data['telephone']
            if ld_data.get('email'): result['email'] = ld_data['email']
            if ld_data.get('website'): result['website'] = ld_data['website']; result['has_website'] = True
            if ld_data.get('address'): result['address'] = ld_data['address']
        except Exception:
            pass  # JSON-LD extraction is best-effort

        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(2000)
        page.evaluate('window.scrollTo(0, Math.ceil(document.body.scrollHeight/2))')
        page.wait_for_timeout(1500)
        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        page.wait_for_timeout(1500)
        page.evaluate('window.scrollTo(0, 0)')
        page.wait_for_timeout(1500)

        extract_js = '''
        (function() {
          var d = {url: window.location.href.split('?')[0].replace(/\\/+$/, '')};
          var body = document.body ? document.body.innerText || '' : '';
          // fullText = textContent with script/style contents stripped (for FB pages that hide content)
          var ftEl = document.createElement('div');
          ftEl.appendChild(document.body.cloneNode(true));
          var ftScripts = ftEl.querySelectorAll('script,style,svg');
          for (var fi = 0; fi < ftScripts.length; fi++) ftScripts[fi].remove();
          var fullText = ftEl.textContent || '';

          var h = document.querySelector('[data-pagelet="ProfileHeader"],[data-pagelet="CommercialProfile"],header');
          if (h) { var el = h.querySelector('h1,h2,strong'); if (el) d.business_name = el.innerText.trim(); }
          if (!d.business_name) { var og = document.querySelector('meta[property="og:title"]'); if (og) d.business_name = (og.getAttribute('content') || '').trim(); }
          if (!d.business_name) { var h1 = document.querySelector('h1'); if (h1) { var ht = h1.innerText.replace(/\u00a0/g, ' ').replace(/\s+Verified\s*(?:account|page)?\s*$/i, '').replace(/\s+/g, ' ').trim(); if (ht && ht.length > 1) d.business_name = ht; } }
          if (!d.business_name) { var t = document.title.replace(/ \\| Facebook/, '').replace(/ - Facebook/, '').trim(); if (t && !/^search/i.test(t)) d.business_name = t; }

          var cats = ['Beauty Salon','Boutique','Clothing','Store','Shop','Restaurant','Cafe','Bakery','Jewelry','Skincare','Cosmetics','Fashion','Grocery','Pharmacy','Clinic','Fitness','Gym','Salon','Spa','Tailor','Studio'];
          for (var i = 0; i < cats.length; i++) { if (new RegExp('\\\\b' + cats[i] + '\\\\b', 'i').test(body)) { d.category = cats[i]; break; } }
          if (!d.category) { var des = document.querySelector('meta[property="og:description"],meta[name="description"]'); if (des) { var dc = des.getAttribute('content') || ''; for (var i = 0; i < cats.length; i++) { if (new RegExp('\\\\b' + cats[i] + '\\\\b', 'i').test(dc)) { d.category = cats[i]; break; } } } }
          if (!d.category) { for (var ci = 0; ci < cats.length; ci++) { if (new RegExp('\\\\b' + cats[ci] + '\\\\b', 'i').test(fullText)) { d.category = cats[ci]; break; } } }

          var fm = body.match(/([\\d,.]+[KkMmBb]?)\\s*(followers|likes|people follow|\u099c\u09a8 \u09ab\u09b2\u09cb\u09af\u09bc\u09be\u09b0|follower)/i);
          if (!fm) fm = body.match(/([\\d,.]+[KkMmBb]?)\\s*followers?\\s*[\\u2022\\/\\|\\-]\\s*(?:\\d+\\s*)?following/i);
          if (!fm) fm = body.match(/([\\d,.]+[KkMmBb]?)\\s*(?:\\w+\\s+)?(?:followers?|likes?)/i);
          if (!fm) { var fl = body.match(/(\\d[\\d,]*)\\s*(?:people|person)\\s+(?:follow|like)/i); if (fl) fm = fl; }
          // Fallback: extract followers from og:description (e.g. "Pearl Kingdom, Dhaka. 266,936 likes ...")
          if (!fm) { var ogd = (document.querySelector('meta[property="og:description"],meta[name="description"]') || {}).content || ''; var ofm = ogd.match(/([\\d,.]+[KkMmBb]?)\\s*(likes|followers)/i); if (ofm) fm = ofm; }
          // Fallback: extract followers from fullText (textContent with script/style stripped)
          if (!fm) { var ftm = fullText.match(/([\\d,.]+[KkMmBb]?)\\s*(followers|likes|people follow|\u099c\u09a8 \u09ab\u09b2\u09cb\u09af\u09bc\u09be\u09b0|follower)/i); if (ftm) fm = ftm; }
          if (!fm) { var ftm = fullText.match(/([\\d,.]+[KkMmBb]?)\\s*followers?\\s*[\\u2022\\/\\|\\-]\\s*(?:\\d+\\s*)?following/i); if (ftm) fm = ftm; }
          if (!fm) { var ftm = fullText.match(/([\\d,.]+[KkMmBb]?)\\s*(?:\\w+\\s+)?(?:followers?|likes?)/i); if (ftm) fm = ftm; }
          if (fm) d.followers = fm[1];

          // \u2500\u2500 Email (extension approach: mailto: + contact sections + JSON scripts) \u2500\u2500
          var emailExcl = ['facebook.com', 'fb.com', 'sentry.io', 'example.com', '.png', '.jpg', '.svg', '.gif', 'w3.org', 'schema.org', 'google.com', 'googleapis.com', 'play.google', 'support.google', 'policies.google', 'developers.facebook', 'about.meta'];
          var emailRe = /[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}/g;
          var emailResults = [];
          var emailSeen = {};
          function addEmail(e) {
            var k = e.toLowerCase().trim();
            if (k && !emailSeen[k] && !emailExcl.some(function(x) { return k.indexOf(x) > -1; })) {
              emailSeen[k] = true; emailResults.push(k);
            }
          }
          // mailto: links
          var mailLinks = document.querySelectorAll('a[href^="mailto:"]');
          for (var mi = 0; mi < mailLinks.length; mi++) {
            var raw = mailLinks[mi].getAttribute('href').replace('mailto:', '').split('?')[0].trim();
            if (raw) addEmail(raw);
          }
          // Contact sections (expanded selectors)
          var contactSels = document.querySelectorAll('[data-pagelet="ProfileCards"],[data-pagelet="PageHeader"],[data-pagelet="ProfileSection"],[role="main"],[aria-label*="about" i],[aria-label*="contact" i]');
          for (var ci = 0; ci < contactSels.length; ci++) {
            var ct = contactSels[ci].textContent || '';
            var m = ct.match(emailRe) || [];
            for (var cj = 0; cj < m.length; cj++) addEmail(m[cj]);
          }
          // JSON scripts (full document)
          var jsonScripts = document.querySelectorAll('script[type="application/json"]');
          for (var si = 0; si < jsonScripts.length; si++) {
            var raw = jsonScripts[si].textContent || '';
            var m = raw.match(emailRe) || [];
            for (var sj = 0; sj < m.length; sj++) addEmail(m[sj]);
          }
          // Page innerHTML (broader JSON search) \u2014 strips script tags first
          if (emailResults.length === 0) {
            try {
              var allScripts = document.querySelectorAll('script');
              for (var sk = 0; sk < allScripts.length; sk++) {
                var skText = allScripts[sk].textContent || '';
                var skM = skText.match(emailRe) || [];
                for (var skj = 0; skj < skM.length; skj++) addEmail(skM[skj]);
              }
            } catch(e) {}
          }
          // meta description fallback
          if (emailResults.length === 0) {
            var metaDescs = document.querySelectorAll('meta[property="og:description"],meta[name="description"]');
            for (var mi = 0; mi < metaDescs.length; mi++) {
              var mc = metaDescs[mi].getAttribute('content') || '';
              var mem = mc.match(emailRe) || [];
              for (var mj = 0; mj < mem.length; mj++) addEmail(mem[mj]);
            }
          }
          // Visible page text fallback (last resort)
          if (emailResults.length === 0) {
            try {
              var m = fullText.match(emailRe) || [];
              for (var fi = 0; fi < m.length; fi++) addEmail(m[fi]);
            } catch(e) {}
          }
          if (emailResults.length > 0) d.email = emailResults[0];

          // \u2500\u2500 Phone (extension approach: tel: + contact sections + validation) \u2500\u2500
          function looksReal(s) {
            if (/^0{2,}/.test(s)) return false;
            if (/^(\\d)\\1+$/.test(s)) return false;
            if (s.length >= 8 && s.length % 3 === 0) {
              var part = s.slice(0, 3);
              if (part.repeat(s.length / 3) === s) return false;
            }
            if (s.length >= 8 && s.length % 2 === 0) {
              var part = s.slice(0, 2);
              if (part.repeat(s.length / 2) === s) return false;
            }
            return true;
          }
          var phoneResults = [];
          var phoneSeen = {};
          function addPhone(p) {
            var n = p.replace(/[\\s\\-\\(\\)\\.]/g, '');
            if (!n) return;
            if (n.indexOf('01') === 0 && n.length === 11) n = '+880' + n.slice(1);
            else if (n.indexOf('880') === 0 && n.length === 13) n = '+' + n;
            if (phoneSeen[n]) return;
            var np = n.replace(/^\\+/, '');
            if (np.length < 10) return;
            if (/^8801[3-9]\\d{8}$/.test(np) && looksReal(np.slice(3))) {
              phoneSeen[n] = true; phoneResults.push(n);
            }
          }
          // tel: links
          var telLinks = document.querySelectorAll('a[href^="tel:"]');
          for (var ti = 0; ti < telLinks.length; ti++) {
            var raw = telLinks[ti].getAttribute('href').replace('tel:', '').split(/[;,#]/)[0].trim();
            if (raw) addPhone(raw);
          }
          // Contact sections
          var contactSels2 = document.querySelectorAll('[data-pagelet="ProfileCards"],[data-pagelet="PageHeader"],[role="main"],[aria-label*="about" i]');
          for (var ci = 0; ci < contactSels2.length; ci++) {
            var ct = contactSels2[ci].textContent || '';
            var clean = ct.replace(/[\\s\\-\\(\\)\\.]/g, '');
            var m = clean.match(/(?:01[3-9]\\d{8}|\\+?8801[3-9]\\d{8})/g) || [];
            for (var cj = 0; cj < m.length; cj++) addPhone(m[cj]);
          }
          // fullText fallback
          if (phoneResults.length === 0) {
            var cleanFt = fullText.replace(/[\\s\\-\\(\\)\\.]/g, '');
            var m = cleanFt.match(/(?:01[3-9]\\d{8}|\\+?8801[3-9]\\d{8})/g) || [];
            for (var fi = 0; fi < m.length; fi++) {
              var n = m[fi];
              if (n.indexOf('01') === 0 && n.length === 11) n = '+880' + n.slice(1);
              var np = n.replace(/^\\+/, '');
              if (/^8801[3-9]\\d{8}$/.test(np) && looksReal(np.slice(3))) {
                if (!phoneSeen[n]) { phoneSeen[n] = true; phoneResults.push(n); }
                break;  // only first valid from fullText
              }
            }
          }
          if (phoneResults.length > 0) d.phone = phoneResults.join(', ');

          // \u2500\u2500 Website (extension approach: all links + JSON scripts + redirects) \u2500\u2500
           var siteExcl = ['facebook.com','fb.com','fbcdn','instagram','twitter','youtube','whatsapp','wa.me','messenger','google','gmail','maps.google.com','google.com/maps','dms.net','m.me','mng.com','doubleclick.net','googlesyndication.com','googleadservices.com','msn.com','live.com','bing.com','yahoo.com','cnn.com','bbc.com','nypost.com','apple.com','microsoft.com','support.google','policies.google','play.google.com','developers.facebook','about.meta','news.'];
          function isExcluded(url) {
            try {
              var u = new URL(url);
              return siteExcl.some(function(e) { return u.hostname.indexOf(e) > -1; });
            } catch(e) { return true; }
          }
          // All links (ProfileCards links first)
          var profileCards = document.querySelectorAll('[data-pagelet="ProfileCards"] a[href]');
          for (var pi = 0; pi < profileCards.length; pi++) {
            var hf = profileCards[pi].href;
            if (hf && hf.indexOf('http') === 0 && !isExcluded(hf)) {
              try { var u = new URL(hf); d.website = u.origin + u.pathname; d.has_website = true; } catch(e) {}
              if (d.website) break;
            }
          }
          // All links fallback \u2014 restrict to ProfileCards/about links only (avoid grabbing random post links)
          if (!d.website) {
            var scopedLinks = document.querySelectorAll('[data-pagelet="ProfileCards"] a[href], [data-pagelet="PageHeader"] a[href], [aria-label*="website" i] a[href], [aria-label*="Website" i]');
            for (var li = 0; li < scopedLinks.length; li++) {
              var hf = scopedLinks[li].href || '';
              if (hf && hf.indexOf('http') === 0 && !isExcluded(hf)) {
                try { var u = new URL(hf); d.website = u.origin + u.pathname; d.has_website = true; break; } catch(e) {}
              }
            }
          }
          // Facebook redirect links (l.php?u=)
          if (!d.website) {
            var fbLinks = document.querySelectorAll('a[href*="l.facebook.com/l.php?u="]');
            for (var li = 0; li < fbLinks.length; li++) {
              var m = fbLinks[li].href.match(/[?&]u=([^&]+)/);
              if (m) { try { var u = decodeURIComponent(m[1]); var p = new URL(u); if (!isExcluded(p.href)) { d.website = p.origin + p.pathname; d.has_website = true; break; } } catch(e) {} }
            }
          }
          // JSON script fallback
          if (!d.website) {
            var jsonScripts = document.querySelectorAll('script[type="application/json"]');
            for (var si = 0; si < jsonScripts.length; si++) {
              var raw = jsonScripts[si].textContent || '';
              var m = raw.match(/"website"\\s*:\\s*"([^"]+)"/);
              if (m && m[1].indexOf('http') === 0 && !isExcluded(m[1])) { d.website = m[1]; d.has_website = true; break; }
            }
          }
          // REMOVED fullText regex fallback for website \u2014 too noisy (grabbed random URLs like ncl.com, sky.com, msn.com from page body)

          // \u2500\u2500 Address (extension approach: Google Maps links + structured patterns) \u2500\u2500
          // Normalize: split text by separators so we never match across "Location A \u00b7 Location B"
          function splitSegments(s) {
            return (s || '').split(/[\u00b7\u2022|;]/).map(function(x) { return x.trim(); }).filter(function(x) { return x.length > 2; });
          }
          var bodySegs = splitSegments(body);
          var ftSegs = splitSegments(fullText);
          var ogdEl = document.querySelector('meta[property="og:description"],meta[name="description"]');
          var ogd = ogdEl ? (ogdEl.getAttribute('content') || '') : '';
          var ogdSegs = splitSegments(ogd);
          // Google Maps links
          var mapLinks = document.querySelectorAll('a[href*="maps.google.com"], a[href*="maps.app.goo.gl"], a[href*="google.com/maps"]');
          for (var mi = 0; mi < mapLinks.length; mi++) {
            var parent = mapLinks[mi].closest('div,[role="main"]') || mapLinks[mi].parentElement;
            if (!parent) continue;
            var parentText = (parent.textContent || '');
            for (var pi = 0; pi < splitSegments(parentText).length; pi++) {
              var seg = splitSegments(parentText)[pi];
              if (/(Road|House|Floor|Level|Lane|Street|Block|Sector|Building|Village)/i.test(seg) && seg.length < 200) {
                d.address = seg;
                break;
              }
            }
            if (d.address) break;
          }
          // Structured address pattern fallback \u2014 run on segments, never on joined text
          if (!d.address) {
            var addrPatterns = [
              /(?:Road|House|Floor|Level|Lane|Street|Block|Sector|Building|Village|Thana|Upazila).{3,120}?(?:Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal)/i,
              /(?:Gulshan|Banani|Mirpur|Uttara|Dhanmondi|Mohammadpur|Motijheel|Khilgaon|Badda|Bashundhara|Farmgate|Shyamoli|Lalmatia|Malibagh|Rampura|Wari|Jatrabari).{3,80}?(?:Dhaka|Chattogram|Chittagong|Sylhet)/i,
              /(?:Panthapath|Kakrail|Shahbag|Kawran Bazar|Elephant Road|New Market|Azimpur|Green Road|Nikunja|Baridhara|Bonosree|Aftab Nagar).{3,60}?(?:Dhaka|Chattogram)/i,
            ];
            function scanSegs(segs, patterns) {
              for (var si2 = 0; si2 < segs.length; si2++) {
                var seg = segs[si2];
                for (var ai = 0; ai < patterns.length; ai++) {
                  var m = seg.match(patterns[ai]);
                  if (m) return m[0].trim();
                }
              }
              return null;
            }
            d.address = scanSegs(bodySegs, addrPatterns) || scanSegs(ftSegs, addrPatterns) || scanSegs(ogdSegs, addrPatterns);
          }
          if (!d.address) {
            var cityRe = /\\b(Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal|Rangpur|Mymensingh|Comilla|Narayanganj|Gazipur)\\b/i;
            for (var si3 = 0; si3 < bodySegs.length && !d.address; si3++) { var m = bodySegs[si3].match(cityRe); if (m) d.address = m[0].trim(); }
            if (!d.address) for (var si4 = 0; si4 < ftSegs.length && !d.address; si4++) { var m2 = ftSegs[si4].match(cityRe); if (m2) d.address = m2[0].trim(); }
            if (!d.address) for (var si5 = 0; si5 < ogdSegs.length && !d.address; si5++) { var m3 = ogdSegs[si5].match(cityRe); if (m3) d.address = m3[0].trim(); }
          }

          // Strategy 1: <time datetime="..."> elements (Facebook uses these \u2014 convert ISO to "X ago")
          if (!d.last_post_date) {
            var timeEls = document.querySelectorAll('time');
            for (var ti = 0; ti < timeEls.length; ti++) {
              var iso = timeEls[ti].getAttribute('datetime') || '';
              if (iso && /\\d{4}/.test(iso)) {
                var dt = new Date(iso);
                var now = new Date();
                var diffMs = now - dt;
                if (!isNaN(dt.getTime()) && diffMs > 0 && diffMs < 730 * 24 * 3600 * 1000) {
                  var diffMin = Math.floor(diffMs / 60000);
                  var diffHr = Math.floor(diffMin / 60);
                  var diffDay = Math.floor(diffHr / 24);
                  var diffWk = Math.floor(diffDay / 7);
                  var diffMo = Math.floor(diffDay / 30);
                  var diffYr = Math.floor(diffDay / 365);
                  function ago(n, unit) { return n + ' ' + unit + (n === 1 ? '' : 's') + ' ago'; }
                  if (diffYr >= 1) d.last_post_date = ago(diffYr, 'year');
                  else if (diffMo >= 1) d.last_post_date = ago(diffMo, 'month');
                  else if (diffWk >= 1) d.last_post_date = ago(diffWk, 'week');
                  else if (diffDay >= 1) d.last_post_date = ago(diffDay, 'day');
                  else if (diffHr >= 1) d.last_post_date = ago(diffHr, 'hour');
                  else if (diffMin >= 1) d.last_post_date = ago(diffMin, 'minute');
                  else d.last_post_date = 'Just now';
                  break;
                }
                // ISO unparseable or too old \u2014 fall through to visible text strategy
                var visible = (timeEls[ti].textContent || '').trim();
                if (visible && /\\d/.test(visible)) { d.last_post_date = visible; break; }
              }
            }
          }
          // Strategy 1b: data-utime / data-time attributes (FB embeds post timestamps here)
          if (!d.last_post_date) {
            var utimeEls = document.querySelectorAll('[data-utime], [data-time], a[href*="/posts/"], a[href*="/permalink/"]');
            var bestPost = null;
            for (var ui = 0; ui < utimeEls.length; ui++) {
              var u = utimeEls[ui].getAttribute('data-utime') || utimeEls[ui].getAttribute('data-time') || '';
              if (u && /^\\d{10,13}$/.test(u)) {
                var ts = parseInt(u.length === 10 ? u + '000' : u);
                var dt2 = new Date(ts);
                if (!isNaN(dt2.getTime())) {
                  var diffMs2 = Date.now() - dt2.getTime();
                  if (diffMs2 > 0 && diffMs2 < 730 * 24 * 3600 * 1000) {
                    if (!bestPost || ts > bestPost) bestPost = ts;
                  }
                }
              }
            }
            if (bestPost) {
              var dt3 = new Date(bestPost);
              var diffMin2 = Math.floor((Date.now() - dt3.getTime()) / 60000);
              var diffHr2 = Math.floor(diffMin2 / 60);
              var diffDay2 = Math.floor(diffHr2 / 24);
              var diffWk2 = Math.floor(diffDay2 / 7);
              var diffMo2 = Math.floor(diffDay2 / 30);
              function ago2(n, unit) { return n + ' ' + unit + (n === 1 ? '' : 's') + ' ago'; }
              if (diffDay2 >= 30) d.last_post_date = ago2(Math.floor(diffDay2/30), 'month');
              else if (diffWk2 >= 1) d.last_post_date = ago2(diffWk2, 'week');
              else if (diffDay2 >= 1) d.last_post_date = ago2(diffDay2, 'day');
              else if (diffHr2 >= 1) d.last_post_date = ago2(diffHr2, 'hour');
              else if (diffMin2 >= 1) d.last_post_date = ago2(diffMin2, 'minute');
              else d.last_post_date = 'Just now';
            }
          }
          // Strategy 2: <abbr> elements with aria-label/title containing "X ago"
          if (!d.last_post_date) {
            var abbrs = document.querySelectorAll('abbr');
            for (var i = 0; i < abbrs.length; i++) {
              var t = abbrs[i].getAttribute('aria-label') || abbrs[i].getAttribute('title') || abbrs[i].textContent || '';
              if (t && !/notification/i.test(t)) { if (/\\b(?:about\\s+)?(?:\\d+|an?)\\s+(hours?|minutes?|days?|weeks?|months?|years?)\\s+ago\\b|^just now$/i.test(t)) { d.last_post_date = t; break; } }
            }
          }
          // Strategy 3: full "X hours/days ago" form in body text
          if (!d.last_post_date) {
            var tm = body.match(/\\b(?:about\\s+)?(?:\\d+|an?)\\s+(hours?|minutes?|days?|weeks?|months?|years?)\\s+ago\\b|^just now$/gi);
            if (!tm) tm = fullText.match(/\\b(?:about\\s+)?(?:\\d+|an?)\\s+(hours?|minutes?|days?|weeks?|months?|years?)\\s+ago\\b|^just now$/gi);
            if (tm) d.last_post_date = tm[0];
          }
          // Strategy 4: Facebook's abbreviated forms "2h", "3d", "1w", "2mo", "Just now", "Yesterday"
          if (!d.last_post_date) {
            var abbrRe = body.match(/\\b(?:just now|yesterday)\\b|\\b(\\d+)\\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|w|wk|wks|week|weeks|mo|mos|month|months|y|yr|yrs|year|years)\\b/gi);
            if (abbrRe && abbrRe.length) d.last_post_date = abbrRe[0];
          }
          // Strategy 5: Bengali relative-time phrases (e.g. "\u09e8 \u0998\u09a3\u09cd\u099f\u09be \u0986\u0997\u09c7", "\u09e9 \u09a6\u09bf\u09a8 \u0986\u0997\u09c7")
          if (!d.last_post_date) {
            var bnRe = body.match(/\\d+\\s*(\u09b8\u09c7\u0995\u09c7\u09a8\u09cd\u09a1|\u09ae\u09bf\u09a8\u09bf\u099f|\u0998\u09a3\u09cd\u099f\u09be|\u09a6\u09bf\u09a8|\u09b8\u09aa\u09cd\u09a4\u09be\u09b9|\u09ae\u09be\u09b8|\u09ac\u099b\u09b0)\\s*(\u0986\u0997\u09c7|\u09aa\u09c2\u09b0\u09cd\u09ac\u09c7)/);
            if (!bnRe) bnRe = fullText.match(/\\d+\\s*(\u09b8\u09c7\u0995\u09c7\u09a8\u09cd\u09a1|\u09ae\u09bf\u09a8\u09bf\u099f|\u0998\u09a3\u09cd\u099f\u09be|\u09a6\u09bf\u09a8|\u09b8\u09aa\u09cd\u09a4\u09be\u09b9|\u09ae\u09be\u09b8|\u09ac\u099b\u09b0)\\s*(\u0986\u0997\u09c7|\u09aa\u09c2\u09b0\u09cd\u09ac\u09c7)/);
            if (bnRe) d.last_post_date = bnRe[0];
          }
          // Normalize abbreviated forms to readable "X hours/days ago" form
          if (d.last_post_date) {
            var norm = d.last_post_date.trim().toLowerCase();
            var map = { 'just now': 'Just now', 'yesterday': 'Yesterday' };
            if (map[norm]) { d.last_post_date = map[norm]; }
            else {
              var m = norm.match(/^(\\d+)\\s*([a-z]+)/);
              if (m) {
                var n = parseInt(m[1]);
                var unit = m[2];
                var unitMap = {
                  's': 'second', 'sec': 'second', 'secs': 'second', 'second': 'second', 'seconds': 'second',
                  'm': 'minute', 'min': 'minute', 'mins': 'minute', 'minute': 'minute', 'minutes': 'minute',
                  'h': 'hour', 'hr': 'hour', 'hrs': 'hour', 'hour': 'hour', 'hours': 'hour',
                  'd': 'day', 'day': 'day', 'days': 'day',
                  'w': 'week', 'wk': 'week', 'wks': 'week', 'week': 'week', 'weeks': 'week',
                  'mo': 'month', 'mos': 'month', 'month': 'month', 'months': 'month',
                  'y': 'year', 'yr': 'year', 'yrs': 'year', 'year': 'year', 'years': 'year'
                };
                var fullUnit = unitMap[unit] || unit;
                var plural = (n === 1) ? fullUnit : (fullUnit + 's');
                d.last_post_date = n + ' ' + plural + ' ago';
              }
            }
          }

          return JSON.stringify(d);
        })();
        '''
        raw = page.evaluate(extract_js)
        data = json.loads(raw)
        result.update(data)
        result['url'] = fb_url.rstrip('/')

        # Extract from raw HTML source (Facebook embeds business data in script JSON)
        try:
            html_src = page.content()
            fb_data = _extract_fb_json_data(html_src)
            if not result.get('phone') and fb_data.get('phone'):
                p = re.sub(r'[\s\-\(\)\.]', '', fb_data['phone'])
                if p.startswith('01') and len(p) == 11: p = '+880' + p[1:]
                elif p.startswith('1') and len(p) == 10: p = '+880' + p
                elif p.startswith('880') and not p.startswith('+'): p = '+' + p
                if re.match(r'^\+?8801[3-9]\d{8}$', p): result['phone'] = p
            if not result.get('email') and fb_data.get('email'):
                if re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', fb_data['email']):
                    result['email'] = fb_data['email']
            if not result.get('website') and fb_data.get('website'):
                result['website'] = fb_data['website']
                result['has_website'] = True
            if not result.get('address') and fb_data.get('address'):
                result['address'] = fb_data['address']
            if not result.get('category') and fb_data.get('category'):
                result['category'] = fb_data['category']
        except Exception:
            pass  # HTML extraction is best-effort

        # Visit /directory_contact_info FIRST \u2014 FB embeds WhatsApp phone link here (most reliable source)
        if not result.get('phone') or not result.get('email'):
            contact_info_url = fb_url.rstrip('/') + '/directory_contact_info'
            try:
                page.goto(contact_info_url, timeout=10000, wait_until='domcontentloaded')
                page.wait_for_timeout(3000)
                html_ci = page.content()
                fb_ci = _extract_fb_json_data(html_ci)
                if not result.get('phone') and fb_ci.get('phone'):
                    p = re.sub(r'[\s\-\(\)\.]', '', fb_ci['phone'])
                    if p.startswith('01') and len(p) == 11: p = '+880' + p[1:]
                    elif p.startswith('880') and not p.startswith('+'): p = '+' + p
                    if re.match(r'^\+?8801[3-9]\d{8}$', p): result['phone'] = p
                if not result.get('email') and fb_ci.get('email'):
                    if re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', fb_ci['email']):
                        result['email'] = fb_ci['email']
                # Phone: prefer WhatsApp link from contact_info; fallback to phone scan of that page only
                if not result.get('phone') and fb_ci.get('phone'):
                    p = re.sub(r'[\s\-\(\)\.]', '', fb_ci['phone'])
                    if p.startswith('01') and len(p) == 11: p = '+880' + p[1:]
                    elif p.startswith('880') and not p.startswith('+'): p = '+' + p
                    if re.match(r'^\+?8801[3-9]\d{8}$', p): result['phone'] = p
            except Exception:
                pass  # Contact info may not exist \u2014 best-effort
        # Visit About page for contact info (works for public pages)
        if not result.get('email') or not result.get('phone') or not result.get('address') or not result.get('website'):
            about_url = fb_url.rstrip('/') + '/about'
            try:
                page.goto(about_url, timeout=10000, wait_until='domcontentloaded')
                page.wait_for_timeout(2000)
                # Click "Contact info" tab if present \u2014 many pages hide phone/email behind this
                try:
                    clicked = page.evaluate('''() => {
                        for (const el of document.querySelectorAll('span, a, div, [role="tab"]')) {
                            const txt = (el.innerText || '').trim();
                            if (/^Contact\s*info$/i.test(txt) && txt.length < 30 && el.offsetParent !== null) {
                                try { el.click(); return true; } catch(e) {}
                            }
                        }
                        return false;
                    }''')
                    if clicked:
                        page.wait_for_timeout(2000)
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        page.wait_for_timeout(800)
                except Exception:
                    pass
                about_js = '''() => {
                  var d = {};
                  var body = (document.body ? document.body.textContent : document.documentElement.textContent) || '';
                  var em = body.match(/[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}/g);
                  if (em) { for (var i = 0; i < em.length; i++) { if (!/(facebook|fb\\.com|sentry|example)/i.test(em[i])) { d.email = em[i]; break; } } }
                  // Phone from VISIBLE elements only (avoid FB internal JSON noise)
                  try {
                    var visEls = document.querySelectorAll('div, span, a, p, td, li');
                    for (var vi = 0; vi < visEls.length; vi++) {
                      var el = visEls[vi];
                      if (el.offsetParent === null) continue;
                      var txt = (el.innerText || '').trim();
                      var clean = txt.replace(/[\\s\\-\\(\\)\\.]/g, '');
                      var pm = clean.match(/(?:01[3-9]\\d{8}|\\+?8801[3-9]\\d{8})/);
                      if (pm) { d.phone = pm[0]; break; }
                    }
                    // Also try tel: links
                    if (!d.phone) {
                      var tels = document.querySelectorAll('a[href^="tel:"]');
                      if (tels.length) d.phone = tels[0].href.replace('tel:', '').split(/[;,#]/)[0].trim();
                    }
                  } catch(e) {}
                  if (!d.email) {
                    var metaDescs = document.querySelectorAll('meta[property="og:description"],meta[name="description"]');
                    for (var mi = 0; mi < metaDescs.length; mi++) {
                      var mc = metaDescs[mi].getAttribute('content') || '';
                      var mem = mc.match(/[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}/g);
                      if (mem) { for (var mj = 0; mj < mem.length; mj++) { if (!/(facebook|fb\\.com|sentry|example)/i.test(mem[mj])) { d.email = mem[mj]; break; } } }
                      if (d.email) break;
                    }
                  }

           var exc = ['facebook','fb.com','fbcdn','instagram','twitter','youtube','whatsapp','wa.me','messenger','google','gmail','maps.google.com','google.com/maps','dms.net','m.me','mng.com','doubleclick.net','googlesyndication.com','googleadservices.com','msn.com','live.com','bing.com','yahoo.com','cnn.com','bbc.com','nypost.com','apple.com','microsoft.com','support.google','policies.google','play.google.com','developers.facebook','about.meta','news.','sky.com','sky.','skynews','nytimes.com','washingtonpost.com','foxnews.com','reuters.com','apnews.com','theguardian.com','huffpost.com','buzzfeed.com','dailymail.co.uk','usatoday.com','forbes.com','businessinsider.com','techcrunch.com','theverge.com','engadget.com','wired.com','mashable.com','cnet.com','zdnet.com','news.yahoo.com','akamaihd.net','cloudfront.net','amazonaws.com','googleusercontent.com','fbcdn.net','fbsbx.com','staticxx.com'];
                  // Scope to official page info containers only \u2014 avoid grabbing random post links
                  var profileAnchors = document.querySelectorAll('[data-pagelet="ProfileCards"] a[href], [data-pagelet="PageHeader"] a[href], [aria-label*="website" i] a[href], [aria-label*="Website" i]');
                  for (var i = 0; i < profileAnchors.length; i++) {
                    var hf = profileAnchors[i].href;
                    if (hf.indexOf('l.facebook.com/l.php?u=') > -1) {
                      var m = hf.match(/[?&]u=([^&]+)/);
                      if (m) { try { var u = decodeURIComponent(m[1]); var p = new URL(u); if (!exc.some(function(e) { return p.hostname.indexOf(e) > -1; })) { d.website = u; d.has_website = true; break; } } catch(e) {} }
                    } else if (hf.indexOf('http') === 0) {
                      try { var p2 = new URL(hf); if (!exc.some(function(e) { return p2.hostname.indexOf(e) > -1; })) { d.website = p2.origin + p2.pathname; d.has_website = true; break; } } catch(e) {}
                    }
                  }
                  // REMOVED body-text regex fallback for website on About page \u2014 too noisy (grabbed random URLs like ncl.com, sky.com, msn.com). Now only ProfileCards anchors above.
                  var am = body.match(/(?:Road|House|Floor|Level|Lane|Street|Block|Sector|Building|Village|Thana|Upazila).{5,120}(?:Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal)/i);
                  if (!am) am = body.match(/(?:Gulshan|Banani|Mirpur|Uttara|Dhanmondi|Mohammadpur|Motijheel|Khilgaon|Badda|Bashundhara|Farmgate|Shyamoli|Lalmatia|Malibagh|Rampura|Wari|Jatrabari).{5,80}(?:Dhaka|Chattogram|Chittagong|Sylhet)/i);
                  if (!am) am = body.match(/(?:Panthapath|Kakrail|Shahbag|Kawran Bazar|Elephant Road|New Market|Azimpur|Green Road|Nikunja|Baridhara|Bonosree|Aftab Nagar).{5,60}(?:Dhaka|Chattogram)/i);
                  if (!am) am = body.match(/\\b(Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal|Rangpur|Mymensingh|Comilla|Narayanganj|Gazipur)\\b/i);
          if (am) d.address = decodeURIComponent(am[0].trim());
                  var cats = ['Beauty Salon','Boutique','Clothing','Store','Shop','Restaurant','Cafe','Bakery','Jewelry','Skincare','Cosmetics','Fashion','Grocery','Pharmacy','Clinic','Fitness','Gym','Salon','Spa','Tailor','Studio'];
                  if (!d.category) { for (var i = 0; i < cats.length; i++) { if (new RegExp('\\\\b' + cats[i] + '\\\\b', 'i').test(body)) { d.category = cats[i]; break; } } }
                  return JSON.stringify(d);
                }'''
                about_raw = page.evaluate(about_js)
                about_data = json.loads(about_raw)
                if about_data.get('email') and not result.get('email'): result['email'] = about_data['email']
                if about_data.get('phone') and not result.get('phone'): result['phone'] = about_data['phone']
                if about_data.get('website') and not result.get('website'): result['website'] = about_data['website']; result['has_website'] = True
                if about_data.get('address') and not result.get('address'): result['address'] = about_data['address']
                if about_data.get('category') and not result.get('category'): result['category'] = about_data['category']
            except Exception:
                pass  # About page may be behind login \u2014 best-effort
    except Exception as e:
        raise Exception(f'Extraction failed: {e}')
    finally:
        ctx.close()

    # Score calculation
    score = 5
    if not result.get('has_website'):
        score += 1
    if result.get('phone'):
        score += 1
    if result.get('email'):
        score += 1
    if result.get('address'):
        score += 1
    if result.get('category'):
        score += 1
    if result.get('followers'):
        try:
            num = int(re.sub(r'[^0-9]', '', str(result['followers'])))
            if num < 50000:
                score += 1
        except ValueError:
            pass
    result['qualification_score'] = max(1, min(10, score))
    return result


def _extract_instagram_page(ig_url):
    result = {
        'url': ig_url,
        'business_name': '', 'category': '', 'followers': '',
        'email': '', 'phone': '', 'website': '', 'has_website': False,
        'address': '', 'last_post_date': '', 'qualification_score': 5,
    }
    browser = _get_browser()
    ctx = browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        locale='en_US',
        viewport={'width': 1280, 'height': 720},
    )
    _apply_fb_cookies(ctx)
    page = ctx.new_page()
    try:
        page.goto(ig_url, timeout=30000, wait_until='domcontentloaded')
        page.wait_for_timeout(8000)

        # Try to extract whatever is available (may be limited without login)
        try:
            page.evaluate("document.querySelector('article') && document.querySelector('article').scrollIntoView()")
            page.wait_for_timeout(2000)
        except:
            pass

        extract_js = """
        (function() {
          var d = {url: window.location.href.split('?')[0].replace(/\\/+$/, '')};
          var body = (document.body ? document.body.textContent : document.documentElement.textContent) || '';

          // Try Instagram's __NEXT_DATA__ or __INITIAL_STATE__ first
          try {
            var scripts = document.querySelectorAll('script:not([src])');
            for (var si = 0; si < scripts.length; si++) {
              var sc = scripts[si].textContent || '';
              if (sc.indexOf('__INITIAL_STATE__') > -1) {
                var start = sc.indexOf('{'), end = sc.lastIndexOf('}') + 1;
                var state = JSON.parse(sc.substring(start, end));
                var user = state && state.user && Object.values(state.user)[0];
                if (user) {
                  if (user.full_name) d.business_name = user.full_name;
                  if (user.biography) { d.bio = user.biography; }
                  if (user.edge_followed_by && user.edge_followed_by.count !== undefined) {
                    d.followers = String(user.edge_followed_by.count).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ',') + ' followers';
                  }
                  if (user.external_url) { d.website = user.external_url; d.has_website = true; }
                }
              }
            }
          } catch(e) {}

          // Fallback: meta tags
          if (!d.business_name) { var og = document.querySelector('meta[property="og:title"]'); if (og) { var oc = (og.getAttribute('content') || '')
            .replace(/ on Instagram$/, '').replace(/ \u2022 Instagram.*$/, '').replace(/ *\(@[a-zA-Z0-9_.]+\)/, '').trim(); if (oc && oc !== 'Instagram') d.business_name = oc; } }
          if (!d.business_name) { var t = document.title; if (t) { var tc = t.replace(/ \u2022 Instagram.*$/, '').replace(/ *\(@[a-zA-Z0-9_.]+\)/, '').trim(); if (tc && tc !== 'Instagram') d.business_name = tc; } }

          // Meta description for bio/category
          var desc = document.querySelector('meta[property="og:description"],meta[name="description"]');
          var dc = desc ? (desc.getAttribute('content') || '') : '';
          var allText = dc + ' ' + (d.bio || '') + ' ' + body;

          // Category from bio or description
          var catList = ['Beauty Salon','Boutique','Clothing','Store','Shop','Restaurant','Cafe','Bakery','Jewelry','Skincare','Cosmetics','Fashion','Grocery','Pharmacy','Clinic','Fitness','Gym','Salon','Spa','Tailor','Studio','Makeup','Nail','Photography','Decor','Brand','Agency','Service','Consultant','Coach','Travel','Hotel','Real Estate','Tech','IT','Software'];
          for (var ci = 0; ci < catList.length; ci++) {
            var re = new RegExp('\\\\b' + catList[ci] + '\\\\b', 'i');
            if (re.test(allText)) { d.category = catList[ci]; break; }
          }

          // Email from all text sources
          var emails = allText.match(/[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}/g);
          if (emails) {
            var seen = {};
            for (var ei = 0; ei < emails.length; ei++) {
              if (!/(facebook|fb\\.com|sentry|example)/i.test(emails[ei]) && !seen[emails[ei]]) {
                seen[emails[ei]] = true;
                d.email = (d.email || '') + (d.email ? ', ' : '') + emails[ei];
              }
            }
          }

          // Phone from body
          var cleanBody = body.replace(/[\\s\\-\\(\\)\\.]/g, '');
          var ph = cleanBody.match(/(?:01[3-9]\\d{8}|\\+?8801[3-9]\\d{8})/);
          if (ph) { var p = ph[0]; if (p.indexOf('+') !== 0 && p.indexOf('880') === 0) p = '+' + p; else if (p.indexOf('01') === 0) p = '+880' + p.slice(1); d.phone = p; }

          // Website from DOM links if not found in state
          // Filter known non-business links
          var exc = ['facebook','fb.com','instagram','twitter','youtube','whatsapp','wa.me','google','gmail','tiktok','snapchat','about.meta','about.facebook'];

          if (!d.website) {
            var links = document.querySelectorAll('a[href]');
            for (var li = 0; li < links.length; li++) {
              var hf = links[li].href;
              if (hf && hf.indexOf('http') === 0 && hf.indexOf('instagram.com') === -1) {
                try { var u = new URL(hf); if (!exc.some(function(e) { return u.hostname.indexOf(e) > -1; })) { d.website = hf; d.has_website = true; break; } } catch(e) {}
              }
            }
            if (!d.website) {
              var wm = allText.match(/(?:https?:\\/\\/)?(?:www\\.)?([a-zA-Z0-9-]+\\.(?:com|bd|net|org|shop|store|app))(?:\\/[^\\s]*)?/gi);
              if (wm) { for (var wi = 0; wi < wm.length; wi++) { try { var u = new URL(wm[wi].indexOf('http') === 0 ? wm[wi] : 'https://' + wm[wi]); if (!exc.some(function(e) { return u.hostname.indexOf(e) > -1; }) && !u.hostname.includes('instagram')) { d.website = u.href; d.has_website = true; break; } } catch(e) {} } }
            }
          }

          // Followers from og:description fallback
          if (!d.followers) { var fm = body.match(/([\\d,.]+[KkMm]?)\\s*followers?/i); if (fm) d.followers = fm[1].trim() + ' followers'; }
          if (!d.followers) { var fm2 = dc.match(/([\\d,.]+[KkMm]?)\\s*(?:follower|like)/i); if (fm2) d.followers = fm2[1].trim() + ' followers'; }

          // Address
          var cityRe = new RegExp('\\\\b(Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal|Rangpur|Mymensingh|Comilla|Narayanganj|Gazipur|Gulshan|Banani|Mirpur|Uttara|Dhanmondi|Mohammadpur)\\\\b', 'i');
          var am = body.match(cityRe);
          if (am) d.address = am[0].trim();

          // Post date
          var timeEls = document.querySelectorAll('time');
          for (var ti = 0; ti < timeEls.length; ti++) {
            var t = timeEls[ti].getAttribute('datetime') || timeEls[ti].textContent || '';
            if (t) { d.last_post_date = t; break; }
          }
          if (!d.last_post_date) {
            var pdRe = new RegExp('\\\\b(?:about\\\\s+)?(?:\\\\d+|an?)\\\\s+(hours?|minutes?|days?|weeks?|months?|years?)\\\\s+ago\\\\b|^just now$', 'gi');
            var tm = body.match(pdRe);
            if (tm) d.last_post_date = tm[0];
          }

          return JSON.stringify(d);
        })();
        """
        raw = page.evaluate(extract_js)
        data = json.loads(raw)
        result.update(data)
        result['url'] = ig_url.rstrip('/')
    except Exception as e:
        raise Exception(f'Extraction failed: {e}')
    finally:
        ctx.close()

    score = 5
    if not result.get('has_website'):
        score += 1
    if result.get('phone'):
        score += 1
    if result.get('email'):
        score += 1
    if result.get('category'):
        score += 1
    if result.get('followers'):
        try:
            num = int(re.sub(r'[^0-9]', '', str(result['followers'])))
            if num < 50000:
                score += 1
        except ValueError:
            pass
    result['qualification_score'] = max(1, min(10, score))
    return result


class Handler(BaseHTTPRequestHandler):

    def _cors_headers(self):
        origin = self.headers.get('Origin', '')
        allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
        allowed_origins = [o.strip() for o in allowed_origins if o.strip()]
        if origin in allowed_origins or '*' in allowed_origins:
            self.send_header('Access-Control-Allow-Origin', origin if origin and '*' not in allowed_origins else '*')
        else:
            self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Max-Age', '86400')

    def _security_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'strict-origin-when-cross-origin')
        self.send_header('Permissions-Policy', 'geolocation=(), microphone=(), camera=(), payment=()')

    def _json(self, code, body):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self._security_headers()
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0: return None
        body = self.rfile.read(length)
        try: return json.loads(body)
        except json.JSONDecodeError: return None

    def _serve_static(self, filename):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if not os.path.exists(path):
            self._json(404, {'error': 'File not found'})
            return
        with open(path, 'rb') as f:
            content = f.read()
        ext = filename.split('.')[-1]
        mime_map = {'html': 'text/html', 'css': 'text/css', 'js': 'application/javascript', 'png': 'image/png', 'svg': 'image/svg+xml'}
        self.send_response(200)
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        if ext == 'html':
            ts = str(int(time.time() * 1000))
            content = content.replace(b'</head>', b'<!-- v=' + ts.encode() + b' --></head>')
        self.send_header('Content-Type', mime_map.get(ext, 'application/octet-stream'))
        self.send_header('Content-Length', str(len(content)))
        self._cors_headers()
        self._security_headers()
        self.end_headers()
        self.wfile.write(content)

    def _serve_bookmarklet_js(self):
        host = self.headers.get('Host', '127.0.0.1:8800')
        base = f'http://{host}'
        bm_js = f'''(function(){{
  var d={{url:window.location.href.split('?')[0].replace(/\\/+$/,'')}};

  /* \u2500\u2500 Business Name \u2500\u2500 */
  var h=document.querySelector('[data-pagelet="ProfileHeader"],[data-pagelet="CommercialProfile"]');
  if(h){{var el=h.querySelector('h1,h2,strong');if(el)d.business_name=el.innerText.trim();}}
  if(!d.business_name){{var og=document.querySelector('meta[property="og:title"]');if(og)d.business_name=(og.getAttribute('content')||'').trim();}}
  if(!d.business_name){{var h1=document.querySelector('h1');if(h1)d.business_name=h1.innerText.trim();}}
  if(!d.business_name){{var t=document.title.replace(/ \\| Facebook$/,'').replace(/ - Facebook$/,'').trim();if(t&&!/^search/i.test(t))d.business_name=t;}}

  /* \u2500\u2500 Category \u2500\u2500 */
  var cats=['Beauty Salon','Boutique','Clothing','Store','Shop','Restaurant','Cafe','Bakery','Jewelry','Skincare','Cosmetics','Fashion','Grocery','Pharmacy','Clinic','Fitness','Gym','Salon','Spa','Tailor','Studio'];
  var body=document.body.innerText||'';
  for(var i=0;i<cats.length;i++){{if(new RegExp('\\\\b'+cats[i]+'\\\\b','i').test(body)){{d.category=cats[i];break;}}}}
  if(!d.category){{var desc=document.querySelector('meta[property="og:description"]');if(desc){{var dc=desc.getAttribute('content')||'';for(var i=0;i<cats.length;i++){{if(new RegExp('\\\\b'+cats[i]+'\\\\b','i').test(dc)){{d.category=cats[i];break;}}}}}}}}

  /* \u2500\u2500 Followers \u2500\u2500 */
  var fm=body.match(/([\\d,.]+[KkMmBb]?)\\s*(followers|likes|people follow|\u099c\u09a8 \u09ab\u09b2\u09cb\u09af\u09bc\u09be\u09b0|follower)/i);
  if(!fm)fm=body.match(/([\\d,.]+[KkMmBb]?)\\s*followers?\\s*[\\u2022\\/\\|\\-]\\s*(?:\\d+\\s*)?following/i);
  if(!fm)fm=body.match(/([\\d,.]+[KkMmBb]?)\\s*(?:\\w+\\s+)?(?:followers?|likes?)/i);
  if(fm)d.followers=fm[1];
  // Fallback: og:description (e.g. "Pearl Kingdom, Dhaka. 266,936 likes ...")
  if(!d.followers){{var ogd=(document.querySelector('meta[property="og:description"],meta[name="description"]')||{{}}).content||'';var ofm=ogd.match(/([\\d,.]+[KkMmBb]?)\\s*(likes|followers)/i);if(ofm)d.followers=ofm[1];}}

  /* \u2500\u2500 Email \u2500\u2500 */
  var em=body.match(/[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{{2,}}/g);
  if(em){{for(var i=0;i<em.length;i++){{if(!/(facebook|fb\\.com|sentry|example)/i.test(em[i])){{d.email=em[i];break;}}}}}}

  /* \u2500\u2500 Phone (BD format) \u2500\u2500 */
  var ph=body.replace(/[\\s\\-\\(\\)\\.]/g,'').match(/(?:01[3-9]\\d{{8}}|\\+?8801[3-9]\\d{{8}})/);
  if(ph){{var p=ph[0];if(p.indexOf('+')!==0&&p.indexOf('880')===0)p='+'+p;else if(p.indexOf('01')===0)p='+880'+p.slice(1);d.phone=p;}}

  /* \u2500\u2500 Website \u2500\u2500 */
  var excl=['facebook','fb\\.com','fbcdn','instagram','twitter','youtube','whatsapp','wa\\.me','messenger','google','gmail'];
  var links=document.querySelectorAll('a[href]');
  for(var i=0;i<links.length;i++){{var hf=links[i].href;if(hf.indexOf('l.facebook.com/l.php?u=')>-1){{var m=hf.match(/[?&]u=([^&]+)/);if(m){{try{{var u=decodeURIComponent(m[1]);var p=new URL(u);if(!excl.some(function(e){{return p.hostname.indexOf(e)>-1}})){{d.website=u;d.has_website=true;break;}}}}catch(e){{}}}}}}}}
  /* REMOVED body-text regex fallback \u2014 too noisy (grabbed random URLs like ncl.com, sky.com, msn.com). Instagram typically provides website via external_url above. */

  /* \u2500\u2500 Address \u2500\u2500 */
  var am=body.match(/(?:Road|House|Floor|Level|Lane|Street|Block|Sector|Building|Village|Thana|Upazila).{{5,120}}(?:Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal)/i);
  if(!am){{var ogd=(document.querySelector('meta[property="og:description"],meta[name="description"]')||{{}}).content||'';var am2=ogd.match(/(?:Shop|House|Building|Road|Block|Sector|Floor|Gulshan|Banani|Mirpur|Uttara|Dhanmondi|Bashundhara).{{3,90}}(?:Dhaka|Chattogram)/i);if(am2)am=am2;}}
  if(am)d.address=am[0].trim();

  /* \u2500\u2500 Last Post Date \u2500\u2500 */
  var abbrs=document.querySelectorAll('abbr');
  for(var i=0;i<abbrs.length;i++){{var t=abbrs[i].getAttribute('aria-label')||abbrs[i].getAttribute('title')||abbrs[i].textContent||'';if(t&&!/notification/i.test(t)){{if(/\\b(?:about\\s+)?(?:\\d+|an?)\\s+(hours?|minutes?|days?|weeks?|months?|years?)\\s+ago\\b|^just now$/i.test(t)){{d.last_post_date=t;break;}}}}}}
  if(!d.last_post_date){{var timeEls=document.querySelectorAll('time');for(var ti=0;ti<timeEls.length;ti++){{var iso=timeEls[ti].getAttribute('datetime')||'';if(iso&&/\\d{{4}}/.test(iso)){{d.last_post_date=iso;break;}}}}}}
  if(!d.last_post_date){{var tm=body.match(/\\b(?:about\\s+)?(?:\\d+|an?)\\s+(hours?|minutes?|days?|weeks?|months?|years?)\\s+ago\\b|^just now$/gi);if(tm)d.last_post_date=tm[0];}}
  if(!d.last_post_date){{var abbrRe=body.match(/\\b(?:just now|yesterday)\\b|\\b(\\d+)\\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days|w|wk|wks|week|weeks|mo|mos|month|months|y|yr|yrs|year|years)\\b/gi);if(abbrRe&&abbrRe.length)d.last_post_date=abbrRe[0];}}
  if(!d.last_post_date){{var bnRe=body.match(/\\d+\\s*(\u09b8\u09c7\u0995\u09c7\u09a8\u09cd\u09a1|\u09ae\u09bf\u09a8\u09bf\u099f|\u0998\u09a3\u09cd\u099f\u09be|\u09a6\u09bf\u09a8|\u09b8\u09aa\u09cd\u09a4\u09be\u09b9|\u09ae\u09be\u09b8|\u09ac\u099b\u09b0)\\s*(\u0986\u0997\u09c7|\u09aa\u09c2\u09b0\u09cd\u09ac\u09c7)/);if(bnRe)d.last_post_date=bnRe[0];}}
  if(d.last_post_date){{var norm=d.last_post_date.trim().toLowerCase();var map={{'just now':'Just now','yesterday':'Yesterday'}};if(map[norm]){{d.last_post_date=map[norm];}}else{{var m=norm.match(/^(\\d+)\\s*([a-z]+)/);if(m){{var n=parseInt(m[1]);var unit=m[2];var unitMap={{s:'second',sec:'second',secs:'second',second:'second',seconds:'second',m:'minute',min:'minute',mins:'minute',minute:'minute',minutes:'minute',h:'hour',hr:'hour',hrs:'hour',hour:'hour',hours:'hour',d:'day',day:'day',days:'day',w:'week',wk:'week',wks:'week',week:'week',weeks:'week',mo:'month',mos:'month',month:'month',months:'month',y:'year',yr:'year',yrs:'year',year:'year',years:'year'}};var fullUnit=unitMap[unit]||unit;d.last_post_date=n+' '+fullUnit+(n===1?'':'s')+' ago';}}}}}}

  /* \u2500\u2500 Score \u2500\u2500 */
  var sc=5;
  if(!d.has_website)sc++;
  if(d.phone)sc++;
  if(d.email)sc++;
  if(d.address)sc++;
  if(d.category)sc++;
  if(d.followers){{var n=parseInt(d.followers.replace(/[^0-9]/g,''));if(!isNaN(n)&&n<50000)sc++;}}
  if(d.last_post_date){{var days=999;if(/just now|min|hour/i.test(d.last_post_date))days=0;else{{var nu=parseInt(d.last_post_date.match(/\\d+/)?.[0]||'0');if(/day/i.test(d.last_post_date))days=nu;else if(/week/i.test(d.last_post_date))days=nu*7;else if(/month/i.test(d.last_post_date))days=nu*30;else if(/year/i.test(d.last_post_date))days=nu*365;}}if(days>90)sc-=4;else if(days>50)sc-=2;}}
  d.qualification_score=Math.max(1,Math.min(10,sc));

  /* \u2500\u2500 Navigate \u2500\u2500 */
  var enc=encodeURIComponent(JSON.stringify(d));
  window.location.href='{base}/extract?data='+enc;
}})();'''
        self.send_response(200)
        self.send_header('Content-Type', 'application/javascript')
        self.send_header('Content-Length', str(len(bm_js)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(bm_js.encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/health':
            self._json(200, {'status': 'ok'})
        elif parsed.path == '/api/lead':
            params = parse_qs(parsed.query)
            url_param = params.get('url', [None])[0]
            if url_param:
                user = require_auth(self)
                if not user: return
                is_admin = user['role'] in ('admin', 'super_admin')
                leads = read_all_leads(user_id=user['id'], include_all_users=is_admin)
                lead = next((l for l in leads if l.get('page_url', '').strip() == url_param), None)
                if lead:
                    self._json(200, lead)
                else:
                    self._json(404, {'error': 'Lead not found'})
            else:
                self._json(400, {'error': 'url parameter required'})
        elif parsed.path == '/api/leads':
            user = require_auth(self)
            if not user: return
            params = parse_qs(parsed.query)
            status_filter = params.get('status', [None])[0]
            is_admin = user['role'] in ('admin', 'super_admin')
            if is_admin:
                leads = read_all_leads(filter_status=status_filter, include_all_users=True)
            else:
                leads = read_all_leads(filter_status=status_filter, user_id=user['id'])
            self._json(200, leads)
        elif parsed.path == '/api/leads/trash':
            user = require_auth(self)
            if not user: return
            is_admin = user['role'] in ('admin', 'super_admin')
            if is_admin:
                self._json(200, read_trashed_leads(include_all_users=True))
            else:
                self._json(200, read_trashed_leads(user_id=user['id']))
        elif parsed.path == '/api/trash/stats':
            user = require_auth(self)
            if not user: return
            is_admin = user['role'] in ('admin', 'super_admin')
            if is_admin:
                all_leads = read_all_leads(include_trashed=True, include_all_users=True)
            else:
                all_leads = read_all_leads(include_trashed=True, user_id=user['id'])
            trashed = [l for l in all_leads if (l.get('deleted_at') or '').strip()]
            self._json(200, {'trashed_count': len(trashed)})
        elif parsed.path == '/api/funnel':
            user = require_auth(self)
            if not user: return
            is_admin = user['role'] in ('admin', 'super_admin')
            self._json(200, get_funnel_stats(user_id=user['id'], include_all_users=is_admin))
        elif parsed.path == '/api/leads/qualified':
            self._json(200, get_qualified_leads())
        elif parsed.path == '/api/last-lead':
            url = get_last_lead_url()
            if url:
                self._json(200, {'page_url': url})
            else:
                self._json(404, {'error': 'No recent lead'})
        # \u2500\u2500 F-Commerce GET endpoints \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        elif parsed.path == '/api/fcommerce/leads':
            params = parse_qs(parsed.query)
            filters = {
                'priority': params.get('priority', [None])[0],
                'source': params.get('source', [None])[0],
                'category': params.get('category', [None])[0],
            }
            if not any(filters.values()):
                filters = None
            leads = _read_fcommerce_leads(filters=filters)
            self._json(200, leads)
        elif parsed.path == '/api/fcommerce/stats':
            self._json(200, _fcommerce_stats())
        elif parsed.path == '/api/fcommerce/export':
            leads = _read_fcommerce_leads()
            import io
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=FCOMMERCE_COLUMNS)
            writer.writeheader()
            for lead in leads:
                writer.writerow(lead)
            csv_bytes = output.getvalue().encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="fcommerce_leads_export.csv"')
            self.send_header('Content-Length', str(len(csv_bytes)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(csv_bytes)
            return
        elif parsed.path == '/api/outreach/status':
            token_ok = lead_gen_outreach.get_netlify_token() is not None
            self._json(200, {
                'netlify_token_configured': token_ok,
                'telegram_configured': bool(TELEGRAM_TOKEN),
            })
        elif parsed.path in ('/', '/extract'):
            self._serve_static('extract.html')
        elif parsed.path == '/leads':
            self._serve_static('leads.html')
        elif parsed.path == '/trash':
            self._serve_static('trash.html')
        elif parsed.path == '/login':
            self._serve_static('login.html')
        elif parsed.path == '/register':
            self._serve_static('register.html')
        elif parsed.path == '/profile':
            self._serve_static('profile.html')
        elif parsed.path == '/pricing':
            self._serve_static('pricing.html')
        elif parsed.path == '/forgot-password':
            self._serve_static('forgot-password.html')
        elif parsed.path == '/reset-password':
            self._serve_static('reset-password.html')
        elif parsed.path == '/admin':
            self._serve_static('admin.html')
        elif parsed.path == '/api/auth/me':
            user = require_auth(self)
            if not user: return
            self._json(200, user)
        elif parsed.path == '/api/debug/sessions':
            conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT * FROM sessions ORDER BY id DESC LIMIT 10')
            rows = [dict(r) for r in c.fetchall()]
            c.execute('SELECT COUNT(*) as cnt FROM sessions')
            total = c.fetchone()['cnt']
            conn.close()
            self._json(200, {'total_sessions': total, 'sessions': rows, 'db_path': AUTH_DB_PATH})
        elif parsed.path == '/api/auth/leads-remaining':
            user = require_auth(self)
            if not user: return
            limit = get_lead_limit(user)
            remaining = max(0, limit - user['leads_used'])
            self._json(200, {'leads_used': user['leads_used'], 'leads_limit': limit, 'leads_remaining': remaining, 'tier': user.get('subscription_tier', 'free')})
        elif parsed.path == '/api/admin/users':
            user = require_auth(self)
            if not user: return
            if user['role'] not in ('admin', 'super_admin'):
                self._json(403, {'error': 'Forbidden'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id, name, email, role, created_at FROM users ORDER BY id')
            users = [{'id': r[0], 'name': r[1], 'email': r[2], 'role': r[3], 'created_at': r[4]} for r in c.fetchall()]
            conn.close()
            self._json(200, users)
        elif parsed.path == '/api/admin/stats':
            user = require_auth(self)
            if not user: return
            if user['role'] not in ('admin', 'super_admin'):
                self._json(403, {'error': 'Forbidden'})
                return
            leads = read_all_leads(include_all_users=True)
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM users')
            user_count = c.fetchone()[0]
            c.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
            role_counts = {r: cnt for r, cnt in c.fetchall()}
            conn.close()
            statuses = {}
            this_month = 0
            now = datetime.now()
            month_prefix = now.strftime('%Y-%m')
            for l in leads:
                s = l.get('status', 'unknown')
                statuses[s] = statuses.get(s, 0) + 1
                d = (l.get('date') or '').strip()
                if d.startswith(month_prefix):
                    this_month += 1
            self._json(200, {
                'total_leads': len(leads),
                'total_users': user_count,
                'role_counts': role_counts,
                'statuses': statuses,
                'this_month': this_month,
                'month_label': now.strftime('%B %Y'),
            })
        elif parsed.path == '/api/bookmarklet-extract':
            self._serve_bookmarklet_js()
        elif parsed.path == '/api/qualified/daily-files':
            files = []
            if os.path.exists(QUALIFIED_DIR):
                for fname in os.listdir(QUALIFIED_DIR):
                    if fname.endswith('.csv') and fname != 'qualified_leads.csv':
                        fpath = os.path.join(QUALIFIED_DIR, fname)
                        fsize = os.path.getsize(fpath)
                        with open(fpath, 'r', newline='', encoding='utf-8') as f:
                            row_count = sum(1 for _ in csv.DictReader(f))
                        files.append({
                            'filename': fname,
                            'date': fname.split('_')[0],
                            'day': fname.replace('.csv', '').split('_', 1)[1] if '_' in fname else '',
                            'records': row_count,
                            'size_bytes': fsize,
                        })
            self._json(200, sorted(files, key=lambda x: x['filename'], reverse=True))
        elif parsed.path == '/api/qualified/daily':
            params = parse_qs(parsed.query)
            req_date = params.get('date', [None])[0]
            if not req_date:
                self._json(400, {'error': 'date parameter required (YYYY-MM-DD)'})
                return
            if not os.path.exists(QUALIFIED_DIR):
                self._json(404, {'error': f'No daily file found for {req_date}'})
                return
            for fname in os.listdir(QUALIFIED_DIR):
                if fname.startswith(req_date) and fname.endswith('.csv'):
                    fpath = os.path.join(QUALIFIED_DIR, fname)
                    with open(fpath, 'r', newline='', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        leads = [r for r in reader]
                    self._json(200, {'filename': fname, 'date': req_date, 'leads': leads})
                    return
            self._json(404, {'error': f'No daily file found for {req_date}'})
        elif parsed.path == '/api/user/preferences':
            user = require_auth(self)
            if not user: return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT COALESCE(telegram_notifications, 1) FROM users WHERE id = ?', (user['id'],))
            row = c.fetchone()
            conn.close()
            self._json(200, {'telegram_notifications': (str(row[0]) == '1') if row else True})
        elif parsed.path.startswith('/api/avatars/'):
            fname = os.path.basename(parsed.path)
            if USE_MONGO and cloudinary_storage and cloudinary_storage.is_configured():
                user_id = fname.rsplit('.', 1)[0]
                url = cloudinary_storage.get_avatar_url(user_id)
                if url:
                    self.send_response(302)
                    self.send_header('Location', url)
                    self.send_header('Cache-Control', 'public, max-age=86400')
                    self._cors_headers()
                    self.end_headers()
                    return
                self._json(404, {'error': 'Not found'})
                return
            fpath = os.path.join(AVATAR_DIR, fname)
            if not os.path.exists(fpath):
                self._json(404, {'error': 'Not found'})
                return
            with open(fpath, 'rb') as f:
                content = f.read()
            ext = fname.split('.')[-1].lower()
            mime = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}.get(ext, 'image/jpeg')
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'public, max-age=86400')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return
        elif parsed.path.startswith('/assets/'):
            # Serve files from the project's assets/ directory (js, css, icons, etc.)
            rel = parsed.path[len('/assets/'):]
            # Prevent path traversal
            if '..' in rel or rel.startswith('/'):
                self._json(404, {'error': 'Not found'})
                return
            fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', rel)
            if not os.path.exists(fpath) or not os.path.isfile(fpath):
                self._json(404, {'error': 'Not found'})
                return
            with open(fpath, 'rb') as f:
                content = f.read()
            ext = rel.split('.')[-1].lower()
            mime = {'js': 'application/javascript', 'css': 'text/css', 'png': 'image/png', 'svg': 'image/svg+xml', 'ico': 'image/x-icon', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'webp': 'image/webp'}.get(ext, 'application/octet-stream')
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'public, max-age=3600')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(content)
            return
        else:
            self._json(404, {'error': 'Not found'})

    def _handle_avatar_upload(self):
        user = require_auth(self)
        if not user: return
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            self._json(400, {'error': 'No file data'})
            return
        content_type = self.headers.get('Content-Type', '')
        raw = self.rfile.read(length)
        boundary = None
        for part in content_type.split(';'):
            part = part.strip()
            if part.startswith('boundary='):
                boundary = part[9:].strip()
                if boundary.startswith('"') and boundary.endswith('"'):
                    boundary = boundary[1:-1]
                break
        if not boundary:
            self._json(400, {'error': 'No boundary in Content-Type'})
            return
        delimiter = b'--' + boundary.encode()
        parts = raw.split(delimiter)
        for part in parts:
            if b'name="avatar"' in part:
                idx = part.find(b'\r\n\r\n')
                if idx > -1:
                    fdata = part[idx + 4:].rstrip(b'\r\n--')
                    public_url = None
                    if USE_MONGO and cloudinary_storage and cloudinary_storage.is_configured():
                        public_url = cloudinary_storage.upload_avatar(user['id'], fdata)
                        if public_url and USE_MONGO:
                            mongo_db.update_user(user['id'], {'avatar_url': public_url})
                    if not public_url:
                        os.makedirs(AVATAR_DIR, exist_ok=True)
                        fpath = os.path.join(AVATAR_DIR, f'{user["id"]}.jpg')
                        with open(fpath, 'wb') as fout:
                            fout.write(fdata)
                        public_url = f'/api/avatars/{user["id"]}.jpg'
                    self._json(200, {'status': 'uploaded', 'url': public_url})
                    return
        self._json(400, {'error': 'avatar field not found in upload'})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == '/api/auth/avatar':
            self._handle_avatar_upload()
            return
        data = self._read_body()

        if parsed.path == '/api/lead':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user:
                return
            if not user.get('email_verified'):
                self._json(403, {'error': 'Please verify your email before saving leads', 'verify_required': True})
                return
            ok, remaining = can_extract_lead(user)
            if not ok:
                self._json(403, {'error': f'Lead limit reached ({get_lead_limit(user)}). Upgrade to Pro for unlimited leads.', 'limit_reached': True, 'tier': user.get('subscription_tier', 'free')})
                return
            ensure_csv()
            # Only admin / super_admin may trigger Telegram notifications.
            # Regular users and 'pro' users always save DB-only, regardless of payload or preference.
            is_admin_or_super = user.get('role') in ('admin', 'super_admin')
            if is_admin_or_super:
                if 'notify_telegram' in data:
                    user_notify = bool(data.get('notify_telegram'))
                else:
                    conn_pref = sqlite3.connect(AUTH_DB_PATH)
                    c_pref = conn_pref.cursor()
                    c_pref.execute('SELECT COALESCE(telegram_notifications, 1) FROM users WHERE id = ?', (user['id'],))
                    pref_row = c_pref.fetchone()
                    conn_pref.close()
                    user_notify = (str(pref_row[0]) == '1') if pref_row else True
            else:
                user_notify = False
            data['_saved_by_name'] = user.get('name', '') or ''
            data['_saved_by_id'] = user.get('id', 0)
            data['saved_by_user_name'] = data['_saved_by_name']
            data['saved_by_user_id'] = data['_saved_by_id']
            is_new, msg = append_lead(data, notify_telegram=user_notify, user_id=user['id'])
            if msg == 'duplicate':
                self._json(200, {'status': 'duplicate', 'message': 'Lead already exists, skipped'})
            elif is_new:
                conn = sqlite3.connect(AUTH_DB_PATH)
                c = conn.cursor()
                c.execute('UPDATE users SET leads_used = leads_used + 1 WHERE id = ?', (user['id'],))
                conn.commit()
                conn.close()
                self._json(201, {'status': 'saved', 'message': msg, 'leads_remaining': remaining - 1})
            else:
                self._json(400, {'status': 'error', 'message': msg})
        elif parsed.path == '/api/lead/status':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            page_url = data.get('page_url', '').strip()
            new_status = data.get('status', '').strip().lower()
            follow_up = data.get('follow_up_date', '').strip()
            if not page_url or not new_status:
                self._json(400, {'error': 'page_url and status required'})
                return
            ok, msg = update_lead_status(page_url, new_status, follow_up, user_id=user['id'])
            if ok:
                self._json(200, {'status': 'updated', 'message': msg})
            else:
                self._json(400, {'error': msg})
        elif parsed.path == '/api/lead/delete':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_url = data.get('page_url', '').strip()
            if not page_url:
                self._json(400, {'error': 'page_url required'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            ok, msg = trash_lead(page_url, user_id=user['id'])
            if not ok and is_admin:
                ok, msg = trash_lead(page_url)
            if ok:
                self._json(200, {'status': 'trashed', 'message': 'Moved to Trash \u2014 recoverable', 'page_url': page_url})
            else:
                self._json(400, {'error': msg})
        elif parsed.path == '/api/lead/trash':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_url = data.get('page_url', '').strip()
            if not page_url:
                self._json(400, {'error': 'page_url required'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            ok, msg = trash_lead(page_url, user_id=user['id'])
            if not ok and is_admin:
                ok, msg = trash_lead(page_url)
            if ok:
                self._json(200, {'status': 'trashed', 'message': 'Moved to Trash', 'page_url': page_url})
            else:
                self._json(400, {'error': msg})
        elif parsed.path == '/api/lead/restore':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_url = data.get('page_url', '').strip()
            if not page_url:
                self._json(400, {'error': 'page_url required'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            ok, msg = restore_lead(page_url, user_id=user['id'])
            if not ok and is_admin:
                ok, msg = restore_lead(page_url)
            if ok:
                self._json(200, {'status': 'restored', 'message': 'Recovered from Trash', 'page_url': page_url})
            else:
                self._json(400, {'error': msg})
        elif parsed.path == '/api/lead/purge':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_url = data.get('page_url', '').strip()
            if not page_url:
                self._json(400, {'error': 'page_url required'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            ok, msg = purge_lead(page_url, user_id=user['id'])
            if not ok and is_admin:
                ok, msg = purge_lead(page_url)
            if ok:
                self._json(200, {'status': 'purged', 'message': 'Permanently deleted', 'page_url': page_url})
            else:
                self._json(400, {'error': msg})
        elif parsed.path == '/api/lead/bulk-trash':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_urls = data.get('page_urls', [])
            if not isinstance(page_urls, list) or not page_urls:
                self._json(400, {'error': 'page_urls must be a non-empty list'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            moved = []
            failed = []
            for url in page_urls:
                url = (url or '').strip()
                if not url:
                    continue
                ok, msg = trash_lead(url, user_id=user['id'])
                if not ok and is_admin:
                    ok, msg = trash_lead(url)
                if ok:
                    moved.append(url)
                else:
                    failed.append({'page_url': url, 'reason': msg})
            self._json(200, {'status': 'ok', 'moved_count': len(moved), 'failed_count': len(failed), 'moved': moved, 'failed': failed})
        elif parsed.path == '/api/lead/bulk-restore':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_urls = data.get('page_urls', [])
            if not isinstance(page_urls, list) or not page_urls:
                self._json(400, {'error': 'page_urls must be a non-empty list'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            restored = []
            failed = []
            for url in page_urls:
                url = (url or '').strip()
                if not url:
                    continue
                ok, msg = restore_lead(url, user_id=user['id'])
                if not ok and is_admin:
                    ok, msg = restore_lead(url)
                if ok:
                    restored.append(url)
                else:
                    failed.append({'page_url': url, 'reason': msg})
            self._json(200, {'status': 'ok', 'restored_count': len(restored), 'failed_count': len(failed), 'restored': restored, 'failed': failed})
        elif parsed.path == '/api/lead/bulk-purge':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_urls = data.get('page_urls', [])
            if not isinstance(page_urls, list) or not page_urls:
                self._json(400, {'error': 'page_urls must be a non-empty list'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            purged = []
            failed = []
            for url in page_urls:
                url = (url or '').strip()
                if not url:
                    continue
                ok, msg = purge_lead(url, user_id=user['id'])
                if not ok and is_admin:
                    ok, msg = purge_lead(url)
                if ok:
                    purged.append(url)
                else:
                    failed.append({'page_url': url, 'reason': msg})
            self._json(200, {'status': 'ok', 'purged_count': len(purged), 'failed_count': len(failed), 'purged': purged, 'failed': failed})
        elif parsed.path == '/api/lead/bulk-delete':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            page_urls = data.get('page_urls', [])
            if not isinstance(page_urls, list) or not page_urls:
                self._json(400, {'error': 'page_urls must be a non-empty list'})
                return
            is_admin = user['role'] in ('admin', 'super_admin')
            moved = []
            failed = []
            for url in page_urls:
                url = (url or '').strip()
                if not url:
                    continue
                ok, msg = trash_lead(url, user_id=user['id'])
                if not ok and is_admin:
                    ok, msg = trash_lead(url)
                if ok:
                    moved.append(url)
                else:
                    failed.append({'page_url': url, 'reason': msg})
            self._json(200, {'status': 'ok', 'deleted_count': len(moved), 'failed_count': len(failed), 'deleted': moved, 'failed': failed, 'note': 'Moved to Trash \u2014 recoverable from /trash'})
        elif parsed.path == '/api/lead/action':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            action = data.get('action', '').strip().lower()
            name = data.get('business_name', '').strip()
            if not action or not name:
                self._json(400, {'error': 'action and business_name required'})
                return
            if action not in ('qualify', 'disqualify', 'demo'):
                self._json(400, {'error': "action must be qualify, disqualify, or demo"})
                return

            lead = _find_lead_by_name(name, user_id=user['id'])
            if not lead:
                self._json(404, {'error': f'Lead "{name}" not found'})
                return

            page_url = lead.get('page_url', '').strip()

            if action == 'qualify':
                ok, msg = update_lead_status(page_url, 'qualified', user_id=user['id'])
                if ok:
                    self._json(200, {'status': 'qualified', 'message': f'\u2705 {lead["business_name"]} qualified & saved to vault'})
                else:
                    self._json(400, {'error': msg})
            elif action == 'disqualify':
                ok, msg = delete_lead(page_url, user_id=user['id'])
                if ok:
                    self._json(200, {'status': 'deleted', 'message': f'\u274c {lead["business_name"]} removed from leads'})
                else:
                    self._json(400, {'error': msg})
            elif action == 'demo':
                n = lead.get('business_name', '') or lead.get('name', '')
                p = lead.get('phone', '')
                cat = lead.get('category', '')
                addr = lead.get('address', '')
                _generate_and_send_demo(TELEGRAM_CHAT_ID, TELEGRAM_THREAD_ID, lead, n, p, cat, addr)
                self._json(200, {'status': 'demo_generated', 'message': f'\U0001F310 Demo for {n} sent to Dashboard'})
        # \u2500\u2500 F-Commerce POST / DELETE endpoints \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        elif parsed.path == '/api/fcommerce/lead':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            ok, msg, result = _save_fcommerce_lead(data)
            if msg == 'duplicate':
                self._json(200, {'status': 'duplicate', 'message': 'F-Commerce lead already exists'})
            elif msg.startswith('score_too_low'):
                self._json(400, {
                    'status': 'rejected',
                    'message': msg,
                    'warning': 'Lead rejected \u2014 score below 6. Improve website status, followers, or post recency to qualify.'
                })
            elif ok:
                self._json(201, {
                    'status': 'saved',
                    'message': msg,
                    'lead': result,
                })
            else:
                self._json(400, {'status': 'error', 'message': msg})
        elif parsed.path == '/api/fcommerce/lead/delete':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            page_url = data.get('page_url', '').strip()
            if not page_url:
                self._json(400, {'error': 'page_url required'})
                return
            ok, msg = _delete_fcommerce_lead(page_url)
            if ok:
                self._json(200, {'status': 'deleted', 'message': msg})
            else:
                self._json(400, {'error': msg})
        # \u2500\u2500 Lead Gen Outreach \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        elif parsed.path == '/api/outreach':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            text = data.get('text', '').strip()
            if not text:
                self._json(400, {'error': 'text (lead card) required'})
                return
            intent = data.get('intent', '').strip().lower()
            print(f"\n{'='*60}", flush=True)
            print(f"OUTREACH: Lead card received ({len(text)} chars)", flush=True)
            if intent:
                print(f"  Intent provided: {intent}", flush=True)
            print(f"{'='*60}", flush=True)
            # Parse + ask \u2014 do NOT auto-execute unless intent is clearly demo
            result = lead_gen_outreach.process_lead_init(text, intent=intent)
            if result.get('error') == 'NETLIFY_TOKEN_REQUIRED':
                self._json(412, {'status': 'token_required', 'message': result.get('message', '')})
            elif result.get('success') and result.get('netlify_url'):
                self._json(200, {
                    'status': 'deployed',
                    'netlify_url': result['netlify_url'],
                    'build_time': result['build_time'],
                    'business_name': result.get('lead', {}).get('business_name', ''),
                })
            elif result.get('success') and result.get('lead_id'):
                self._json(202, {
                    'status': 'pending',
                    'lead_id': result['lead_id'],
                    'business_name': result.get('lead', {}).get('business_name', ''),
                    'message': 'Lead received. Choose action: POST /api/outreach/action with lead_id and action (demo/outreach/qualify/all)',
                })
            else:
                self._json(400, {
                    'status': 'error',
                    'error': result.get('error', 'Could not parse lead card'),
                })
        elif parsed.path == '/api/outreach/action':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            lead_id = data.get('lead_id', '').strip()
            action = data.get('action', '').strip().lower()
            if not lead_id or not action:
                self._json(400, {'error': 'lead_id and action required'})
                return
            print(f"OUTREACH ACTION: {action} for lead {lead_id}", flush=True)
            result = lead_gen_outreach.execute_lead_action(lead_id, action)
            if result.get('error') == 'NETLIFY_TOKEN_REQUIRED':
                self._json(412, {'status': 'token_required', 'message': result.get('message', '')})
            elif result.get('success'):
                self._json(200, result)
            else:
                self._json(400, {'status': 'error', 'error': result.get('error', 'Unknown error')})
        elif parsed.path == '/api/outreach/token':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            token = data.get('token', '').strip()
            if not token:
                self._json(400, {'error': 'token required'})
                return
            lead_gen_outreach.set_netlify_token(token)
            self._json(200, {'status': 'saved', 'message': 'Netlify token saved to .env'})
        elif parsed.path == '/api/outreach/audit':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            url = data.get('url', '').strip()
            coverage = data.get('coverage', 'quick').strip()
            if not url:
                self._json(400, {'error': 'url is required'})
                return
            _tg_send(f"\U0001F50D <b>Auditing website...</b>\n<code>{h(url)}</code>")
            audit = lead_gen_outreach.audit_website(url, coverage)
            name = data.get('name', url)
            msg = lead_gen_outreach.format_audit_result(name, audit)
            _tg_send(msg, disable_preview=False)
            if audit['success']:
                self._json(200, {
                    'status': 'complete',
                    'url': url,
                    'time': audit.get('time', '?'),
                    'report_preview': audit['report'][:500],
                })
            else:
                self._json(400, {
                    'status': 'error',
                    'error': audit['error'],
                })
        elif parsed.path == '/api/linkedin/save':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            name = data.get('name', '').strip()
            url = data.get('url', '').strip()
            if not name or not url:
                self._json(400, {'error': 'name and url required'})
                return
            os.makedirs(os.path.dirname(LINKEDIN_CSV_PATH), exist_ok=True)
            existing_urls = set()
            if os.path.exists(LINKEDIN_CSV_PATH):
                with open(LINKEDIN_CSV_PATH, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        u = row.get('url', '').strip()
                        if u:
                            existing_urls.add(u)
            if url in existing_urls:
                self._json(200, {'status': 'duplicate', 'message': 'Lead already exists'})
                return
            row = {col: '' for col in LINKEDIN_COLUMNS}
            row['date'] = datetime.now().isoformat()
            row['source'] = 'linkedin_google_dork'
            row['status'] = 'new'
            matched = data.get('matched_products', [])
            if isinstance(matched, list):
                row['matched_products'] = '|'.join(matched)
            else:
                row['matched_products'] = str(matched)
            for key in LINKEDIN_COLUMNS:
                if key in data and data[key] not in (None, ''):
                    row[key] = str(data[key])
            file_exists = os.path.exists(LINKEDIN_CSV_PATH) and os.path.getsize(LINKEDIN_CSV_PATH) > 0
            with open(LINKEDIN_CSV_PATH, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=LINKEDIN_COLUMNS)
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)
            kb_score = data.get('kb_score', 0)
            try:
                score_val = float(kb_score)
            except (ValueError, TypeError):
                score_val = 0
            if score_val >= 8.0:
                token = TELEGRAM_TOKEN
                if token:
                    msg = f"\U0001F525 HIGH SCORE LinkedIn Lead: {name} | {data.get('headline', '')} | Score: {kb_score}/10\n\U0001F517 {url}"
                    payload = {
                        "chat_id": TELEGRAM_CHAT_ID,
                        "message_thread_id": TELEGRAM_THREAD_ID,
                        "text": msg,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    }
                    try:
                        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=10)
                    except Exception:
                        pass
            self._json(201, {'status': 'ok', 'saved': name, 'score': kb_score})
        elif parsed.path == '/api/extract-facebook':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            fb_url = data.get('url', '').strip()
            if not fb_url or 'facebook.com' not in fb_url:
                self._json(400, {'error': 'Valid Facebook URL required'})
                return
            try:
                # Playwright only \u2014 fast (~30s). For missing fields, user clicks "Try Apify" or fills manual.
                result = _extract_facebook_page(fb_url)
                if result is not None:
                    result['source'] = 'playwright'
                self._json(200, {'ok': True, 'data': result})
            except Exception as e:
                self._json(500, {'ok': False, 'error': str(e)})
        elif parsed.path == '/api/extract-facebook/apify':
            # Slower but more reliable \u2014 uses FB-internal API via Apify
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            fb_url = data.get('url', '').strip()
            if not fb_url or 'facebook.com' not in fb_url:
                self._json(400, {'error': 'Valid Facebook URL required'})
                return
            result = _extract_via_apify(fb_url, timeout=300)
            if result is None:
                self._json(500, {'ok': False, 'error': 'Apify extraction failed or timed out'})
                return
            result['source'] = 'apify'
            self._json(200, {'ok': True, 'data': result})
        elif parsed.path == '/api/extract-facebook/manual':
            # Manual save with user-supplied fields
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            url = data.get('url', '').strip()
            if not url:
                self._json(400, {'error': 'url required'})
                return
            result = {
                'url': url,
                'business_name': data.get('business_name', '').strip(),
                'category': data.get('category', '').strip(),
                'followers': data.get('followers', '').strip(),
                'email': data.get('email', '').strip(),
                'phone': data.get('phone', '').strip(),
                'website': data.get('website', '').strip(),
                'has_website': bool(data.get('website', '').strip()),
                'address': data.get('address', '').strip(),
                'last_post_date': data.get('last_post_date', '').strip(),
                'qualification_score': 5,
                'source': 'manual',
            }
            self._json(200, {'ok': True, 'data': result})
        elif parsed.path == '/api/extract-instagram':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            ig_url = data.get('url', '').strip()
            if not ig_url or 'instagram.com' not in ig_url:
                self._json(400, {'error': 'Valid Instagram URL required'})
                return
            try:
                result = _extract_instagram_page(ig_url)
                self._json(200, {'ok': True, 'data': result})
            except Exception as e:
                self._json(500, {'ok': False, 'error': str(e)})
        # \u2500\u2500 Auth POST endpoints \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        elif parsed.path == '/api/auth/register':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            name = data.get('name', '').strip()
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            if not name or not email or not password:
                self._json(400, {'error': 'name, email, and password required'})
                return
            if len(password) < 6:
                self._json(400, {'error': 'Password must be at least 6 characters'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            if c.fetchone():
                conn.close()
                self._json(409, {'error': 'Email already registered'})
                return
            h, salt = hash_password(password)
            now = datetime.now().isoformat()
            role = 'admin' if os.environ.get('ADMIN_EMAIL', '').lower() == email else 'user'
            if role == 'admin':
                code = 'verified'
                exp = now
            else:
                code = ''.join(secrets.choice(string.digits) for _ in range(6))
                exp = (datetime.now().timestamp() + 600)
            c.execute('''INSERT INTO users (name, email, password_hash, password_salt, role,
                         email_verified, verification_code, verification_expires, created_at, updated_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (name, email, h, salt, role,
                       1 if role == 'admin' else 0,
                       code, str(exp) if role != 'admin' else '',
                       now, now))
            user_id = c.lastrowid
            c.execute('INSERT INTO settings (user_id) VALUES (?)', (user_id,))
            conn.commit()
            token = create_session(user_id)
            conn.close()
            if role != 'admin':
                sent = send_verification_email(email, code)
            else:
                sent = False
            self._json(201, {'token': token,
                             'user': {'id': user_id, 'name': name, 'email': email, 'role': role,
                                      'email_verified': role == 'admin'},
                             'verification_sent': role != 'admin',
                             'message': 'Account created. Please verify your email.' if role != 'admin' else 'Account created.'})
        elif parsed.path == '/api/auth/verify-email':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user = require_auth(self)
            if not user: return
            code = data.get('code', '').strip()
            if not code:
                self._json(400, {'error': 'Verification code required'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT verification_code, verification_expires FROM users WHERE id = ?', (user['id'],))
            row = c.fetchone()
            if not row:
                conn.close()
                self._json(400, {'error': 'No verification pending'})
                return
            stored_code, expires_str = row
            if stored_code == 'verified':
                conn.close()
                self._json(200, {'status': 'already_verified'})
                return
            if stored_code != code:
                conn.close()
                self._json(400, {'error': 'Invalid verification code'})
                return
            if expires_str and float(expires_str) < time.time():
                conn.close()
                self._json(400, {'error': 'Verification code expired. Request a new one.'})
                return
            c.execute('UPDATE users SET email_verified = 1, verification_code = ? WHERE id = ?', ('verified', user['id']))
            conn.commit()
            conn.close()
            self._json(200, {'status': 'verified'})
        elif parsed.path == '/api/auth/resend-verification':
            user = require_auth(self)
            if not user: return
            if user.get('email_verified'):
                self._json(200, {'status': 'already_verified'})
                return
            code = ''.join(secrets.choice(string.digits) for _ in range(6))
            exp = str(datetime.now().timestamp() + 600)
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE users SET verification_code = ?, verification_expires = ? WHERE id = ?',
                      (code, exp, user['id']))
            conn.commit()
            conn.close()
            sent = send_verification_email(user['email'], code)
            self._json(200, {'status': 'resent' if sent else 'failed', 'message': 'Check your email' if sent else 'Failed to send. Try again later.'})
        elif parsed.path == '/api/auth/leads-remaining':
            user = require_auth(self)
            if not user: return
            limit = get_lead_limit(user)
            remaining = max(0, limit - user['leads_used'])
            self._json(200, {'leads_used': user['leads_used'], 'leads_limit': limit, 'leads_remaining': remaining, 'tier': user.get('subscription_tier', 'free')})
        elif parsed.path == '/api/auth/login':
            client_ip = self.client_address[0]
            now = time.time()
            if client_ip in _login_attempts:
                cnt, first = _login_attempts[client_ip]
                if now - first > LOGIN_RATE_WINDOW:
                    _login_attempts[client_ip] = [1, now]
                elif cnt >= LOGIN_RATE_LIMIT:
                    self._json(429, {'error': 'Too many login attempts. Try again in 15 minutes.'})
                    return
                else:
                    _login_attempts[client_ip][0] = cnt + 1
            else:
                _login_attempts[client_ip] = [1, now]
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            if not email or not password:
                self._json(400, {'error': 'Email and password required'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH, timeout=30)
            c = conn.cursor()
            c.execute('SELECT id, name, email, role, password_hash, password_salt, COALESCE(email_verified, 0), COALESCE(leads_used, 0), COALESCE(subscription_tier, "free") FROM users WHERE email = ?', (email,))
            row = c.fetchone()
            if not row:
                conn.close()
                self._json(401, {'error': 'Invalid email or password'})
                return
            if not verify_password(password, row[4], row[5]):
                conn.close()
                self._json(401, {'error': 'Invalid email or password'})
                return
            _login_attempts.pop(client_ip, None)
            print(f"[auth] LOGIN success: user={row[0]} email={email}", flush=True)
            token = create_session(row[0], conn)
            if not token:
                conn.close()
                print(f"[auth] Login FAILED: session creation returned None", flush=True)
                self._json(500, {'error': 'Failed to create session'})
                return
            conn.commit()
            conn.close()
            print(f"[auth] Login response: token={token[:20]}... user={row[1]}", flush=True)
            self._json(200, {'token': token, 'user': {'id': row[0], 'name': row[1], 'email': row[2], 'role': row[3], 'email_verified': bool(row[6]), 'leads_used': row[7], 'subscription_tier': row[8]}})
        elif parsed.path == '/api/auth/refresh':
            user = require_auth(self)
            if not user: return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            new_token = secrets.token_hex(32)
            auth = self.headers.get('Authorization', '')
            old = auth[7:] if auth.startswith('Bearer ') else ''
            if old:
                c.execute('UPDATE sessions SET token = ?, created_at = ? WHERE token = ?',
                          (new_token, datetime.now().isoformat(), old))
            else:
                new_token = create_session(user['id'])
            conn.commit()
            conn.close()
            user['email_verified'] = bool(user.get('email_verified'))
            self._json(200, {'token': new_token, 'user': user})
        elif parsed.path == '/api/auth/extension-token':
            self._json(200, {
                'instructions': 'GET your bearer token from /api/auth/refresh once, then paste into the extension popup to authorize it.',
                'how_to': 'In your browser, after logging into the web app, open DevTools and run: localStorage.getItem("token"). Paste that value into the extension popup.'
            })
            return
        elif parsed.path == '/api/user/preferences':
            user = require_auth(self)
            if not user: return
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            tg = data.get('telegram_notifications')
            if tg is None:
                self._json(400, {'error': 'telegram_notifications required'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('UPDATE users SET telegram_notifications = ? WHERE id = ?', (1 if tg else 0, user['id']))
            conn.commit()
            conn.close()
            self._json(200, {'telegram_notifications': bool(tg)})
        elif parsed.path == '/api/auth/logout':
            auth = self.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                token = auth[7:]
                conn = sqlite3.connect(AUTH_DB_PATH)
                c = conn.cursor()
                c.execute('DELETE FROM sessions WHERE token = ?', (token,))
                conn.commit()
                conn.close()
            self._json(200, {'status': 'logged_out'})
        elif parsed.path == '/api/auth/profile':
            user = require_auth(self)
            if not user: return
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            name = data.get('name', '').strip()
            email = data.get('email', '').strip().lower()
            if not name:
                self._json(400, {'error': 'Name is required'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            if email and email != user['email']:
                c.execute('SELECT id FROM users WHERE email = ? AND id != ?', (email, user['id']))
                if c.fetchone():
                    conn.close()
                    self._json(409, {'error': 'Email already in use'})
                    return
            now = datetime.now().isoformat()
            if email:
                c.execute('UPDATE users SET name = ?, email = ?, updated_at = ? WHERE id = ?', (name, email, now, user['id']))
            else:
                c.execute('UPDATE users SET name = ?, updated_at = ? WHERE id = ?', (name, now, user['id']))
            conn.commit()
            conn.close()
            self._json(200, {'status': 'updated', 'user': {'name': name, 'email': email or user['email']}})
        elif parsed.path == '/api/auth/forgot-password':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            email = data.get('email', '').strip().lower()
            if not email:
                self._json(400, {'error': 'Email required'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            row = c.fetchone()
            if not row:
                conn.close()
                self._json(200, {'status': 'sent', 'message': 'If that email is registered, a reset link has been sent.'})
                return
            token = secrets.token_hex(32)
            exp = str(time.time() + 3600)
            c.execute('UPDATE users SET password_reset_token = ?, password_reset_expires = ? WHERE id = ?', (token, exp, row[0]))
            conn.commit()
            conn.close()
            host = self.headers.get('Host', 'localhost:8800')
            sent = send_reset_email(email, token, host)
            self._json(200, {'status': 'sent' if sent else 'failed', 'message': 'If that email is registered, a reset link has been sent.' if sent else 'Failed to send email. Try again later.'})
        elif parsed.path == '/api/auth/reset-password':
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            token = data.get('token', '').strip()
            new_password = data.get('new_password', '')
            if not token or not new_password:
                self._json(400, {'error': 'token and new_password required'})
                return
            if len(new_password) < 6:
                self._json(400, {'error': 'Password must be at least 6 characters'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT id, password_reset_expires FROM users WHERE password_reset_token = ?', (token,))
            row = c.fetchone()
            if not row:
                conn.close()
                self._json(400, {'error': 'Invalid or expired reset token'})
                return
            if not row[1] or float(row[1]) < time.time():
                conn.close()
                self._json(400, {'error': 'Reset token expired. Request a new one.'})
                return
            h, salt = hash_password(new_password)
            c.execute('UPDATE users SET password_hash = ?, password_salt = ?, password_reset_token = NULL, password_reset_expires = NULL, updated_at = ? WHERE id = ?',
                      (h, salt, datetime.now().isoformat(), row[0]))
            conn.commit()
            conn.close()
            self._json(200, {'status': 'reset', 'message': 'Password updated successfully.'})
        elif parsed.path == '/api/auth/change-password':
            user = require_auth(self)
            if not user: return
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            if not old_password or not new_password:
                self._json(400, {'error': 'old_password and new_password required'})
                return
            if len(new_password) < 6:
                self._json(400, {'error': 'New password must be at least 6 characters'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT password_hash, password_salt FROM users WHERE id = ?', (user['id'],))
            row = c.fetchone()
            if not verify_password(old_password, row[0], row[1]):
                conn.close()
                self._json(401, {'error': 'Current password is incorrect'})
                return
            h, salt = hash_password(new_password)
            now = datetime.now().isoformat()
            c.execute('UPDATE users SET password_hash = ?, password_salt = ?, updated_at = ? WHERE id = ?', (h, salt, now, user['id']))
            conn.commit()
            conn.close()
            self._json(200, {'status': 'password_updated'})
        elif parsed.path == '/api/admin/users/delete':
            user = require_auth(self)
            if not user: return
            if user['role'] not in ('admin', 'super_admin'):
                self._json(403, {'error': 'Forbidden'})
                return
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            user_id = data.get('user_id')
            if not user_id:
                self._json(400, {'error': 'user_id required'})
                return
            if int(user_id) == user['id']:
                self._json(400, {'error': 'Cannot delete yourself'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT role FROM users WHERE id = ?', (user_id,))
            target_row = c.fetchone()
            if not target_row:
                conn.close()
                self._json(404, {'error': 'User not found'})
                return
            target_role = target_row[0]
            if user['role'] == 'admin' and target_role not in ('user', 'pro'):
                conn.close()
                self._json(403, {'error': 'Admins can only remove regular users'})
                return
            c.execute('DELETE FROM sessions WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM settings WHERE user_id = ?', (user_id,))
            c.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            self._json(200, {'status': 'deleted'})
        elif parsed.path == '/api/admin/users/role':
            user = require_auth(self)
            if not user: return
            if user['role'] not in ('admin', 'super_admin'):
                self._json(403, {'error': 'Forbidden'})
                return
            if data is None:
                self._json(400, {'error': 'Invalid JSON'})
                return
            target_id = data.get('user_id')
            new_role = data.get('role')
            if not target_id or new_role not in ('user', 'pro', 'admin', 'super_admin'):
                self._json(400, {'error': 'Invalid user_id or role'})
                return
            if int(target_id) == user['id']:
                self._json(400, {'error': 'Cannot change your own role'})
                return
            conn = sqlite3.connect(AUTH_DB_PATH)
            c = conn.cursor()
            c.execute('SELECT role FROM users WHERE id = ?', (target_id,))
            target_row = c.fetchone()
            if not target_row:
                conn.close()
                self._json(404, {'error': 'User not found'})
                return
            target_curr_role = target_row[0]
            if user['role'] == 'admin':
                if target_curr_role not in ('user', 'pro') or new_role not in ('user', 'pro'):
                    conn.close()
                    self._json(403, {'error': 'Admins can only toggle users between user and pro'})
                    return
            c.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, target_id))
            conn.commit()
            conn.close()
            self._json(200, {'status': 'updated'})
        else:
            self._json(404, {'error': 'Not found'})


# \u2500\u2500 Telegram Polling (incoming message handler) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
BOT_API = os.environ.get('TELEGRAM_BOT_API', 'http://localhost:8081/bot')
_last_update_offset = 0


def send_xlsx_document(chat_id, thread_id, xlsx_bytes, filename, caption):
    token = TELEGRAM_TOKEN
    if not token:
        return False
    try:
        url = f"{BOT_API}{token}/sendDocument"
        files = {'document': (filename, io.BytesIO(xlsx_bytes), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        data = {
            'chat_id': chat_id,
            'message_thread_id': thread_id,
            'caption': caption,
            'parse_mode': 'HTML',
        }
        resp = requests.post(url, data=data, files=files, timeout=30)
        ok = resp.json().get('ok', False)
        if ok:
            print(f"  XLSX sent: {filename} ({len(xlsx_bytes)} bytes)", flush=True)
        else:
            print(f"  sendDocument failed: {resp.json()}", flush=True)
        return ok
    except Exception as e:
        print(f"  sendDocument error: {e}", flush=True)
        return False


def get_last_n_leads_csv(n):
    today_path = get_daily_qualified_path()
    sources = []

    if os.path.exists(today_path):
        sources.append(('daily', today_path))
    if os.path.exists(QUALIFIED_CSV_PATH):
        sources.append(('qualified', QUALIFIED_CSV_PATH))
    if os.path.exists(CSV_PATH):
        sources.append(('all', CSV_PATH))

    for label, path in sources:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if rows:
            last_n = rows[-n:]
            with open(path, 'r', newline='', encoding='utf-8') as f:
                raw_header = f.readline().strip()
            fieldnames = [fn.strip().strip('"') for fn in raw_header.split(',')]
            out = io.StringIO()
            writer = csv.DictWriter(out, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            writer.writerows(last_n)
            csv_content = out.getvalue()
            xlsx_bytes = csv_to_xlsx_bytes(csv_content)
            return xlsx_bytes, label
    return None, None


def send_telegram_text(chat_id, thread_id, text):
    token = TELEGRAM_TOKEN
    if not token:
        return
    try:
        requests.post(f"{BOT_API}{token}/sendMessage", json={
            'chat_id': chat_id,
            'message_thread_id': thread_id,
            'text': text,
        }, timeout=10)
    except Exception as e:
        print(f"  sendMessage error: {e}", flush=True)


def get_today_leads():
    today = datetime.now().strftime('%Y-%m-%d')
    day_name = datetime.now().strftime('%A')
    daily_path = os.path.join(QUALIFIED_DIR, f'{today}_{day_name}.csv')

    if os.path.exists(daily_path):
        with open(daily_path, 'r', newline='', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
        return rows, daily_path

    if os.path.exists(CSV_PATH):
        rows = []
        with open(CSV_PATH, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('date', '').strip().startswith(today):
                    rows.append(row)
        return rows, CSV_PATH

    return [], None


CIRCLED_NUMS = ['\u2460', '\u2461', '\u2462', '\u2463', '\u2464', '\u2465', '\u2466', '\u2467', '\u2468', '\u2469',
                '\u246a', '\u246b', '\u246c', '\u246d', '\u246e', '\u246f', '\u2470', '\u2471', '\u2472', '\u2473']


def _has_real_website(row):
    hw = row.get('has_website', '').strip().lower()
    website = row.get('website', '').strip().lower()
    if hw != 'true' or not website:
        return False
    social_domains = ('tiktok.com', 'instagram.com', 'facebook.com', 'twitter.com',
                      'x.com', 'linkedin.com', 'youtube.com', 'youtu.be',
                      'pinterest.com', 'snapchat.com', 'threads.net')
    return not any(d in website for d in social_domains)


def format_today_count(rows):
    if not rows:
        return "No leads found today."

    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    month_day = today.strftime('%b %d')

    daily_path = os.path.join(QUALIFIED_DIR, f'{date_str}_{today.strftime("%A")}.csv')
    daily_path_abs = os.path.abspath(daily_path)

    lines = [
        '\U0001f4bb terminal',
        f'grep "^{date_str}" {daily_path_abs}',
        '',
        f'{len(rows)} leads today ({month_day}):',
        '',
    ]

    hot_count = 0
    for i, row in enumerate(rows):
        num = CIRCLED_NUMS[i] if i < len(CIRCLED_NUMS) else f'{i + 1}.'
        name = row.get('business_name', 'Unknown').strip() or 'Unknown'
        raw_date = row.get('date', '').strip()
        raw_qat = row.get('qualified_at', '').strip()
        found_time = raw_qat if not raw_date or len(raw_date) <= 10 else raw_date
        platform = row.get('platform', 'facebook').strip() or 'facebook'
        phone = row.get('phone', '').strip()
        phone_display = phone if phone else ''

        has_site = _has_real_website(row)
        if has_site:
            site_status = 'true'
        else:
            site_status = '\u274c no website'
            hot_count += 1

        lines.append(f'{num} {name} | {found_time} | {platform} | {site_status} | {phone_display}')

    lines.append('')
    lines.append(f'\U0001f525 {hot_count} hot leads (no website). Anything you want to do with these?')

    return '\n'.join(lines)


SMART_HUNT_SCRIPT = os.path.join(os.path.dirname(__file__), 'smart_hunt.py')
_pending_hunt = {}
_last_hunt_summary = {}


def _parse_hunt_output(stdout):
    lines = stdout.strip().split('\n')
    summary = []
    urls = []
    in_separator = False
    for line in lines:
        s = line.strip()
        if s.startswith('==='):
            in_separator = not in_separator
            continue
        if s.startswith('[') and '/22]' in s and '|' in s and 'http' in s:
            for p in s.split(' | '):
                if p.strip().startswith('http'):
                    urls.append(p.strip().rstrip('/'))
        elif any(k in s for k in ('Smart Hunt Complete', 'URLs found', 'Enriched', 'Saved leads', 'PREMIUM', 'HIGH', 'MEDIUM', 'Time', '\U0001F525', '\u2b50', '\U0001F7E1', '\u23ed')):
            summary.append(s)
    result = '\n'.join(summary)
    if urls:
        result += '\n\n' + '\n'.join(f'\u2022 {u}' for u in urls)
    return result if result else (stdout[:500] if stdout else 'No results.')


def _run_hunt(cat, chat_id, thread_id, extra_args, count):
    send_telegram_text(chat_id, thread_id, f"\U0001F50D Hunting <b>{cat}</b> for {count} lead(s)...")
    cmd = [sys.executable, SMART_HUNT_SCRIPT, '--category', cat, '--count', str(count)]
    cmd += extra_args
    print(f"  Running: {' '.join(cmd)}", flush=True)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        msg = _parse_hunt_output(result.stdout or '')
        send_telegram_text(chat_id, thread_id, msg)
        _last_hunt_summary[(chat_id, thread_id)] = msg
    except subprocess.TimeoutExpired:
        send_telegram_text(chat_id, thread_id, '\u23f1 Hunt timed out after 10 minutes.')
    except Exception as e:
        send_telegram_text(chat_id, thread_id, f'\u274c Hunt error: {e}')
        print(f"  Hunt error: {e}", flush=True)


def _resolve_cat(raw):
    r = raw.strip().lower()
    for alias, canon in CATEGORY_ALIASES.items():
        if r == alias.lower() or r == canon.lower():
            return canon
    for key in CATEGORY_QUERIES:
        if r == key.lower():
            return key
        display = CATEGORY_DISPLAY_NAMES.get(key, '').lower()
        if r == display:
            return key
    return None

def handle_dashboard_message(chat_id, thread_id, text):
    text_clean = text.strip().lower()
    text_raw = text.strip()

    # Greetings
    if re.match(r'^(?:hi|hello|hey|yo|assalamu|salam|sup|good\s+(?:morning|afternoon|evening))\b', text_clean):
        send_telegram_text(chat_id, thread_id,
            "Hey! \U0001F44B I can hunt leads by category, show today's finds, or export. "
            "Try \"find fashion leads\", \"how many today?\", or \"send csv\".")
        return

    # Export intent: send/give/export (all/last N) leads (csv/xlsx) \u2014 no category mentioned
    export = re.match(r'(?:give|send|export|get)\s+(?:me\s+)?(?:all|the\s+)?(?:last\s+)?(\d+)?\s*leads?(?:\s*(?:in|to|as)\s*(?:csv|xlsx|excel|file))?\s*$', text_clean)
    if not export:
        export = re.match(r'(?:last\s+)?(\d+)?\s*leads?(?:\s*csv|xlsx)?\s*$', text_clean)
    if export:
        n = int(export.group(1)) if export.group(1) else 200
        n = max(1, min(n, 200))
        xlsx_bytes, source_label = get_last_n_leads_csv(n)
        if xlsx_bytes is None:
            send_telegram_text(chat_id, thread_id, "No leads found yet.")
            return
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"leads_{today}.xlsx"
        source_map = {'daily': '\U0001F4CB Today\'s Qualified', 'qualified': '\U0001F4CB Qualified Master', 'all': '\U0001F4CB All Leads'}
        _chart_emoji = '\U0001F4CA'
        caption = f"{source_map.get(source_label, _chart_emoji)} \u2014 Last {n} leads ({today})"
        send_xlsx_document(chat_id, thread_id, xlsx_bytes, filename, caption)
        return

    # Find/hunt/search [category] (leads) \u2014 triggers smart hunt
    hunt_cat = re.match(r'(?:find|hunt|search|look\s+for)\s+(?:me\s+)?(?:for\s+)?(.+?)\s*(?:leads?|business(?:es)?|pages?)?\s*$', text_clean)
    if not hunt_cat:
        hunt_cat = re.match(r'^(.+?)\s*leads?\s*$', text_clean)
    if hunt_cat:
        raw_cat = hunt_cat.group(1).strip().lower()
        resolved = _resolve_cat(raw_cat)
        if not resolved:
            for key, display in CATEGORY_DISPLAY_NAMES.items():
                if raw_cat in display.lower() or display.lower() in raw_cat:
                    resolved = key
                    break
        if not resolved:
            for key in CATEGORY_QUERIES:
                if raw_cat in key.lower() or key.lower() in raw_cat:
                    resolved = key
                    break
        if resolved:
            _pending_hunt[(chat_id, thread_id)] = {'state': 'pick_count', 'cat': resolved, 'extra_args': []}
            send_telegram_text(chat_id, thread_id, f"\u2753 How many <b>{CATEGORY_DISPLAY_NAMES.get(resolved, resolved)}</b> leads? (1-100)")
            return
        cats = sorted(CATEGORY_QUERIES.keys())
        lines = [f"{i}) {CATEGORY_DISPLAY_NAMES.get(c, c)}" for i, c in enumerate(cats, 1)]
        send_telegram_text(chat_id, thread_id,
            f"Not sure about \"{raw_cat}\". Available:\n" + '\n'.join(lines) +
            "\nReply a number or name.")
        return

    # Number reply to pending hunt
    nums = [int(n) for n in re.findall(r'\d+', text_clean) if n.isdigit()]
    if (chat_id, thread_id) in _pending_hunt and nums:
        pending = _pending_hunt.pop((chat_id, thread_id))
        if pending.get('state') == 'pick_count':
            _run_hunt(pending['cat'], chat_id, thread_id, pending.get('extra_args', []), min(max(nums[0], 1), 100))
        return

    # "how many (leads) (today)?" / "count" / "total"
    if re.search(r'(?:how\s+many|count|total)', text_clean):
        rows, src = get_today_leads()
        msg = format_today_count(rows)
        send_telegram_text(chat_id, thread_id, msg)
        return

    # Fallback
    send_telegram_text(chat_id, thread_id,
        f"Not sure about \"{h(text_raw[:50])}\". Try:\n"
        f"\u2022 \"find fashion leads\" \u2014 hunt\n"
        f"\u2022 \"how many today?\" \u2014 count\n"
        f"\u2022 \"send csv\" \u2014 export")


def poll_dashboard():
    global _last_update_offset
    token = TELEGRAM_TOKEN
    if not token:
        return

    print("  Telegram polling started (Lead Gen Dashboard + Lead Finder)", flush=True)
    api = f"https://api.telegram.org/bot{token}"

    while True:
        try:
            resp = requests.get(f"{api}/getUpdates", params={
                'offset': _last_update_offset,
                'timeout': 30,
                'allowed_updates': ['message'],
            }, timeout=35)
            result = resp.json()

            if not result.get('ok'):
                time.sleep(3)
                continue

            for update in result.get('result', []):
                _last_update_offset = update['update_id'] + 1
                msg = update.get('message', {})
                chat = msg.get('chat', {})
                cid = str(chat.get('id', ''))
                tid = msg.get('message_thread_id')
                txt = msg.get('text', '')

                if cid == TELEGRAM_CHAT_ID and tid in (TELEGRAM_THREAD_ID, 382) and txt:
                    label = 'Dashboard' if tid == TELEGRAM_THREAD_ID else 'Lead Finder'
                    print(f"  \u2190 {label} message: {txt[:120]}", flush=True)
                    handle_dashboard_message(cid, tid, txt)

        except requests.Timeout:
            pass
        except Exception as e:
            print(f"  Polling error: {e}", flush=True)
            time.sleep(5)


if __name__ == '__main__':
    if not TELEGRAM_TOKEN:
        print("WARNING: TELEGRAM_TOKEN not set. Notifications disabled.", flush=True)

    ensure_csv()
    ensure_qualified_csv()
    _ensure_fcommerce_csv()
    init_auth_db()

    # Register Telegram bot commands
    if TELEGRAM_TOKEN:
        for api_base in (BOT_API, "https://api.telegram.org/bot"):
            try:
                requests.post(f"{api_base}{TELEGRAM_TOKEN}/deleteWebhook?drop_pending_updates=true", timeout=5)
                resp = requests.post(f"{api_base}{TELEGRAM_TOKEN}/setMyCommands", json={
                    "commands": [
                        {"command": "help", "description": "Show what I can do"},
                    ],
                }, timeout=10)
                if resp.json().get('ok'):
                    print(f"  Commands registered via {api_base}", flush=True)
                    break
            except Exception as e:
                print(f"  Command reg via {api_base} failed: {e}", flush=True)
                continue

        # DISABLED: conflicts with Hermes gateway polling (same bot token)
        # polling_thread = threading.Thread(target=poll_dashboard, daemon=True)
        # polling_thread.start()

    port = int(os.environ.get('PORT', 8800))
    server = ThreadingHTTPServer(('0.0.0.0', port), Handler)

    def _shutdown(signum, frame):
        print(f'\nReceived signal {signum}, shutting down gracefully...', flush=True)
        try:
            server.shutdown()
        except Exception:
            pass
        server.server_close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    print(f'Skarbol Lead Gen server running on http://0.0.0.0:{port}', flush=True)
    print(f'  DATABASE_URL: {"set" if os.environ.get("DATABASE_URL") else "not set (using SQLite)"}', flush=True)
    print(f'  ALLOWED_ORIGINS: {os.environ.get("ALLOWED_ORIGINS", "*")}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down\u2026', flush=True)
        server.server_close()
