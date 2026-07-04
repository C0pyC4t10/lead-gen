(function () {
  console.log('[Skarbol] content.js v2 loaded on:', window.location.href);
  // Clear stale data from previous sessions
  chrome.storage.local.remove('currentLead');
  chrome.storage.local.remove('pendingAbout');
  let extractTimeout = null;

  // Inject fetch interceptor in main world to capture post timestamps
  function injectDateInterceptor() {
    const script = document.createElement('script');
    script.src = chrome.runtime.getURL('interceptor.js');
    script.onload = function() { script.remove(); };
    document.documentElement.appendChild(script);
  }
  injectDateInterceptor();

  // Listen for messages from the injected script
  window.addEventListener('message', function skarbolListener(event) {
    if (event.data && event.data.type === '__SKARBOL_POST_DATE' && event.data.date) {
      chrome.storage.local.get('currentLead', function(result) {
        if (result.currentLead) {
          result.currentLead.last_post_date = event.data.date;
          result.currentLead.qualification_score = calculateScore(result.currentLead);
          chrome.storage.local.set({ currentLead: result.currentLead });
          console.log('[Skarbol] post date from API:', event.data.date);
        }
      });
    }
  });

  function normalizeUrl(url) {
    const u = new URL(url);
    u.searchParams.delete('sk');
    u.searchParams.delete('v');
    u.searchParams.delete('ref');
    u.searchParams.delete('__tn__');
    u.hash = '';
    return u.toString().replace(/\/+$/, '');
  }

  const urlObj = new URL(window.location.href);
  const isProfilePhp = urlObj.pathname.includes('profile.php');
  const isAboutPage = urlObj.pathname.includes('/about') ||
    (isProfilePhp && (urlObj.searchParams.get('sk') === 'about' || urlObj.searchParams.get('v') === 'about'));
  const pageBaseUrl = normalizeUrl(window.location.href);

  function aboutUrl() {
    if (isProfilePhp) {
      const u = new URL(pageBaseUrl);
      u.searchParams.set('sk', 'about');
      return u.toString();
    }
    return pageBaseUrl + '/about';
  }

  function extractPageData() {
    console.log('[Skarbol] extracting on', isAboutPage ? '/about' : 'main', 'page');

    const data = { url: pageBaseUrl };

    data.business_name = extractBusinessName();
    data.category = extractCategory();
    data.followers = extractFollowers();
    data.email = extractEmail();
    data.phone = extractPhone();
    data.website = extractWebsite();
    data.has_website = !!data.website;
    data.address = extractAddress();
    data.last_post_date = extractLastPostDate();
    data.qualification_score = calculateScore(data);

    console.log('[Skarbol] extracted:', JSON.stringify(data));

    if (isAboutPage) {
      chrome.storage.local.get('pendingAbout', (result) => {
        const pending = result.pendingAbout;
        if (pending && pending.mainUrl === pageBaseUrl) {
          const merged = { ...pending.data, ...data, url: pageBaseUrl };
          merged.email = merged.email || pending.data.email || '';
          merged.phone = merged.phone || pending.data.phone || '';
          merged.website = merged.website || pending.data.website || '';
          merged.has_website = !!merged.website;
          merged.address = merged.address || pending.data.address || '';
          merged.qualification_score = calculateScore(merged);
          chrome.storage.local.set({ currentLead: merged }, () => {
            console.log('[Skarbol] merged data saved to currentLead');
          });
          window.location.href = pageBaseUrl;
        } else {
          chrome.storage.local.set({ currentLead: data }, () => {
            console.log('[Skarbol] about page data saved');
          });
        }
        chrome.storage.local.remove('pendingAbout');
      });
    } else {
      chrome.storage.local.set({ currentLead: data }, () => {
        console.log('[Skarbol] main page data saved');
      });

      const hasContact = data.phone || data.email || data.website || data.address;
      if (!hasContact) {
        autoNavigateAbout(data);
      }
    }
  }

  function autoNavigateAbout(partialData) {
    chrome.storage.local.set({
      pendingAbout: { mainUrl: pageBaseUrl, data: partialData, timestamp: Date.now() }
    }, () => {
      console.log('[Skarbol] saved pendingAbout, navigating to about');
    });

    const aboutLink = isProfilePhp
      ? document.querySelector('a[href*="sk=about"], a[aria-label*="About"]')
      : document.querySelector('a[href*="/about"][role="tab"], a[href*="/about"]:not([role="button"])');

    if (aboutLink) {
      aboutLink.click();
      console.log('[Skarbol] clicked About tab');
    } else {
      window.location.href = aboutUrl();
    }
  }

  function extractBusinessName() {
    const skipWords = new Set([
      'notifications', 'home', 'watch', 'menu', 'settings', 'profile',
      'friends', 'photos', 'chats', 'about', 'messages', 'pages',
      'facebook', 'marketplace', 'groups', 'see all', 'search',
      'search results', 'create', 'saved', 'memories', 'most recent',
      'unread', 'read', 'seen', 'delivered',
    ]);
    const skipAltPatterns = [
      /no photo description available/i,
      /^profile photo/i,
      /^profile picture/i,
      /^photo of/i,
      /^picture of/i,
      /^loading/i,
      /^\d+$/,
      /photos?\s+from/i,
      /post/i,
      /cover\s+photo/i,
      /timeline/i,
    ];

    // Page header — only look inside the profile/commercial page header area
    const headerArea = document.querySelector(
      '[data-pagelet="ProfileHeader"], ' +
      '[data-pagelet="CommercialProfile"]'
    );
    if (headerArea) {
      const h1InHeader = headerArea.querySelectorAll('h1, h2, strong');
      for (const el of h1InHeader) {
        const t = el.innerText.trim();
        if (t && t.length > 3 && t.length < 120 && !skipWords.has(t.toLowerCase()) && !/^\d+$/.test(t)) {
          return t;
        }
      }
      const spansInHeader = headerArea.querySelectorAll('span[dir="auto"]');
      for (const span of spansInHeader) {
        const t = span.innerText.trim();
        if (t && t.length > 3 && t.length < 120 && !skipWords.has(t.toLowerCase()) && !/^\d+$/.test(t)) {
          return t;
        }
      }
    }

    // og:title — reliable for the actual page name
    const ogTitle = document.querySelector('meta[property="og:title"]');
    if (ogTitle) {
      const t = (ogTitle.getAttribute('content') || '').trim();
      if (t && !skipWords.has(t.toLowerCase())) return t;
    }

    // h1 headings
    const h1s = document.querySelectorAll('h1');
    for (const h1 of h1s) {
      const t = h1.innerText.trim();
      if (t && t.length > 3 && !skipWords.has(t.toLowerCase())) return t;
    }

    // Profile photo alt text — but ONLY the small circular profile image, not post photos
    const profileImgs = document.querySelectorAll(
      'img[alt]:not([alt=""]):not([alt*="post" i]):not([alt*="Photo from" i])'
    );
    const ranked = [];
    for (const img of profileImgs) {
      const alt = img.alt.trim();
      if (!alt || alt.length < 3 || alt.length > 60) continue;
      if (skipWords.has(alt.toLowerCase())) continue;
      if (skipAltPatterns.some(p => p.test(alt))) continue;
      if (!/^[A-Za-z0-9&\-'. ]+$/.test(alt)) continue;
      // Prefer smaller images (profile photos are typically 40-168px)
      const w = img.naturalWidth || img.width || 999;
      ranked.push({ alt, score: w < 200 ? 10 : 1 });
    }
    if (ranked.length) {
      ranked.sort((a, b) => b.score - a.score);
      return ranked[0].alt;
    }

    // document title fallback
    const title = document.title.replace(/ \| Facebook$/, '').replace(/ - Facebook$/, '').trim();
    if (title && title.length > 3 && !skipWords.has(title.toLowerCase()) && !/^search/i.test(title)) return title;

    return '';
  }

  function extractCategory() {
    const categoryKeywords = [
      'Beauty Salon', 'Salon', 'Parlour', 'Parlor', 'Cosmetics', 'Skincare', 'Makeup',
      'Boutique', 'Fashion', 'Clothing', 'Tailor', 'Designer', 'Jewelry', 'Jewellery',
      'Gift Shop', 'Gifts', 'Handicraft', 'Crafts',
      'Restaurant', 'Cafe', 'Coffee Shop', 'Bakery', 'Caterer', 'Food',
      'Clinic', 'Doctor', 'Dental', 'Optical', 'Pharmacy', 'Medicine',
      'Store', 'Shop', 'Retail', 'Wholesaler', 'Distributor', 'Supplier',
      'Manufacturer', 'Factory', 'Brand', 'Company', 'Agency', 'Service',
      'Studio', 'Spa', 'Salon', 'Parlour',
      'Gym', 'Fitness', 'Yoga', 'Wellness',
      'Photography', 'Videography', 'Media',
      'School', 'Academy', 'Coach', 'Training', 'Tutorial',
      'Consultant', 'Consulting', 'Advisor',
      'Real Estate', 'Property', 'Developer',
      'IT', 'Software', 'Technology', 'Digital',
      'Transport', 'Logistics', 'Delivery', 'Courier',
      'Electronics', 'Mobile', 'Gadget',
      'Home Decor', 'Furniture', 'Interior',
      'Baby', 'Kids', 'Toys',
      'Grocery', 'Supermarket', 'Mart',
      'Hotel', 'Resort', 'Travel', 'Tour',
      'Auto', 'Car', 'Bike', 'Garage', 'Workshop',
      'Agriculture', 'Farm', 'Fisheries',
      'Event', 'Wedding', 'Planner', 'Decorator',
    ];
    const catPattern = new RegExp('\\b(' + categoryKeywords.join('|') + ')\\b', 'i');

    // First try: contact info section in About page — most reliable
    const contactSections = document.querySelectorAll(
      '[data-pagelet="ProfileCards"], ' +
      '[data-pagelet="PageHeader"], ' +
      '[aria-label*="about" i], ' +
      'div[role="main"]'
    );
    for (const section of contactSections) {
      const text = section.innerText || '';
      const match = text.match(catPattern);
      if (match) {
        // Return the full surrounding context (1-4 words) for a clean category name
        const idx = text.indexOf(match[0]);
        const snippet = text.slice(Math.max(0, idx - 30), idx + match[0].length + 30);
        const lines = snippet.split('\n').filter(l => catPattern.test(l));
        if (lines.length > 0) return lines[0].trim();
      }
    }

    // Second try: any span/div with a category match
    const spans = document.querySelectorAll('span, div');
    for (const el of spans) {
      const text = el.innerText.trim();
      if (
        text && text.length < 80 &&
        /[A-Z]/.test(text) &&
        catPattern.test(text)
      ) {
        return text;
      }
    }

    // Third try: meta description
    const ogDesc = document.querySelector('meta[property="og:description"]');
    if (ogDesc) {
      const desc = ogDesc.getAttribute('content') || '';
      const catMatch = desc.match(catPattern);
      if (catMatch) return catMatch[0];
    }

    return '';
  }

  function extractFollowers() {
    const text = document.body.innerText;
    const patterns = [
      /(\d[\d,.]*[KkMmBb]?)\s*(followers|likes|people follow|follow this)/i,
      /([\d,]+)\s*·\s*(followers|likes|following)/i,
      /(followers|likes)\s+(\d[\d,.]*[KkMm]?)/i,
      /(\d[\d,.]*[KkMm]?)\s+(জন ফলোয়ার|জন লাইক|follower|like)/i,
    ];
    for (const p of patterns) {
      const match = text.match(p);
      if (match) return match[0].trim();
    }
    return '';
  }

  function extractEmail() {
    const exclude = ['facebook.com', 'fb.com', 'sentry.io', 'example.com', '.png', '.jpg', '.svg', '.gif'];
    const results = [];
    const seen = new Set();

    function addEmail(e) {
      const k = e.toLowerCase().trim();
      if (k && !seen.has(k) && !exclude.some(d => k.includes(d))) {
        seen.add(k);
        results.push(k);
      }
    }

    // Priority 1: mailto: links
    const links = document.querySelectorAll('a[href^="mailto:"]');
    for (const link of links) {
      const raw = link.getAttribute('href').replace('mailto:', '').split('?')[0].trim();
      if (raw) addEmail(raw);
    }

    // Priority 1.5: "Contact info" section — most reliable for email
    try {
      const contactInfoEl = Array.from(document.querySelectorAll('div, section, span'))
        .find(el => /contact\s*info/i.test(el.innerText || '') && el.children.length < 10);
      if (contactInfoEl) {
        const ciText = contactInfoEl.innerText || '';
        const ciMatches = ciText.match(emailRegex) || [];
        ciMatches.forEach(addEmail);
      }
    } catch (_) {}

    // Priority 2: Contact-specific sections (About page cards)
    const contactSections = document.querySelectorAll(
      '[data-pagelet="ProfileCards"], ' +
      '[data-pagelet="PageHeader"], ' +
      '[role="main"], ' +
      '[aria-label*="about" i]'
    );
    const emailRegex = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
    for (const section of contactSections) {
      const sectionText = section.innerText || '';
      const matches = sectionText.match(emailRegex) || [];
      matches.forEach(addEmail);
    }

    // Priority 3: JSON script tags (server-rendered metadata)
    try {
      const scripts = document.querySelectorAll('script[type="application/json"]');
      for (const s of scripts) {
        const raw = s.textContent;
        if (!raw) continue;
        const matches = raw.match(emailRegex) || [];
        matches.forEach(addEmail);
      }
    } catch (_) {}

    // Priority 4: Full page body
    const textMatches = document.body.innerText.match(emailRegex) || [];
    textMatches.forEach(addEmail);

    return results.join(', ');
  }

  function extractPhone() {
    const results = [];
    const seen = new Set();

    function looksLikeRealNumber(s) {
      // Reject if subscriber part starts with "00" — not a real number
      if (/^0{2,}/.test(s)) return false;
      // Reject if all same digit (e.g. 000000000, 111111111)
      if (/^(\d)\1+$/.test(s)) return false;
      // Reject if evenly repeating short pattern (e.g. 123123123)
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
      // BD local → international
      if (normalized.startsWith('01') && normalized.length === 11) {
        normalized = '+880' + normalized.slice(1);
      } else if (normalized.startsWith('880') && normalized.length === 13) {
        normalized = '+' + normalized;
      } else if (/^\d{8,13}$/.test(normalized) && !normalized.startsWith('+')) {
        normalized = '+' + normalized;
      }
      if (seen.has(normalized)) return;
      const noPlus = normalized.replace(/^\+/, '');
      if (noPlus.length < 10) return; // minimum 10 digits total
      // BD numbers: +8801[3-9]XXXXXXXXX
      if (/^8801[3-9]\d{8}$/.test(noPlus)) {
        seen.add(normalized);
        results.push(normalized);
        return;
      }
      // General: try 1-3 digit country code, require subscriber >= 8
      for (let ccLen = 1; ccLen <= 3 && ccLen < noPlus.length - 7; ccLen++) {
        const sub = noPlus.substring(ccLen);
        if (sub.length >= 8 && sub.length <= 12 && looksLikeRealNumber(sub)) {
          seen.add(normalized);
          results.push(normalized);
          return;
        }
      }
    }

    // Priority 1: tel: links (most reliable)
    const telLinks = document.querySelectorAll('a[href^="tel:"]');
    for (const link of telLinks) {
      const raw = link.getAttribute('href').replace('tel:', '').split(/[;,#]/)[0].trim();
      if (raw) addPhone(raw);
    }

    // Priority 1.5: "Contact info" section — scan any element containing this text
    try {
      const contactInfoEl = Array.from(document.querySelectorAll('div, section, span'))
        .find(el => /contact\s*info/i.test(el.innerText || '') && el.children.length < 10);
      if (contactInfoEl) {
        const ciText = contactInfoEl.innerText || '';
        const ciClean = ciText.replace(/[\s\-\(\)\.]/g, '');
        const ciPhone = ciClean.match(/(?:01[3-9]\d{8}|\+?8801[3-9]\d{8})/g) || [];
        ciPhone.forEach(addPhone);
        const ciFormatted = ciText.match(/\+?[\d\s\-\(\)\.]{7,20}/g) || [];
        for (const m of ciFormatted) {
          const digits = m.replace(/[\s\-\(\)\.]/g, '');
          if (/^\d{8,13}$/.test(digits)) addPhone(m);
        }
      }
    } catch (_) {}

    // Priority 2: Contact-specific sections (About page cards, contact info)
    const contactSections = document.querySelectorAll(
      '[data-pagelet="ProfileCards"], ' +
      '[data-pagelet="PageHeader"], ' +
      '[role="main"], ' +
      '[aria-label*="about" i], ' +
      '[aria-label*="contact" i], ' +
      'div[data-pagelet]'
    );
    for (const section of contactSections) {
      const sectionText = section.innerText || '';
      const sectionClean = sectionText.replace(/[\s\-\(\)\.]/g, '');
      // BD mobile: 01[3-9] followed by 8 digits
      const bdMobile = sectionClean.match(/(?:01[3-9]\d{8}|\+?8801[3-9]\d{8})/g) || [];
      bdMobile.forEach(addPhone);
      // Also look for formatted numbers in contact sections
      const formatted = sectionText.match(/\+?[\d\s\-\(\)\.]{7,20}/g) || [];
      for (const m of formatted) {
        const digits = m.replace(/[\s\-\(\)\.]/g, '');
        if (/^\d{8,13}$/.test(digits)) addPhone(m);
      }
    }

    // Priority 3: Full page — BD numbers
    const text = document.body.innerText;
    const clean = text.replace(/[\s\-\(\)\.]/g, '');
    const bdClean = clean.match(/(?:01[3-9]\d{8}|\+?8801[3-9]\d{8})/g) || [];
    bdClean.forEach(addPhone);

    // Priority 4: Full page — formatted international numbers
    const formatted = text.match(/\+?[\d\s\-\(\)\.]{7,20}/g) || [];
    for (const m of formatted) {
      const digits = m.replace(/[\s\-\(\)\.]/g, '');
      if (/^\d{8,13}$/.test(digits)) addPhone(m);
    }

    return results.join(', ');
  }

  function cleanUrl(raw) {
    const trackingParams = ['fbclid', 'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'ref', 'fref', '__cft__', '__tn__'];
    try {
      const u = new URL(raw);
      for (const p of trackingParams) u.searchParams.delete(p);
      return u.origin + u.pathname;
    } catch (_) {
      return raw;
    }
  }

  function extractWebsite() {
    const excludeDomains = [
      'facebook.com', 'fb.com', 'fbcdn.net', 'messenger.com', 'instagram.com',
      'twitter.com', 'x.com', 'youtube.com', 'whatsapp.com', 'wa.me', 'm.me',
      'google.com', 'apple.com', 'linkedin.com', 'bing.com',
    ];

    function isExcluded(url) {
      try {
        const u = new URL(url);
        return excludeDomains.some(d => u.hostname.includes(d));
      } catch (_) { return true; }
    }

    // Priority 1: Contact cards — ProfileCards often list website
    const cards = document.querySelectorAll('[data-pagelet="ProfileCards"]');
    let links;
    for (const card of cards) {
      links = card.querySelectorAll('a[href]');
    }
    // Priority 4: Body text — scan all links for website patterns
    const allLinks = document.querySelectorAll('a[href]');
    const candidates = [];

    for (const link of allLinks) {
        const href = link.href;
        if (href && href.startsWith('http') && !isExcluded(href)) {
          return cleanUrl(href);
        }
      }

    // Priority 2: JSON metadata (structured data)
    try {
      const scripts = document.querySelectorAll('script[type="application/json"]');
      for (const s of scripts) {
        const raw = s.textContent;
        if (!raw) continue;
        const urlMatches = raw.match(/"website"\s*:\s*"([^"]+)"/) || raw.match(/"url"\s*:\s*"([^"]+)"(?!.*facebook)/);
        if (urlMatches) {
          const found = urlMatches[1];
          if (found.startsWith('http') && !isExcluded(found)) return cleanUrl(found);
        }
      }
    } catch (_) {}

    // Priority 3: Facebook redirect links (l.php?u=)
    const fbRedirectLinks = document.querySelectorAll('a[href*="l.facebook.com/l.php?u="]');
    for (const link of fbRedirectLinks) {
      try {
        const href = link.href;
        const uParam = href.match(/[?&]u=([^&]+)/);
        if (uParam) {
          const decoded = decodeURIComponent(uParam[1]);
          const u = new URL(decoded);
          if (!excludeDomains.some(d => u.hostname.includes(d))) {
            return cleanUrl(u.href);
          }
        }
      } catch (_) {}
    }

    if (links) for (const link of links) {
      const href = link.href;
      if (!href) continue;
      try {
        const u = new URL(href);
        if (!u.protocol.startsWith('http')) continue;
        if (excludeDomains.some(d => u.hostname.includes(d))) continue;

        const parentText = (link.closest('div, section') || link).innerText.toLowerCase();
        const score = (parentText.includes('links') || parentText.includes('website') ? 2 : 0) +
                      (link.innerText.toLowerCase().includes('website') ? 1 : 0);

        candidates.push({ href, score });
      } catch (_) {}
    }

    const text = document.body.innerText;
    const lines = text.split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      if (/\b(website|links|visit|www)\b/i.test(trimmed)) {
        const domainMatch = trimmed.match(/([a-zA-Z0-9-]+\.[a-zA-Z]{2,}(?:\/[^\s]*)?)/);
        if (domainMatch) {
          let found = domainMatch[1];
          if (!found.startsWith('http')) found = 'https://' + found;
          try {
            const u = new URL(found);
            if (!excludeDomains.some(d => u.hostname.includes(d))) {
              candidates.push({ href: found, score: 1 });
            }
          } catch (_) {}
        }
      }
    }

    if (candidates.length === 0) return '';

    candidates.sort((a, b) => b.score - a.score);
    return candidates[0].href;
  }

  function extractAddress() {
    const cities = 'Dhaka|Chattogram|Chittagong|Sylhet|Khulna|Rajshahi|Barisal|Rangpur|Mymensingh|Narayanganj|Gazipur|Comilla|Bogra|Jessore|Dinajpur|Tangail|Pabna|Brahmanbaria|Sirajganj|Narsingdi|Savar|Cox\\s?Bazar';
    const text = document.body.innerText;

    // Priority 1: Google Maps links — most reliable real address
    const mapLinks = document.querySelectorAll('a[href*="maps.google.com"], a[href*="maps.app.goo.gl"], a[href*="google.com/maps"]');
    for (const link of mapLinks) {
      const parent = link.closest('div, [role="main"]') || link.parentElement;
      if (!parent) continue;
      const pt = parent.innerText;
      // Extract the short address block near the link
      const lines = pt.split('\n').map(l => l.trim()).filter(l => l.length > 3);
      const addrIdx = lines.findIndex(l => /(Road|House|Floor|Level|Lane|Street|Block|Sector|Building|Village)/i.test(l));
      if (addrIdx >= 0) {
        const block = lines.slice(Math.max(0, addrIdx - 1), addrIdx + 3).join(', ');
        if (block.length < 200) return block;
      }
      // Fallback: last 3 substantial lines before/around the link
      const linkLineIdx = lines.findIndex(l => l.includes('maps.google') || l.includes('goo.gl'));
      const around = lines.slice(Math.max(0, linkLineIdx - 2), linkLineIdx + 2).filter(l => l.length > 5);
      if (around.length) return around.join(', ');
    }

    // Priority 2: Structured address pattern with city name
    const addrBlockPatterns = [
      new RegExp('(?:Road|House|Floor|Level|Lane|Avenue|Street|Block|Sector|Building|Village|Thana|Upazila|District|Holding).{5,120}(?:' + cities + ')', 'is'),
      new RegExp('(?:' + cities + ').{0,60}(?:Road|House|Floor|Level|Lane|Avenue|Street|Block|Sector|Building)', 'is'),
    ];
    for (const p of addrBlockPatterns) {
      const m = text.match(p);
      if (m) {
        const block = m[0].trim();
        if (block.length < 200) return block;
      }
    }

    // Priority 3: City-only fallback
    const cityMatch = text.match(new RegExp('\\b(?:' + cities + ')\\b'));
    if (cityMatch) {
      return cityMatch[0];
    }

    return '';
  }

  function extractLastPostDate() {
    const skipAncestors = [
      '[role="dialog"]', '[aria-label*="notification" i]', '[aria-label*="messenger" i]',
      '[aria-label*="chat" i]', '[aria-label*="sidebar" i]', '[data-pagelet*="right" i]',
      '[aria-label="Home"]', '[aria-label*="mark as read" i]',
    ];
    const skipSelector = skipAncestors.join(',');

    function isSkipped(el) {
      return el && el.closest && el.closest(skipSelector);
    }

    const timePattern = /\b(?:about\s+)?(?:\d+|an?)\s+(hours?|minutes?|days?|weeks?|months?|years?|hour|minute|day|week|month|year)\s+ago\b|^just now$/i;
    const shortPattern = /^\d{1,4}[hmdw]$/i;
    const todayPattern = /\b(Today|Yesterday)\s+(at\s+)?\d/i;

    function estimateMinutes(text) {
      const parsed = new Date(text);
      if (!isNaN(parsed.getTime())) {
        return Math.floor((Date.now() - parsed.getTime()) / 60000);
      }
      const t = text.toLowerCase();
      if (/just now/i.test(t)) return 0;
      if (/about an? hour/i.test(t)) return 60;
      const num = parseInt(t.match(/\d+/)?.[0] || '1', 10);
      if (/min/.test(t)) return num;
      if (/hour/.test(t) || /^(\d+)h$/.test(t)) return num * 60;
      if (/day/.test(t) || /^(\d+)d$/.test(t)) return num * 1440;
      if (/week/.test(t) || /^(\d+)w$/.test(t)) return num * 10080;
      if (/month/.test(t)) return num * 43200;
      if (/year/.test(t)) return num * 525600;
      return 999999;
    }

    const now = Date.now();
    let candidates = [];

    // 1. Check abbr elements with aria-label / title / textContent
    const abbrs = document.querySelectorAll('abbr');
    for (const el of abbrs) {
      if (isSkipped(el)) continue;
      const t = el.getAttribute('aria-label') || el.getAttribute('title') || el.textContent || '';
      if (!t || t.toLowerCase().includes('notification')) continue;
      if (timePattern.test(t) || shortPattern.test(t.trim())) {
        candidates.push({ text: t, score: now - estimateMinutes(t) * 60000 });
      }
    }

    // 2. TreeWalker: scan all text nodes for short time patterns like "16h", "3d"
    if (candidates.length === 0) {
      try {
        const walker = document.createTreeWalker(
          document.body, NodeFilter.SHOW_TEXT, null, false
        );
        let node;
        while ((node = walker.nextNode())) {
          const text = (node.textContent || '').trim();
          if (!text) continue;
          if (shortPattern.test(text)) {
            const parent = node.parentElement;
            if (parent && !isSkipped(parent)) {
              candidates.push({ text, score: now - estimateMinutes(text) * 60000 });
            }
          }
        }
      } catch (_) {}
    }

    // 3. Try JSON script tags for server-rendered post data
    if (candidates.length === 0) {
      try {
        const scripts = document.querySelectorAll('script[type="application/json"]');
        for (const s of scripts) {
          const raw = s.textContent;
          if (!raw) continue;
          const found = raw.match(/"(?:creation_time|publish_time|scheduled_publish_time)"\s*[:]\s*(\d{10,})/gi);
          if (found) {
            let best = 0;
            for (const match of found) {
              const num = parseInt(match.match(/\d{10,}/)?.[0] || '0', 10);
              if (num > best) best = num;
            }
            if (best > 1e9) {
              const d = new Date(best * 1000);
              const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
              const month = months[d.getMonth()];
              const day = d.getDate();
              let hours = d.getHours();
              const minutes = d.getMinutes();
              const ampm = hours >= 12 ? 'PM' : 'AM';
              hours = hours % 12 || 12;
              const text = month + ' ' + day + ', ' + d.getFullYear() + ' ' + hours + ':' + (minutes < 10 ? '0' : '') + minutes + ' ' + ampm;
              candidates.push({ text, score: best * 1000 });
            }
          }
        }
      } catch (_) {}
    }

    // 4. "Today at" or "Yesterday at" patterns
    if (candidates.length === 0) {
      try {
        const walker = document.createTreeWalker(
          document.body, NodeFilter.SHOW_TEXT, null, false
        );
        let node;
        while ((node = walker.nextNode())) {
          const text = (node.textContent || '').trim();
          if (!text) continue;
          if (todayPattern.test(text)) {
            const parent = node.parentElement;
            if (parent && !isSkipped(parent)) {
              candidates.push({ text, score: now });
            }
          }
        }
      } catch (_) {}
    }

    // 5. Fallback: innerText with full time pattern
    if (candidates.length === 0) {
      const text = document.body.innerText;
      if (text) {
        const m = text.match(timePattern);
        if (m) {
          const t = m[0].trim();
          candidates.push({ text: t, score: now - estimateMinutes(t) * 60000 });
        }
      }
    }

    if (candidates.length === 0) {
      console.log('[Skarbol] no post date found in DOM');
      return '';
    }

    candidates.sort((a, b) => b.score - a.score);
    const result = candidates[0].text;
    console.log('[Skarbol] post date found:', result);
    return result;
  }

  function estimateDays(text) {
    if (!text) return -1;
    const parsed = new Date(text);
    if (!isNaN(parsed.getTime())) {
      return Math.floor((Date.now() - parsed.getTime()) / 86400000);
    }
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
    if (days === -1) {
      score -= 1;
    } else if (days > 90) {
      score -= 4;
    } else if (days > 50) {
      score -= 2;
    }

    return Math.max(1, Math.min(10, score));
  }

  const observer = new MutationObserver(() => {
    clearTimeout(extractTimeout);
    extractTimeout = setTimeout(extractPageData, 4000);
  });

  observer.observe(document.body, { childList: true, subtree: true });

  window.addEventListener('load', () => {
    setTimeout(extractPageData, 4000);
  });

  setTimeout(extractPageData, 4000);

  function retryPostDate(delay, maxRetries) {
    let attempts = 0;
    function tryFind() {
      const date = extractLastPostDate();
      if (date) {
        chrome.storage.local.get('currentLead', (result) => {
          const lead = result.currentLead || {};
          if (!lead.last_post_date) {
            lead.last_post_date = date;
            lead.qualification_score = calculateScore(lead);
            chrome.storage.local.set({ currentLead: lead });
            console.log('[Skarbol] post date updated in storage:', date);
          }
        });
        return;
      }
      attempts++;
      if (attempts < maxRetries) {
        console.log('[Skarbol] post date not found, retry', attempts + 1, '/', maxRetries, 'in', delay, 'ms');
        setTimeout(tryFind, delay);
      } else {
        console.log('[Skarbol] post date retry exhausted');
      }
    }
    setTimeout(tryFind, 3000);
  }
  retryPostDate(6000, 7);

  // ── Retry phone & email (lazy-loaded contact section) ──────────
  function retryPhoneEmail(delay, maxRetries) {
    let attempts = 0;
    function tryFind() {
      chrome.storage.local.get('currentLead', (result) => {
        const lead = result.currentLead || {};
        if (lead.phone && lead.email) return;

        const phone = extractPhone();
        const email = extractEmail();
        let updated = false;

        if (phone && (!lead.phone || lead.phone === 'Not found')) {
          lead.phone = phone;
          updated = true;
          console.log('[Skarbol] phone found on retry:', phone);
        }
        if (email && (!lead.email || lead.email === 'Not found')) {
          lead.email = email;
          updated = true;
          console.log('[Skarbol] email found on retry:', email);
        }

        if (updated) {
          lead.qualification_score = calculateScore(lead);
          chrome.storage.local.set({ currentLead: lead });
          return;
        }

        attempts++;
        if (attempts < maxRetries) {
          setTimeout(tryFind, delay);
        } else {
          console.log('[Skarbol] phone/email retry exhausted');
        }
      });
    }
    setTimeout(tryFind, 3000);
  }
  retryPhoneEmail(5000, 8);
})();
