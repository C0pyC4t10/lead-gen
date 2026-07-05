# Lead Gen — Technical Documentation

> Internal technical reference for the Lead Generation webapp at `https://lead-gen-phcw.onrender.com`.
> Last updated: July 5, 2026.

---

## 1. Architecture Overview

```
                        Browser
                           │
                           ▼
              ┌────────────────────────────┐
              │   Render (Docker container) │
              │                            │
              │  ┌──────────────────────┐  │
              │  │   ThreadingHTTPServer │  │  ← Single process, Python stdlib only
              │  │       (server.py)    │  │
              │  └─────────┬────────────┘  │
              │            │               │
              │  ┌─────────▼────────────┐  │
              │  │   Static HTML + JS   │  │  ← No frontend framework, vanilla
              │  │   (extract.html,     │  │
              │  │    leads.html, ...)  │  │
              │  └──────────────────────┘  │
              │            │               │
              │  ┌─────────▼────────────┐  │
              │  │   SQLite databases   │  │  ← Ephemeral (Render free tier)
              │  │   - auth.db          │  │     Auto-seeded on startup
              │  │   - leads.db         │  │
              │  └──────────────────────┘  │
              │                            │
              │  ┌──────────────────────┐  │
              │  │   External services  │  │
              │  │   - Apify (opt.)     │  │  ← FB page scraping via API
              │  │   - Telegram (opt.)  │  │  ← Lead notifications
              │  │   - Cloudinary (opt.)│  │  ← Image hosting
              │  │   - Gmail SMTP (opt.)│  │  ← Email verification
              │  └──────────────────────┘  │
              └────────────────────────────┘
                           │
                           ▼
                Facebook / Instagram
                (via Playwright + stealth)
```

**Core philosophy:** Zero-dependency stdlib HTTP server + lazy-loaded services. Runs on Render free tier (no Postgres/Redis needed). External services are optional and degrade gracefully.

---

## 2. Tech Stack

| Layer | Tech | Why |
|---|---|---|
| HTTP server | `ThreadingHTTPServer` (stdlib) | No framework overhead, works on free tier |
| Frontend | Vanilla HTML + JS + Tailwind CSS | No build step, served as static files |
| Database | SQLite 3 (stdlib) | File-based, persists across requests within a deploy |
| Password hashing | PBKDF2-HMAC-SHA256 (100k iters) | Stdlib `hashlib.pbkdf2_hmac` |
| Auth tokens | HMAC-SHA256 signed (stateless) | No session table needed |
| Browser automation | Playwright 1.x (sync API) | Chromium headless for FB extraction |
| FB page scraping (fallback) | Apify `facebook-pages-scraper` actor | Uses FB-internal API, bypasses bot detection |
| Deployment | Docker → Render free tier | Auto-deploy from GitHub `main` branch |
| Email | Gmail SMTP (optional) | Verification codes |
| Notifications | Telegram Bot API (optional) | Lead alerts |

---

## 3. File Layout

```
lead-gen/
├── server.py                  # Main app: HTTP server + all routes (3929 lines)
├── leads_db.py                # Leads SQLite layer (324 lines)
├── smart_hunt.py              # CLI lead-hunter (Serper → Apify → CSV)
├── build_demo.py              # Static-site builder for outreach demos
├── extract.html               # Extraction UI
├── leads.html                 # Leads dashboard
├── admin.html                 # Admin panel (user mgmt, stats)
├── profile.html               # User profile + Facebook cookies upload
├── login.html / register.html # Auth pages
├── Dockerfile                 # Render deployment image
├── render.yaml                # Render service config + env vars
├── requirements.txt           # Python deps
├── fb_cookies.json            # (gitignored) User-uploaded FB cookies
├── auth.db                    # (gitignored) Auto-seeded user database
└── leads.db                   # (gitignored) Leads database
```

---

## 4. Auth System

### 4.1 Password Storage

- Hashing: PBKDF2-HMAC-SHA256, 100,000 iterations, 32-byte salt, 32-byte hash
- Storage format: `pbkdf2_sha256$100000$<salt_b64>$<hash_b64>`
- Verification: `hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)`

### 4.2 Stateless Tokens

Login/registration returns an HMAC-SHA256 signed token containing `{user_id, email, role, exp}`:

```
token = base64url(payload) + "." + base64url(HMAC-SHA256(secret, payload))
```

- **Secret:** Derived from `AUTH_DB_PATH` path hash (or `AUTH_SECRET` env var)
- **Expiry:** 30 days from issue
- **Storage:** Client-side (localStorage / cookies)
- **Verification:** Zero DB queries — pure HMAC check

**Why stateless?** Render's free tier filesystem resets on every deploy. Session tables would log out all users on every redeploy. HMAC tokens survive any server restart.

