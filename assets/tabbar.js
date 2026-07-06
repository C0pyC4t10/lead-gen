/* ── Scraven shared tab bar ─────────────────────────────────────
   Injects the Facebook-style bottom nav into every page, marks the
   active tab by pathname, hides on scroll-down, shows on scroll-up. */
(function () {
  if (window.__SCRAVEN_TABBAR__) return;
  window.__SCRAVEN_TABBAR__ = true;

  // 5 tabs — each with route, icon, label, and brand-color tint.
  // 'History' replaces the previous 'Pricing' tab per user request.
  var TABS = [
    { id: "home",    href: "/",         icon: "\ud83c\udfe0", label: "Home" },
    { id: "extract", href: "/extract",  icon: "\u26a1",     label: "Extract", primary: true },
    { id: "leads",   href: "/leads",    icon: "\ud83d\udcca", label: "Leads" },
    { id: "history", href: "/trash",    icon: "\ud83d\udd52", label: "History" },
    { id: "account", href: "/profile",  icon: "\ud83d\ude64", label: "Account", elemId: "tabBarAccount" },
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
        '"><span class="ti" aria-hidden="true">' + t.icon +
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
