(function () {
  console.log('[Skarbol] content-instagram.js loaded on:', window.location.href);
  chrome.storage.local.remove('currentLead');

  const INSTA_HOST = 'www.instagram.com';

  function normalizeUrl(url) {
    try {
      const u = new URL(url);
      u.searchParams.delete('igsh');
      u.searchParams.delete('igshid');
      u.searchParams.delete('__tn__');
      u.hash = '';
      return u.toString().replace(/\/+$/, '');
    } catch (_) { return url; }
  }

  const pageBaseUrl = normalizeUrl(window.location.href);

  // ── Email extractor (shared from Facebook content.js) ──
  const emailRegex = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
  function extractEmail() {
    const exclude = ['facebook.com', 'fb.com', 'sentry.io', 'example.com', '.png', '.jpg', '.svg', '.gif'];
    const results = [];
    const seen = new Set();
    function addEmail(e) {
      const k = e.toLowerCase().trim();
      if (k && !seen.has(k) && !exclude.some(d => k.includes(d))) { seen.add(k); results.push(k); }
    }
    const links = document.querySelectorAll('a[href^="mailto:"]');
    for (const link of links) {
      const raw = link.getAttribute('href').replace('mailto:', '').split('?')[0].trim();
      if (raw) addEmail(raw);
    }
    const textMatches = document.body.innerText.match(emailRegex) || [];
    textMatches.forEach(addEmail);
    return results.join(', ');
  }

  // ── Phone extractor (shared from Facebook content.js) ──
  function extractPhone() {
    const results = [];
    const seen = new Set();
    function looksLikeRealNumber(s) {
      if (/^0{2,}/.test(s)) return false;
      if (/^(\d)\1+$/.test(s)) return false;
      if (s.length >= 8 && s.length % 3 === 0) {
        const part = s.slice(0, 3);
        if (part.repeat(s.length / 3) === s) return false;
      }
      if (s.length >= 8 && s.length % 2 === 0) {
        const part = s.slice(0, 2);
        if (part.repeat(s.length / 2) === s) return false;
      }
      return true;
    }
    function addPhone(p) {
      let normalized = p.replace(/[\s\-\(\)\.]/g, '');
      if (!normalized) return;
      if (normalized.startsWith('01') && normalized.length === 11) {
        normalized = '+880' + normalized.slice(1);
      } else if (normalized.startsWith('880') && normalized.length === 13) {
        normalized = '+' + normalized;
      } else if (/^\d{8,13}$/.test(normalized) && !normalized.startsWith('+')) {
        normalized = '+' + normalized;
      }
      if (seen.has(normalized)) return;
      const noPlus = normalized.replace(/^\+/, '');
      if (noPlus.length < 10) return;
      if (/^8801[3-9]\d{8}$/.test(noPlus)) { seen.add(normalized); results.push(normalized); return; }
      for (let ccLen = 1; ccLen <= 3 && ccLen < noPlus.length - 7; ccLen++) {
        const sub = noPlus.substring(ccLen);
        if (sub.length >= 8 && sub.length <= 12 && looksLikeRealNumber(sub)) {
          seen.add(normalized); results.push(normalized); return;
        }
      }
    }
    const telLinks = document.querySelectorAll('a[href^="tel:"]');
    for (const link of telLinks) {
      const raw = link.getAttribute('href').replace('tel:', '').split(/[;,#]/)[0].trim();
      if (raw) addPhone(raw);
    }
    const text = document.body.innerText;
    const clean = text.replace(/[\s\-\(\)\.]/g, '');
    const bdClean = clean.match(/(?:01[3-9]\d{8}|\+?8801[3-9]\d{8})/g) || [];
    bdClean.forEach(addPhone);
    const formatted = text.match(/\+?[\d\s\-\(\)\.]{7,20}/g) || [];
    for (const m of formatted) {
      const digits = m.replace(/[\s\-\(\)\.]/g, '');
      if (/^\d{8,13}$/.test(digits)) addPhone(m);
    }
    return results.join(', ');
  }

  // ── Score calculator (shared) ──
  function estimateDays(text) {
    if (!text) return -1;
    const parsed = new Date(text);
    if (!isNaN(parsed.getTime())) return Math.floor((Date.now() - parsed.getTime()) / 86400000);
    const t = text.toLowerCase();
    if (/just now/i.test(t) || /min/i.test(t)) return 0;
    const num = parseInt(t.match(/\d+/)?.[0] || '0', 10);
    if (/hour/i.test(t)) return 0;
    if (/day/i.test(t)) return num;
    if (/week/i.test(t)) return num * 7;
    if (/month/i.test(t)) return num * 30;
    if (/year/i.test(t)) return num * 365;
    return -1;
  }

  function calculateScore(data) {
    let score = 5;
    if (!data.has_website) score += 1;
    if (data.phone) score += 1;
    if (data.email) score += 1;
    if (data.address) score += 1;
    if (data.category) score += 1;
    if (data.followers) {
      const num = parseInt(data.followers.replace(/[^0-9]/g, ''), 10);
      if (!isNaN(num) && num < 50000) score += 1;
    }
    const days = estimateDays(data.last_post_date);
    if (days === -1) score -= 1;
    else if (days > 90) score -= 4;
    else if (days > 50) score -= 2;
    return Math.max(1, Math.min(10, score));
  }

  // ── Instagram-specific extractors ──

  function extractBusinessName() {
    const skipWords = new Set([
      'notifications', 'settings', 'profile', 'edit profile', 'posts',
      'followers', 'following', 'suggested', 'search',
    ]);
    // h2 in the profile header section is the display name
    const h2s = document.querySelectorAll('h2');
    for (const h2 of h2s) {
      const t = h2.innerText.trim();
      if (t && t.length > 1 && t.length < 80 && !skipWords.has(t.toLowerCase())) {
        return t;
      }
    }
    // Fallback: meta og:title
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      const t = (ogTitle.getAttribute('content') || '').replace(/ on Instagram$/, '').trim();
      if (t && !skipWords.has(t.toLowerCase())) return t;
    }
    return '';
  }

  function extractCategory() {
    const categoryKeywords = [
      'Beauty Salon', 'Salon', 'Parlour', 'Cosmetics', 'Skincare', 'Makeup', 'Nail',
      'Boutique', 'Fashion', 'Clothing', 'Tailor', 'Designer', 'Jewelry',
      'Gift Shop', 'Handicraft', 'Crafts',
      'Restaurant', 'Cafe', 'Coffee Shop', 'Bakery', 'Caterer', 'Food',
      'Clinic', 'Doctor', 'Dental', 'Pharmacy', 'Medicine',
      'Store', 'Shop', 'Retail', 'Wholesaler', 'Brand', 'Company',
      'Manufacturer', 'Factory', 'Agency', 'Service',
      'Studio', 'Spa', 'Gym', 'Fitness', 'Yoga', 'Wellness',
      'Photography', 'Videography', 'Media',
      'School', 'Academy', 'Coach', 'Training',
      'Consultant', 'Real Estate', 'Property',
      'IT', 'Software', 'Technology', 'Digital',
      'Electronics', 'Mobile', 'Gadget',
      'Home Decor', 'Furniture', 'Interior',
      'Baby', 'Kids', 'Toys',
      'Grocery', 'Mart',
      'Hotel', 'Travel', 'Tour',
      'Auto', 'Car', 'Bike',
      'Agriculture', 'Farm',
      'Event', 'Wedding', 'Planner',
    ];
    const catPattern = new RegExp('\\b(' + categoryKeywords.join('|') + ')\\b', 'i');
    // Scan bio text — Instagram bio is usually in a span/div in the header
    const bioEl = document.querySelector('span[class*="bio"], div[class*="bio"], div[class*="description"]');
    if (bioEl) {
      const text = bioEl.innerText;
      const match = text.match(catPattern);
      if (match) return match[0];
    }
    // Fallback: any visible text
    const spans = document.querySelectorAll('span, div');
    for (const el of spans) {
      const text = el.innerText.trim();
      if (text && text.length < 80 && catPattern.test(text)) return text;
    }
    // Meta description
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      const desc = ogDesc.getAttribute('content') || '';
      const m = desc.match(catPattern);
      if (m) return m[0];
    }
    return '';
  }

  function extractFollowers() {
    // Instagram shows "X followers" near the top of the profile
    const text = document.body.innerText;
    const patterns = [
      /([\d,.]+\s*[KkMm]?)\s*followers?/i,
      /фоловери\s+([\d,.]+)/i,
      /([\d,.]+)\s*জন ফলোয়ার/i,
    ];
    for (const p of patterns) {
      const match = text.match(p);
      if (match) {
        let count = match[1] || match[0];
        return count.trim() + ' followers';
      }
    }
    // Look for elements with "followers" text
    const allSpans = document.querySelectorAll('span');
    for (const span of allSpans) {
      const t = span.innerText.trim();
      const m = t.match(/^([\d,.]+\s*[KkMm]?)$/);
      if (m) {
        const next = span.nextElementSibling;
        if (next && /follower/i.test(next.innerText)) {
          return m[1].trim() + ' followers';
        }
      }
    }
    return '';
  }

  function extractWebsite() {
    const excludeDomains = [
      'facebook.com', 'fb.com', 'instagram.com', 'twitter.com', 'x.com',
      'youtube.com', 'whatsapp.com', 'wa.me', 'google.com', 'apple.com',
      'linkedin.com', 'snapchat.com', 'tiktok.com',
    ];
    function isExcluded(url) {
      try { const u = new URL(url); return excludeDomains.some(d => u.hostname.includes(d)); } catch (_) { return true; }
    }
    // Instagram bio website link: usually an anchor in the bio section
    const bioSection = document.querySelector('header section, main section, article');
    if (bioSection) {
      const links = bioSection.querySelectorAll('a[href]');
      for (const link of links) {
        const href = link.href;
        if (href && href.startsWith('http') && !isExcluded(href) && !href.includes('instagram.com')) {
          return href;
        }
      }
    }
    // Fallback: all links on page (skip Instagram)
    const allLinks = document.querySelectorAll('a[href]');
    for (const link of allLinks) {
      const href = link.href;
      if (href && href.startsWith('http') && !isExcluded(href) && !href.includes('instagram.com')) {
        return href;
      }
    }
    // Meta og:url or similar
    const ogUrl = document.querySelector('meta[property="og:url"]');
    if (ogUrl) {
      const u = ogUrl.getAttribute('content') || '';
      if (u && !isExcluded(u) && !u.includes('instagram.com')) return u;
    }
    return '';
  }

  function extractLastPostDate() {
    // Instagram posts have time elements or aria-label with date info
    const texts = document.body.innerText.split('\n');
    const timePattern = /\b(?:about\s+)?(?:\d+|an?)\s+(hours?|minutes?|days?|weeks?|months?|years?)\s+ago\b|^just now$/i;
    const shortPattern = /^\d{1,4}[hmdw]$/i;
    const datePattern = /^[A-Z][a-z]{2,}\s+\d{1,2}(?:,\s*\d{4})?$/;

    function estimateMinutes(text) {
      const parsed = new Date(text);
      if (!isNaN(parsed.getTime())) return Math.floor((Date.now() - parsed.getTime()) / 60000);
      const t = text.toLowerCase();
      if (/just now/i.test(t)) return 0;
      const num = parseInt(t.match(/\d+/)?.[0] || '1', 10);
      if (/min/.test(t)) return num;
      if (/hour/.test(t)) return num * 60;
      if (/day/.test(t)) return num * 1440;
      if (/week/.test(t)) return num * 10080;
      if (/month/.test(t)) return num * 43200;
      if (/year/.test(t)) return num * 525600;
      return 999999;
    }

    const now = Date.now();
    let candidates = [];

    // Time elements
    const times = document.querySelectorAll('time');
    for (const el of times) {
      const t = el.getAttribute('datetime') || el.textContent || '';
      if (t) {
        const parsed = new Date(t);
        if (!isNaN(parsed.getTime())) {
          candidates.push({ text: t, score: parsed.getTime() });
        } else if (timePattern.test(t) || shortPattern.test(t.trim())) {
          candidates.push({ text: t, score: now - estimateMinutes(t) * 60000 });
        }
      }
    }

    // TreeWalker for short time patterns
    if (candidates.length === 0) {
      try {
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
        let node;
        while ((node = walker.nextNode())) {
          const text = (node.textContent || '').trim();
          if (!text) continue;
          if (timePattern.test(text) || shortPattern.test(text) || datePattern.test(text)) {
            candidates.push({ text, score: now - estimateMinutes(text) * 60000 });
          }
        }
      } catch (_) {}
    }

    if (candidates.length === 0) {
      const text = document.body.innerText;
      const m = text.match(timePattern);
      if (m) candidates.push({ text: m[0], score: now - estimateMinutes(m[0]) * 60000 });
    }

    if (candidates.length === 0) return '';

    candidates.sort((a, b) => b.score - a.score);
    return candidates[0].text;
  }

  // ── Main extraction ──
  function extractInstagramData() {
    console.log('[Skarbol] extracting Instagram data');
    const data = { url: pageBaseUrl };
    data.business_name = extractBusinessName();
    data.category = extractCategory();
    data.followers = extractFollowers();
    data.email = extractEmail();
    data.phone = extractPhone();
    data.website = extractWebsite();
    data.has_website = !!data.website;
    data.address = '';
    data.last_post_date = extractLastPostDate();
    data.qualification_score = calculateScore(data);
    console.log('[Skarbol] Instagram extracted:', JSON.stringify(data));
    chrome.storage.local.set({ currentLead: data });
  }

  // ── Wait for page to load, then extract ──
  let extractTimeout = null;
  const observer = new MutationObserver(() => {
    clearTimeout(extractTimeout);
    extractTimeout = setTimeout(extractInstagramData, 4000);
  });
  observer.observe(document.body, { childList: true, subtree: true });
  window.addEventListener('load', () => setTimeout(extractInstagramData, 3000));
  setTimeout(extractInstagramData, 3000);

  // Retry phone/email
  function retryPhoneEmail(delay, maxRetries) {
    let attempts = 0;
    function tryFind() {
      chrome.storage.local.get('currentLead', (result) => {
        const lead = result.currentLead || {};
        if (lead.phone && lead.email) return;
        const phone = extractPhone();
        const email = extractEmail();
        let updated = false;
        if (phone && !lead.phone) { lead.phone = phone; updated = true; }
        if (email && !lead.email) { lead.email = email; updated = true; }
        if (updated) {
          lead.qualification_score = calculateScore(lead);
          chrome.storage.local.set({ currentLead: lead });
          return;
        }
        attempts++;
        if (attempts < maxRetries) setTimeout(tryFind, delay);
      });
    }
    setTimeout(tryFind, 3000);
  }
  retryPhoneEmail(5000, 5);
})();