### 4.3 Auth DB Auto-Seeding

`auth.db` is **NOT** tracked in git (`.gitignore`). On startup, `_seed_default_users()` checks if the `users` table is empty and inserts:
- `jahid.skarbol@gmail.com` (super admin, password: `Jahid@17`)
- `xahidjoy1@gmail.com` (admin, password: `Jahid@17`)

This prevents accidental `git add -A` overwrites of password hashes.

### 4.4 Auth Endpoints

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/auth/register` | `{email, password, name}` | `{token, user}` |
| POST | `/api/auth/login` | `{email, password}` | `{token, user}` |
| POST | `/api/auth/logout` | — | `{ok: true}` |
| GET | `/api/auth/me` | (token in header) | `{user}` |
| POST | `/api/auth/refresh` | (token in header) | `{token, user}` |
| POST | `/api/auth/forgot-password` | `{email}` | `{ok: true}` |
| POST | `/api/auth/reset-password` | `{token, new_password}` | `{ok: true}` |

Token format: `Authorization: Bearer <token>` or `X-Auth-Token: <token>`

---

## 5. Storage Layer

### 5.1 `auth.db` (auto-seeded)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',  -- 'user', 'admin', 'super_admin'
    email_verified INTEGER DEFAULT 0,
    created_at TEXT,
    last_login TEXT,
    telegram_chat_id TEXT,
    telegram_enabled INTEGER DEFAULT 0
);
```

### 5.2 `leads.db` (`leads_db.py`)

