---
name: comprehensive-audit
description: >
  Comprehensive visual and design audit of lead-gen demo websites. Step-by-step inspection of every
  page, section, layout, header, body, footer, content, icons, images, and elements. Reports issues
  to the user and waits for their confirmation before making any fixes. Iterative fix-and-reaudit
  cycle until the site is perfect. For lead-gen outreach demo websites built with this project.
compatibility: opencode
metadata:
  project: lead-gen
  workflow: audit-fix-iterate
---

# Comprehensive Visual & Design Audit

Use this skill when the user asks you to audit a website built by this lead-gen project — every page, every section, every element, layout, header, body, footer, content, icons, images, and design details. **You do NOT fix anything without the user telling you to.**

## Workflow Overview

You follow this exact flow for every audit session:

1. **Phase 1 — Page Discovery** — Identify all pages of the website
2. **Phase 2 — Section-by-Section Inspection** — For each page, inspect every section
3. **Phase 3 — Issue Report** — Present findings to the user
4. **Phase 4 — User Directs Fixes** — Wait. User says what to fix.
5. **Phase 5 — Apply Fixes** — Only what user confirmed
6. **Phase 6 — Re-audit** — Re-check and show before/after

**IMPORTANT:** You NEVER fix anything unless the user explicitly says "fix that" or "fix this issue" or equivalent. You only report, wait, and act on explicit instructions.

---

## Phase 1 — Page Discovery

First, identify every page of the website:

- List all HTML pages (index.html, products.html, about.html, contact.html, order.html, etc.)
- Note the total page count
- Use the Glob tool or Read the directory to find all pages

Report to the user:
```
Found {N} pages:
1. index.html — Homepage
2. products.html — Products listing
3. about.html — About us
...
```

---

## Phase 2 — Section-by-Section Inspection

For **each page**, read the full HTML source and inspect **every section** in order. Use the Read tool to get the full content.

### For every page, inspect these zones in order:

#### 1. HEAD / Meta
- Title tag present and meaningful?
- Meta description present?
- Viewport meta tag?
- Favicon?
- CSS/JS links correct?

#### 2. Header / Navigation
- Logo present and visible?
- Navigation links all working (Home, Products, About, Contact, Order)?
- Language toggle button present?
- WhatsApp button present?
- Mobile hamburger menu present?
- Active page highlighted correctly?
- Header sticks at top?
- Bengali/English labels on all nav items?

#### 3. Hero Section
- Business name displayed correctly?
- Tagline / subtitle present?
- Hero badge/category label?
- Address shown (if available)?
- CTA buttons working (Shop Now, WhatsApp)?
- Background/styling present?
- Bengali AND English text for all labels?

#### 4. Trust Badges / Features Bar
- Trust icons present (Delivery, COD, Original, Quality)?
- Bengali and English labels for each?

#### 5. Products Grid
- Product cards render correctly?
- Each card has: image, name, description, price, order button?
- Images load (not broken)?
- Product names in English, descriptions in Bengali?
- "View All" button at bottom?
- Correct number of products shown?

#### 6. About Section
- About/Bio text present in Bengali and English?
- "Learn More" button links to about.html?

#### 7. Testimonials / Reviews
- Review cards with name, location, quote, stars?
- Realistic Bangladeshi names and locations?
- Bengali quotes?

#### 8. Social Media / Follow Section
- Facebook link correct?
- Follow button present?

#### 9. Footer
- Business name in footer?
- Quick links (Home, Products, About, Contact, Order)?
- Contact info (phone, email, address)?
- Social media links (Facebook, WhatsApp, Instagram)?
- Bengali and English labels?
- Copyright notice?

#### 10. WhatsApp Float Button
- Fixed bottom-right?
- Links to correct WhatsApp number?
- WhatsApp icon visible?

#### For each of these zones, note:
- ✅ **PASS** — everything correct
- ⚠️ **WARNING** — minor issue (e.g., styling could be better, text needs polish)
- ❌ **FAIL** — broken or missing (broken link, missing section, incorrect text)

### After each page, summarize:

```
### Page: products.html
- HEAD: ✅
- Header/Nav: ✅
- Page Hero: ⚠️ Title could be more descriptive
- Product Grid: ✅ All 10 products render
- Filter Bar: ✅ Category filters present
- Footer: ✅
- WhatsApp Float: ✅
```

---

## Phase 3 — Present the Full Issue Report

After inspecting ALL pages, present a consolidated report. Group by issue type, not by page:

### Format:

```
═══════════════════════════════════════════
COMPREHENSIVE AUDIT REPORT: {business_name}
═══════════════════════════════════════════

### 🟢 CRITICAL ISSUES (Broken/Missing)
{List each issue as a bullet with the page and section}

### 🟡 WARNINGS (Needs Improvement)
{List each issue}

### ℹ️ SUGGESTIONS (Nice to Have)
{Optional improvements}

────────────────────────────────────────
Summary: {X} critical, {Y} warnings, {Z} suggestions
────────────────────────────────────────
```

**STOP HERE. WAIT FOR THE USER.**

Ask:
```
I've completed the audit. Review the report above and tell me which issues you want me to fix. Say something like:
- "Fix issue #1" 
- "Fix all critical issues"
- "Fix the header on all pages"
- "Fix [specific thing you noticed]"

I will only make changes you explicitly ask for.
```

---

