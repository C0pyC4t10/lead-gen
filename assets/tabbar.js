/* ── Scraven shared tab bar ─────────────────────────────────────
   Injects the Facebook-style bottom nav into every page, marks the
   active tab by pathname, hides on scroll-down, shows on scroll-up. */
(function () {
  if (window.__SCRAVEN_TABBAR__) return;
  window.__SCRAVEN_TABBAR__ = true;

  // ── Custom SVG icons (Lucide-inspired, Skarbol Tech brand style) ──
  var SVGS = {
    home: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3"/><line x1="12" y1="2" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="22"/><line x1="2" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="22" y2="12"/></svg>',
    extract: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13,2 4,14 11,14 10,22 20,10 13,10"/></svg>',
    leads: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5"/><path d="M3 12c0 1.66 4.03 3 9 3s9-1.34 9-3"/></svg>',
    history: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><polyline points="12,6 12,12 16,14"/></svg>',
    account: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="5"/><path d="M3 21v-2a7 7 0 0 1 7-7h4a7 7 0 0 1 7 7v2"/></svg>',
  };

  // 5 tabs — each with route, icon, label, and brand-color tint.
  var TABS = [
    { id: "home",    href: "/",         svg: SVGS.home,    label: "Home" },
    { id: "extract", href: "/extract",  svg: SVGS.extract, label: "Extract", primary: true },
    { id: "leads",   href: "/leads",    svg: SVGS.leads,   label: "Leads" },
    { id: "history", href: "/trash",    svg: SVGS.history, label: "History" },
    { id: "account", href: "/profile",  svg: SVGS.account, label: "Account", elemId: "tabBarAccount" },
  ];

  function injectStyles() {
    if (document.getElementById("scraven-tabbar-css")) return;
    var link = document.createElement("link");
    link.id = "scraven-tabbar-css";
    link.rel = "stylesheet";
    link.href = "/assets/tabbar.css";
    document.head.appendChild(link);
    document.body.classList.add("has-tab-bar");
  }

  function mountNav() {
    if (document.getElementById("tabBar")) return;
    var nav = document.createElement("nav");
    nav.id = "tabBar";
    nav.className = "tab-bar";
    nav.setAttribute("aria-label", "Primary navigation");
    nav.innerHTML = TABS.map(function (t) {
      var cls = "tab" + (t.primary ? " is-primary" : "");
      var idAttr = t.elemId ? ' id="' + t.elemId + '"' : "";
      return (
        '<a href="' + t.href + '"' + idAttr + ' class="' + cls + '" data-tab-id="' + t.id +
        '"><span class="ti" aria-hidden="true">' + (t.svg || t.icon || '') +
        '</span><span class="tl">' + t.label + '</span></a>'
      );
    }).join("");
    document.body.appendChild(nav);
    return nav;
  }

  function currentPath() {
    var p = window.location.pathname || "/";
    // Treat /index.html as home
    if (p === "/index.html") p = "/";
    p = p.replace(/\/+$/, "");
    return p || "/";
  }

  function syncActive() {
    var bar = document.getElementById("tabBar");
    if (!bar) return;
    var path = currentPath();
    var tabs = bar.querySelectorAll(".tab");
    var matched = false;
    for (var i = 0; i < tabs.length; i++) {
      var t = tabs[i];
      var href = (t.getAttribute("href") || "/").replace(/\/+$/, "") || "/";
      t.classList.remove("is-active");
      t.removeAttribute("aria-current");
      if (!matched && href === path) {
        t.classList.add("is-active");
        t.setAttribute("aria-current", "page");
        matched = true;
      }
    }
  }

  function setupScrollHide() {
    var bar = document.getElementById("tabBar");
    if (!bar) return;
    var lastY = window.scrollY || 0;
    var ticking = false;
    var THRESHOLD = 12;
    var TOP_BUFFER = 60;
    function apply() {
      var y = window.scrollY || window.pageYOffset;
      var delta = y - lastY;
      if (y < TOP_BUFFER) {
        bar.classList.remove("is-hidden");
      } else if (delta > THRESHOLD) {
        bar.classList.add("is-hidden");
      } else if (delta < -THRESHOLD) {
        bar.classList.remove("is-hidden");
      }
      lastY = y;
      ticking = false;
    }
    function onScroll() {
      if (!ticking) {
        window.requestAnimationFrame(apply);
        ticking = true;
      }
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    // Re-show briefly after a tab-tap so the active change is visible
    document.addEventListener("click", function (e) {
      var a = e.target && e.target.closest && e.target.closest(".tab");
      if (a) {
        bar.classList.remove("is-hidden");
        lastY = window.scrollY || 0;
      }
    });
  }

  function init() {
    injectStyles();
    mountNav();
    syncActive();
    setupScrollHide();
    window.addEventListener("popstate", syncActive);
    document.addEventListener("click", function (e) {
      var a = e.target && e.target.closest && e.target.closest(".tab");
      if (a) setTimeout(syncActive, 80);
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