Two tables — `leads` and `qualified_leads` (latter is the user's "starred" subset). Both have ~24 columns including: `date`, `platform`, `business_name`, `page_url`, `category`, `followers`, `email`, `phone`, `website`, `address`, `qualification_score`, `status`, `user_id`.

Indexes: `page_url`, `status`, `user_id` for fast filtering.

### 5.3 Optional Cloud Sync

`mongo_db.py` and `cloudinary_storage.py` are optional modules — if MongoDB / Cloudinary env vars are set, leads and images sync to cloud storage. Falls back to local-only if absent.

---

## 6. Facebook Extraction Pipeline

This is the most complex part of the system. Three layers, in order of preference:

### 6.1 Layer 1: Playwright Headless Browser

**Architecture:**
- `_PLAYWRIGHT_LOCAL = threading.local()` — each thread gets its own browser instance (avoids greenlet errors)
- `_get_browser()` lazy-creates a Chromium browser on the current thread
- `_new_page()` creates a fresh `BrowserContext` + `Page` from the thread's browser
- Each extraction gets its own context (lightweight, isolated) → context is closed in `finally`
- Browser stays open across requests → saves 5–8s startup overhead per extraction

**Stealth patches** (`_stealth_init_script()`):
- `navigator.webdriver = false`
- `navigator.plugins` fake array
- `navigator.languages = ['en-US', 'en']`
- `window.chrome` object present
- `permissions.query` patched to deny `notifications` without prompt
- Launch arg `--disable-blink-features=AutomationControlled`

**Cookies layer** (optional, user-uploaded):
- User uploads cookies via `/profile` → stored in `fb_cookies.json`
- `_load_fb_cookies()` loads and caches them
- `_apply_fb_cookies(ctx)` injects cookies into the browser context
- If cookies present, Facebook serves logged-in content (full phone/email/website)

**Extraction strategy** (`_extract_facebook_page()`):
1. **LD+JSON scan** — Read `<script type="application/ld+json">` tags for structured `telephone`, `email`, `url`, `address`
2. **Scroll loop** — Scroll down + up 5× to trigger lazy-loaded content
3. **Main JS extraction** — Pull `tel:` links, contact sections (`ProfileCards`, `PageHeader`), regex match emails/phones in `innerText`
4. **`/about` page** — Navigate to `<page>/about` for detailed contact info
5. **`mbasic.facebook.com` fallback** — Text-only interface, harder to block, regex-extract phone/website from rendered text

**Phone validation** (`looksReal()` JS function):
- Reject all-zeros, repeating digits (`1111111`)
- Reject repeating triplets (`123123123`)
- Reject repeating half (`12121212`)
- Format: normalize to `+8801XXXXXXXXX`

**Early exit:** Skip remaining passes once phone + email + website all found.

**Timeouts (total ≤ ~25s per extraction):**
- Main page load: 15s
- Selector wait: 5s
- `/about` page: 8s load + 1.5s × 3 waits
- mbasic: 10s load + 1s wait

### 6.2 Layer 2: Apify Fallback

`/api/extract-facebook/apify` uses Apify actor `apify~facebook-pages-scraper` which calls Facebook's internal API.

**Flow:**
1. POST `/v2/acts/{actor_id}/runs` with `{startUrls: [{url}], maxPagesPerQuery: 1}`
2. Poll `/v2/actor-runs/{run_id}` every 2s for `SUCCEEDED` status (max 60s timeout)
3. GET `/v2/actor-runs/{run_id}/dataset/items`
4. Map fields: `title`→`business_name`, `phone`, `email`, `website`, `address`, `categories[0]`→`category`, `likes`→`followers`
5. Normalize phone to `+880XXXXXXXXX`, lowercase email

**Why Apify as fallback:** Uses FB internal API, not headless browser → bypasses bot detection → reliably returns phone/website even for pages that Playwright fails on.

**Env:** `APIFY_API_KEY` must be set in Render dashboard (added to `render.yaml` as `sync: false`).

### 6.3 Layer 3: Manual Override

UI shows "Manual Override" card after extraction. User can type in any missing field and save → `POST /api/leads` accepts the manual values directly.

---

## 7. Cookies Upload System

**Problem:** Facebook serves stripped pages to logged-out headless browsers. With cookies, the page renders as if a real user is logged in.

**Flow:**
1. User installs browser extension (e.g., "Cookie-Editor")
2. Visits `facebook.com`, exports cookies as JSON
3. Goes to `/profile` → pastes JSON → clicks Save
4. Server stores in `fb_cookies.json` (gitignored, ephemeral)
5. Next extraction: `_load_fb_cookies()` reads → `_apply_fb_cookies(ctx)` injects into Playwright context
6. Facebook now serves full content with phone/email/website

**Endpoints:**
- `POST /api/cookies/facebook` — accepts cookies JSON
- `GET /api/cookies/status` — returns `{has_cookies: bool, count: int}`

**Cookie format expected** (from Cookie-Editor extension):
```json
[
  {"name": "c_user", "value": "100012345", "domain": ".facebook.com", "path": "/"},
  {"name": "xs", "value": "...", "domain": ".facebook.com", "path": "/"},
  ...
]
```

---

## 8. Smart Hunt (CLI Pipeline)

`smart_hunt.py` — automated lead hunter. Pipeline:

```
Serper.dev search (Google site:facebook.com)
       ↓
Facebook page URLs (5-50 per category)
       ↓
Apify enrichment (phone, email, website, followers, posts)
       ↓
Engagement scoring (post count, ad activity, response time, etc.)
       ↓
Save to leads.db (only if score >= min-score)
```

**Categories (28):** skincare, cosmetics, fashion, boutique, jewelry, perfume, baby, bags, home, food, fruit, nursery, clothing_brand, jewelry_watches, bags_luggage, health_beauty, cosmetics_store, personal_care, home_decor, kitchen_cooking, furniture_store, patio_garden, electronics, games_toys, outdoor_sporting, food_beverage, bakery, specialty_grocery

**Scoring (0–22):**
- 18–22: PREMIUM (high-value lead)
- 14–17: HIGH
- 10–13: MEDIUM
- <10: skipped

**Usage:**
```bash
python3 smart_hunt.py --category beauty --count 30 --min-score 14
python3 smart_hunt.py --category all --dry-run
python3 smart_hunt.py --flush-cache   # if server was offline during hunt
```

**Cache:** If `server` is unreachable, leads are saved to `pending_leads_cache.json` and `--flush-cache` uploads them when server is back online.

---

## 9. API Endpoints (Public)

### Leads
| Method | Path | Description |
|---|---|---|
| GET | `/api/leads` | List user's leads (paginated, filterable) |
| POST | `/api/leads` | Save a new lead |
| PUT | `/api/leads/{id}` | Update a lead |
| DELETE | `/api/leads/{id}` | Soft-delete (sets `deleted_at`) |
| POST | `/api/leads/{id}/restore` | Restore from trash |
| POST | `/api/leads/bulk-delete` | Bulk soft-delete |
| GET | `/api/leads/export?format=csv\|xlsx` | Export user leads |

### Extraction
| Method | Path | Description |
|---|---|---|
| POST | `/api/extract-facebook` | Playwright extraction (fast, ~20–30s) |
| POST | `/api/extract-facebook/apify` | Apify extraction (slower, ~30–60s, more reliable) |
| POST | `/api/extract-instagram` | Instagram extraction (Playwright) |

### Search & Discovery
| Method | Path | Description |
|---|---|---|
| POST | `/api/search/serper` | Google search via Serper.dev |
| POST | `/api/search/maps` | Google Maps search |
| POST | `/api/search/facebook` | Facebook search (via Serper) |

### Cookies
| Method | Path | Description |
|---|---|---|
| POST | `/api/cookies/facebook` | Upload FB cookies JSON |
| GET | `/api/cookies/status` | Check cookie status |
| DELETE | `/api/cookies/facebook` | Clear stored cookies |

### Admin
| Method | Path | Description |
|---|---|---|
| GET | `/api/admin/users` | List all users |
| POST | `/api/admin/users/{id}/role` | Change user role |
| DELETE | `/api/admin/users/{id}` | Delete user |
| GET | `/api/admin/stats` | System-wide statistics |

---

## 10. Deployment (Render Free Tier)

### 10.1 Dockerfile

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium fonts-liberation libnss3 libatk-bridge2.0-0 libgtk-3-0 libgbm1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install playwright requests openpyxl && playwright install chromium
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV PORT=10000
EXPOSE 10000
CMD ["python", "server.py"]
```

### 10.2 `render.yaml`

Defines web service with env vars. Critical env vars:
- `AUTH_SECRET` — for HMAC tokens (auto-derived if absent)
- `APIFY_API_KEY` — **must be set manually** in Render dashboard (`sync: false`)
- `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID` — optional, for lead notifications
- `SERPER_API_KEY` — for `smart_hunt.py`
- `MONGO_URL`, `CLOUDINARY_*` — optional cloud sync

### 10.3 Free Tier Limitations

- **Ephemeral filesystem:** `auth.db`, `leads.db`, `fb_cookies.json` reset on every deploy
- **Mitigation:** Auth tokens are stateless (survive resets); `auth.db` auto-seeds default users; user-uploaded cookies need to be re-uploaded after deploy
- **Cold starts:** First request after 15 min idle takes ~30s (Render sleeps free instances)

### 10.4 Manual Deploy

1. Push to `main` on GitHub
2. Render dashboard → Manual Deploy → Deploy latest commit
3. Wait ~3–5 min for build + restart

---

## 11. Operational Notes

### Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| `_new_page is not defined` | Old `server.py` without the shared-browser refactor | Pull latest from `main` |
| `Cannot switch to a different thread (greenlet)` | Playwright sync API bound to wrong thread | Fixed via `threading.local()` (commit `3e27b61`) |
| Login fails on deploy | `auth.db` was wiped by `git add -A` | `auth.db` is gitignored + auto-seeded |
| Empty extraction results | FB stripped page (bot detection) | User uploads cookies at `/profile` |
| Apify returns null | `APIFY_API_KEY` not set on Render | Add it manually in dashboard |
| Server cold start (30s) | Free tier sleeps after 15 min idle | Render free-tier limitation |

### Backup & Recovery

- **Database backups:** All SQLite files in `/home/skarbolt/kb/lead-gen/*.db`
- **Cookies:** `fb_cookies.json` (re-export from browser if lost)
- **Source code:** GitHub `main` branch (always pull from there)

---

## 12. Development

### Local Setup

```bash
cd /home/skarbolt/kb/lead-gen
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env   # fill in APIFY_API_KEY etc.
python server.py       # serves on http://localhost:10000
```

### Testing Auth Locally

```bash
# Login
curl -X POST http://localhost:10000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jahid.skarbol@gmail.com","password":"Jahid@17"}'

# Use the returned token
curl http://localhost:10000/api/auth/me \
  -H "Authorization: Bearer <token>"
```

### Testing Extraction Locally

```bash
# Playwright
curl -X POST http://localhost:10000/api/extract-facebook \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"url":"https://www.facebook.com/kitchenkiw"}'

# Apify
curl -X POST http://localhost:10000/api/extract-facebook/apify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"url":"https://www.facebook.com/kitchenkiw"}'
```

---

## 13. Security

- **Passwords:** PBKDF2-SHA256 with 100k iterations + 32-byte random salt (industry standard)
- **Tokens:** HMAC-SHA256 signed, 30-day expiry, stateless (cannot be revoked pre-expiry but expires automatically)
- **Cookies (client-side):** Stored in localStorage; sent as `Authorization: Bearer` header
- **CSRF:** Stateless tokens in `Authorization` header (not auto-sent by browser → immune to CSRF)
- **SQLite:** Parameterized queries throughout (`?` placeholders)
- **Admin actions:** Role check on every endpoint (`role IN ('admin', 'super_admin')`)

### Known Limitations

- Tokens cannot be individually revoked before expiry (mitigation: short 30-day expiry)
- No rate limiting on extraction endpoints (relies on Render free tier's natural throttling)
- No HTTPS-only cookie flag (relying on Render's TLS termination)

---

## 14. Future Improvements

- [ ] Move auth.db to Supabase / Render Postgres (persistent across deploys)
- [ ] Add proper refresh tokens (currently just re-issue access tokens)
- [ ] Async Playwright API for better concurrency
- [ ] Per-user extraction rate limits
- [ ] Token revocation list (Redis or DB)
- [ ] Bulk extraction API (process N URLs in parallel)
- [ ] Frontend framework (React/Vue) — currently vanilla HTML/JS