## Phase 4 — User Directs Fixes

The user will tell you what to fix. They might say:
- "Fix issue X" — fix that specific thing
- "Fix all critical issues" — fix all ❌ items
- "The header logo looks too small" — fix that design issue
- "Change the hero text" — make that change

**IMPORTANT RULES:**
- Only fix what the user explicitly asks for
- If the user says "fix everything" or "fix all issues", list the issues first and ask them to confirm each category
- If the user points out something YOU didn't notice in the audit, acknowledge it, fix it, and add it to the report
- Never make changes the user didn't ask for

---

## Phase 5 — Apply Fixes

For each confirmed fix:

1. **Read the source file** — Read the page HTML/CSS/JS
2. **Make the fix** — Edit the file(s)
3. **Report what changed** — "Fixed: added meta description to index.html"
4. **Wait** — After each fix or batch, wait for the user to continue

Fix categories and approaches:

| Issue Type | Fix Approach | Files Affected |
|---|---|---|
| Missing/incorrect meta | Edit `<head>` section | Each page HTML |
| Broken navigation link | Fix `href` attribute | Each page HTML |
| Missing section | Add section HTML | Specific page |
| Content text (Bengali/English) | Edit `.lang-bn` / `.lang-en` spans | Specific page |
| Image broken | Fix `src` URL or replace | Specific page |
| Styling issue | Edit `styles.css` or inline style | CSS or page |
| Missing icon | Add emoji or SVG | Specific section |
| Layout issue | Edit CSS grid/flex or HTML structure | CSS or page |
| Wrong phone/WhatsApp URL | Fix `wa.me/{number}` | All pages via `_build_js` / `_header` |
| Color/theme issue | Edit CSS variables in `styles.css` | CSS |

**After each fix batch**, tell the user:
```
✅ Fixed:
  - Added meta description to index.html
  - Fixed WhatsApp link on all pages
  - Added missing Bengali label to footer

What's next? Tell me the next issue to fix, or say "re-audit" to check the changes.
```

---

## Phase 6 — Re-audit

When the user says "re-audit" or "check again":

1. Re-read the modified pages
2. Re-inspect only the sections that were changed
3. Present a before/after comparison:

```
═══════════════════════════════════════════
RE-AUDIT REPORT: {business_name}
═══════════════════════════════════════════

Before Fix → After Fix:
❌ Missing meta description → ✅ Added: "Best beauty salon in Dhaka"
❌ Broken WhatsApp link → ✅ Correct number: +8801XXXXXXXXX
⚠️ Header logo size small → ✅ Increased from 32px to 40px

Remaining issues:
⚠️ Footer social links missing Instagram → (waiting for your instruction)
```

Then ask: **"What should I fix next? Or are you happy with the result?"**

---

## Audit Checklist Reference

Use this comprehensive checklist for every page:

### 🏗 Layout & Structure
- [ ] Page has valid HTML5 doctype and `<html lang="bn">`
- [ ] All sections are properly closed (no unclosed tags)
- [ ] CSS classes match the `styles.css` definitions
- [ ] Grid/flex layouts render correctly at desktop width
- [ ] Responsive at 768px (tablet breakpoint)
- [ ] Responsive at 480px (mobile breakpoint)
- [ ] No horizontal scrollbars
- [ ] Consistent spacing and padding across sections

### 🎨 Visual Design
- [ ] Color scheme is consistent across all pages (matches category palette)
- [ ] Typography is consistent (heading font vs body font)
- [ ] Primary color used for CTAs and key elements
- [ ] Cards have consistent border-radius and shadows
- [ ] Hero gradient matches category
- [ ] Icons use appropriate emojis (not broken/empty)

### 📝 Content
- [ ] Bengali text present for all user-facing labels
- [ ] English text present (hidden behind `.lang-en`)
- [ ] No placeholder text like "Lorem ipsum" or "Coming soon"
- [ ] Business name is correct on every page
- [ ] Phone number is correct and consistent
- [ ] Address matches the lead data
- [ ] Product names are in English, descriptions in Bengali
- [ ] Review/testimonial names are realistic Bangladeshi names

### 🔗 Functionality
- [ ] WhatsApp link: `https://wa.me/{clean_number}` works
- [ ] Phone link: `tel:{number}` works
- [ ] Navigation links: Home → /, Products → products.html, etc.
- [ ] Order form pre-fills from URL `?product=`
- [ ] Language toggle switches Bengali/English
- [ ] Mobile menu opens and closes
- [ ] Scroll animations work (`data-aos`)
- [ ] Product filter buttons work on products.html
- [ ] Contact form submits via WhatsApp

### 🖼 Images & Media
- [ ] Logo image loads (not 404)
- [ ] Product images load (not broken placeholders)
- [ ] `onerror` fallback present on all images
- [ ] Images have `loading="lazy"` attribute
- [ ] Image aspect ratios are consistent

### 🌐 Cross-Page Consistency
- [ ] Header/nav is identical across all pages
- [ ] Footer is identical across all pages
- [ ] WhatsApp float is on every page
- [ ] Language state persists across pages (via localStorage)
- [ ] Active page highlighted in nav

---

## Completion

When the user says "done" or "it's perfect" or equivalent:
1. ✅ Confirm the final state with a summary of all fixes made
2. ✅ Note any remaining issues the user chose not to fix
3. ✅ Done
