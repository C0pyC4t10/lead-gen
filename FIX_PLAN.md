# Scraven Fix Plan — Comprehensive Audit & Roadmap

> **App**: Lead extraction SaaS (Facebook/Instagram)  
> **Brand**: Scraven — "The Hunter"  
> **Stack**: Python static server (server.py) + vanilla HTML/CSS/JS  
> **Date**: 2026-07-03

---

## Table of Contents

1. [Phase 0 — Critical Bugs (Fix Now)](#phase-0--critical-bugs-fix-now)
2. [Phase 1 — UX & Design Issues](#phase-1--ux--design-issues)
3. [Phase 2 — Authentication & Verification System](#phase-2--authentication--verification-system)
4. [Phase 3 — RBAC & Sub-Admin System](#phase-3--rbac--sub-admin-system)
5. [Phase 4 — Full Admin Panel](#phase-4--full-admin-panel)
6. [Phase 5 — Profile & Avatar System](#phase-5--profile--avatar-system)
7. [Phase 6 — Advanced Features (Industry Research)](#phase-6--advanced-features)
8. [Architecture Recommendations](#architecture-recommendations)
9. [Reference: Industry Patterns](#reference-industry-patterns)

---

## Phase 0 — Critical Bugs (Fix Now)

### 0.1 Avatar CSS mismatch (extract.html, leads.html)

**Status**: ✅ **Done** — `.avatar` already renamed to `avatar-circle`.

### 0.2 "Skarbol Tech" in extract footer

**Status**: ✅ **Done** — Footer now reads "Scraven".

### 0.3 Pricing page `.lead-badge` CSS after media queries

**Status**: ✅ **Done** — `.lead-badge` CSS is properly placed.

---

## Phase 1 — UX & Design Issues

### 1.1 Page title consistency

| Current | Should be |
|---------|-----------|
| `Pricing — Scraven` | `Scraven — Pricing` |

### 1.2 Missing footer on pricing page

All other pages have a footer. Pricing page ends abruptly after FAQ. Add:

```html
<div class="footer">
  <span class="brand-name">Scraven</span> &mdash; The Hunter
</div>
```

### 1.3 Extract page uses `100vh` instead of `100dvh`

**Status**: ✅ **Done** — extract.html uses `100dvh`.

### 1.4 Profile save — no disabled state on inputs during save

**Status**: ✅ **Done** — `setLoading()` disables `#name`, `#email`, `#btnSaveProfile` during save. `setLoadingPassword()` similarly disables password fields.

### 1.5 Admin stats — silent failure on missing CSV

**Status**: ✅ **Done** — Added `handleUnauthorized`, `addRetryButton`, loading/error/success status messages, partial data resilience, JSON parse safety, retry button, delete-button disabled state, `.btn-glow` and `.status-msg.success` CSS.

---

## Phase 2 — Authentication & Verification System

### Current Architecture

```
POST /api/auth/register        → Creates user, sends 6-digit code via SMTP
POST /api/auth/verify-email    → Verifies code (6 digits, 10min expiry)
POST /api/auth/resend-verification → Resends code
POST /api/auth/login           → Returns JWT-like token + user object
POST /api/auth/logout          → Invalidates session
POST /api/auth/change-password → Requires old + new password
POST /api/auth/profile         → Updates name/email
GET  /api/auth/me              → Returns current user from token
GET  /api/auth/leads-remaining → Returns used/limit/remaining/tier
```

### Issues & Improvements

#### 2.1 Password Reset (Forgot Password) — Missing

**Why needed**: Users can't reset password without admin intervention.

**Implementation**:
```
POST /api/auth/forgot-password  → Sends reset link with token
POST /api/auth/reset-password   → Validates reset token + sets new password
```

Add a `password_reset_token` and `password_reset_expires` column to users table. Reset token is a random 32-char hex string, 1-hour expiry. Email contains a link like `/reset-password?token=xxx`.

#### 2.2 Rate limiting on login

**Why needed**: Prevent brute force attacks.

**Implementation**: Track failed attempts per IP in-memory (or `settings` table). Lockout after 5 failed attempts for 15 minutes.

#### 2.3 Session expiry / refresh

Current tokens never expire. Add:
- Token `created_at` timestamp
- Session expiry (30 days by default)
- `/api/auth/refresh` endpoint
- Auto-refresh on page load if token is close to expiry

#### 2.4 Email verification improvements

- Add resend cooldown (60s between resends)
- Show "resend available in Xs" countdown on verify banner
- Auto-submit verification code when 6 digits entered

#### 2.5 Two-factor authentication (future)

For admin accounts: TOTP-based 2FA using `pyotp` library.

---

## Phase 3 — RBAC & Sub-Admin System

### Current Role System

```
Roles: 'user', 'admin', 'super_admin'
```

Only two levels. No granularity. Sub-admin not possible.

### Proposed RBAC Architecture

#### 3.1 Permission Model

Use a resource:action permission model:

```
leads:read
leads:create
leads:edit
leads:delete
leads:export
users:read
users:create
users:edit
users:delete
settings:read
settings:edit
billing:read
billing:edit
admin:access
```

#### 3.2 Role Definitions

| Role | Permissions | Scope |
|------|------------|-------|
| `super_admin` | All permissions | Global |
| `admin` | All except `admin:access` + `settings:edit` | Global |
| `sub_admin` | `leads:*`, `users:read`, `users:create` | Limited |
| `support` | `users:read`, `leads:read` | Read-only |
| `manager` | `leads:*`, `users:read`, `reports:read` | Department |
| `user` | `leads:read`, `leads:create` | Self only |
| `viewer` | `leads:read` | Read-only |

#### 3.3 Database Schema

```sql
CREATE TABLE roles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  description TEXT,
  permissions TEXT NOT NULL,  -- JSON array of permission strings
  created_at TEXT DEFAULT (datetime('now'))
);

ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id);
ALTER TABLE users ADD COLUMN created_by INTEGER REFERENCES users(id);
ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1;
```

#### 3.4 Admin UI for Role Management

New admin pages:
- `/admin/roles` — List, create, edit roles
- `/admin/users/{id}` — User detail with role assignment, status toggle
- `/admin/users/create` — Create user with role select

#### 3.5 Permission Checking

Centralized `check_permission(user, permission)` function:

```python
def check_permission(user, permission):
    role = get_role(user['role_id'])
    perms = json.loads(role['permissions'])
    if '*' in perms or permission in perms:
        return True
    # Check wildcard: 'leads:*' matches 'leads:read'
    resource = permission.split(':')[0]
    if f'{resource}:*' in perms:
        return True
    return False
```

#### 3.6 Sub-Admin Creation Flow

1. Admin clicks "Create Sub-Admin" in admin panel
2. Fills email, name, selects role (dropdown of non-super-admin roles)
3. System generates temporary password, sends welcome email
4. Sub-admin logs in, forced to change password
5. Sub-admin can manage users only within their permission scope

---

## Phase 4 — Full Admin Panel

### Current State

```
/admin              → Stats cards + user table (read-only)
/api/admin/stats    → total_leads, total_users, statuses
/api/admin/users    → List users
/api/admin/users/delete → Remove user
```

### Full Admin Panel Roadmap

#### 4.1 Dashboard (Phase 4.1)

- [ ] **Stats cards** — Total users, total leads, new today, qualified today, conversion rate
- [ ] **Charts** — Lead acquisition over time (last 7/30 days), status distribution pie chart
- [ ] **Recent activity** — Last 10 actions (new registrations, lead saves, exports)
- [ ] **Quick actions** — Create user, view reports, system settings

#### 4.2 User Management (Phase 4.2)

- [ ] **User table** — Search by name/email, sort by any column, pagination (20 per page)
- [ ] **User detail page** — View profile, leads used, subscription tier, created date, last login
- [ ] **User actions** — Edit role, reset password, toggle active/ban, delete user (with confirmation + soft delete)
- [ ] **Bulk actions** — Select multiple users, assign role, export CSV
- [ ] **Impersonation** — Login as user (with audit trail)

#### 4.3 Lead Management (Phase 4.3)

- [ ] **Lead table** — All leads with search, filter (by status/date/platform), sort, pagination
- [ ] **Lead detail** — View full lead info, edit fields, change status
- [ ] **Bulk operations** — Delete, export, change status
- [ ] **Duplicate detection** — Show/manage duplicates

#### 4.4 Subscription & Billing (Phase 4.4)

- [ ] **Plan table** — Users by plan (guest/free/pro), upgrade/downgrade
- [ ] **Usage stats** — Leads used per user, storage usage
- [ ] **Manual actions** — Grant Pro, extend limits, apply discounts

#### 4.5 Audit Log (Phase 4.5)

```sql
CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER,
  action TEXT NOT NULL,        -- e.g. 'user.login', 'lead.delete', 'admin.role_change'
  target_type TEXT,            -- 'user', 'lead', 'role'
  target_id INTEGER,
  details TEXT,                -- JSON with before/after state
  ip_address TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
```

- [ ] Log all sensitive actions: login, logout, profile change, role change, user creation/deletion, lead deletion, export
- [ ] Admin audit log viewer with filters (user, action, date range)

#### 4.6 System Settings (Phase 4.6)

- [ ] **Limits config** — Guest lead limit, free lead limit, Pro price
- [ ] **SMTP settings** — Gmail user/pass (currently in .env)
- [ ] **Feature flags** — Toggle Instagram extraction, LinkedIn, bulk mode
- [ ] **Announcement banner** — Set message shown to all users

---

## Phase 5 — Profile & Avatar System

### 5.1 Profile Picture Upload

**Implementation**:

```
POST /api/auth/avatar        → Upload image (multipart/form-data)
GET  /api/auth/avatar/{id}   → Serve avatar image
DELETE /api/auth/avatar      → Remove avatar
```

**Storage**:
- Store in `avatars/{user_id}.jpg` on disk
- Max file size: 2MB
- Allowed formats: JPEG, PNG, WebP
- Resize to 256x256 on upload

**UI**:
- Profile page: clickable avatar area with camera overlay
- Preview before upload
- Crop option (simple JS canvas crop)
- Update nav avatar immediately after upload

### 5.2 Profile Enhancements

- [ ] **Timezone selector**
- [ ] **Notification preferences** (email on lead saved, export ready)
- [ ] **API key management** (for programmatic access)
- [ ] **Account deletion** (self-serve with confirmation)

---

## Phase 6 — Advanced Features

### 6.1 Email Templates (Branded)

Currently verification email is plain text with basic HTML. Move to:

- [ ] HTML email templates for: verification, welcome, password reset, password changed, lead export ready
- [ ] Brand colors, logo, Scraven styling
- [ ] Preview in admin panel

### 6.2 Webhook System

For integration with external tools:

- [ ] Webhook on lead created, lead qualified, user registered
- [ ] Configurable per user via admin panel
- [ ] Retry with exponential backoff

### 6.3 Export Enhancements

- [ ] Scheduled exports (daily/weekly email)
- [ ] Export to Google Sheets (OAuth)
- [ ] Export to Salesforce/CRM (API)

### 6.4 Rate Limiting & Abuse Prevention

- [ ] Per-IP rate limiting on auth endpoints
- [ ] Per-user rate limiting on extract endpoints
- [ ] CAPTCHA on registration (after 3 failed attempts)
- [ ] Request logging for abuse analysis

### 6.5 Multi-language / i18n

- [ ] English + Bengali (primary market is Bangladesh)
- [ ] Locale detection from browser
- [ ] Admin panel for managing translations

---

## Architecture Recommendations

### 7.1 Framework Migration

Current Python static server + inline HTML/CSS/JS is not maintainable at scale. Consider:

| Option | Pros | Cons |
|--------|------|------|
| Stay with server.py | Already works, fast iteration | No framework, manual routing, no ORM |
| Flask/FastAPI | Clean routing, middleware, ecosystem | Requires rewrite |
| Next.js (partial done) | Full-stack, SSR, API routes | Already abandoned once |

**Recommendation**: Keep server.py for now. Migrate auth to a proper database ORM (SQLAlchemy) and use a web framework (FastAPI) when time permits.

### 7.2 Database

Current: SQLite at `auth.db`. For production:

- [ ] Migrate to PostgreSQL
- [ ] Add connection pooling
- [ ] Implement proper migrations (Alembic)

### 7.3 Security

- [ ] **CSRF protection** — Add CSRF tokens to all mutating requests
- [ ] **CORS** — Restrict to known origins
- [ ] **Rate limiting** — Per-IP + per-user
- [ ] **Password policy** — Min 8 chars, require uppercase + number
- [ ] **HTTPS enforcement** — Redirect all HTTP to HTTPS
- [ ] **Security headers** — CSP, X-Frame-Options, X-Content-Type-Options

### 7.4 Monitoring

- [ ] Request logging middleware
- [ ] Error tracking (Sentry or similar)
- [ ] Uptime monitoring
- [ ] Usage analytics dashboard

---

## Reference: Industry Patterns

### Common Lead Gen SaaS Features

Based on research of tools like Zoho CRM, PipeDrive, Keap, and SalesExec:

| Feature | Our Status | Industry Standard |
|---------|-----------|------------------|
| Lead capture from social | ✅ Basic FB/IG | ✅ FB, IG, LinkedIn, Twitter, Google Maps |
| Lead scoring | ✅ Basic (0-10) | ✅ AI-powered predictive scoring |
| Email verification | ✅ SMTP check | ✅ ZeroBounce/NeverBounce integration |
| Duplicate detection | ✅ URL-based | ✅ Fuzzy matching (name + phone + email) |
| Bulk extraction | ❌ | ✅ CSV upload, batch URL processing |
| Export formats | ✅ XLSX, PDF, TXT, MD | ✅ + CSV, Google Sheets, Salesforce |
| CRM integration | ❌ | ✅ HubSpot, Salesforce, Zoho |
| Email campaigns | ❌ | ✅ Built-in mailer + templates |
| Team collaboration | ❌ | ✅ Shared leads, comments, assignments |
| Mobile app | ❌ | ✅ iOS + Android |
| API | ✅ Basic | ✅ Full REST + Webhooks |
| RBAC | ❌ Basic | ✅ Granular roles + permissions |
| Audit log | ❌ | ✅ Full activity trail |
| Multi-tenant | ❌ Single DB | ✅ Isolated tenant data |
| White-label | ❌ | ✅ Custom domain, logo, colors |

### RBAC Patterns (from industry research)

1. **Simple roles** — admin/user/viewer (our current)
2. **Permission-based** — Decouple roles from permissions (our target)
3. **Role hierarchy** — Inherit permissions from parent roles (future)
4. **Org-scoped** — User is admin in Org A, viewer in Org B (multi-tenant future)

### Admin Panel Modules (industry standard)

Per Endurance Softwares, Sequenzy, and PyColors guides:

1. **User management** — Search, view, block, impersonate, reset
2. **Billing & subscriptions** — Plan changes, invoices, trials, refunds
3. **Support tools** — User context, activity timeline, error logs
4. **Content/config** — Feature flags, announcements, system settings
5. **Moderation** — Review flagged content, safe destructive actions
6. **Operations** — Queues, escalations, batch jobs
7. **Audit** — Log viewer, compliance reports, data exports

---

## Implementation Priority

| Priority | Phase | Effort | Impact |
|----------|-------|--------|--------|
| P0 | 0 — Critical bugs | 10 min | High |
| P0 | 2.1 — Password reset | 2 hrs | High |
| P1 | 3 — RBAC + sub-admin | 8 hrs | High |
| P1 | 4.1 — Admin dashboard | 4 hrs | Medium |
| P2 | 4.2 — User management | 6 hrs | Medium |
| P2 | 5 — Avatar/profile | 3 hrs | Medium |
| P2 | 2.2 — Rate limiting | 2 hrs | Medium |
| P3 | 4.5 — Audit log | 4 hrs | Medium |
| P3 | 6.1 — Email templates | 2 hrs | Low |
| P4 | 7 — Architecture | Ongoing | High |

---

## Quick Wins (can do in <30 min)

1. Fix avatar CSS (`.avatar` → `.avatar-circle`)
2. Fix "Skarbol Tech" footer → "Scraven"
3. Fix pricing page title order
4. Move `.lead-badge` CSS before media queries
5. Add `display:flex` to body if missing on pricing
6. Add password reset flow
7. Add "forgot password?" link on login page
