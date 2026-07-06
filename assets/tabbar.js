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

  // Custom SVG: Qualified — check-in-circle (target hit)
  SVGS.qualified = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2" fill="currentColor"/></svg>';

  // 5 tabs — each with route, icon, label, and brand-color tint.
  // History is moved into /leads as a tab (Extract/History), so the bottom
  // bar gets Qualified instead.
  var TABS = [
    { id: "home",      href: "/",          svg: SVGS.home,      label: "Home" },
    { id: "extract",   href: "/extract",   svg: SVGS.extract,   label: "Extract", primary: true },
    { id: "leads",     href: "/leads",     svg: SVGS.leads,     label: "Leads" },
    { id: "qualified", href: "/qualified", svg: SVGS.qualified, label: "Qualified" },
    { id: "account",   href: "/profile",   svg: SVGS.account,   label: "Account", elemId: "tabBarAccount" },
  ];

  function injectStyles() {
    if (document.getElementById("scraven-tabbar-css")) return;
    var link = document.createElement("link");
    link.id = "scraven-tabbar-css";
    link.rel = "stylesheet";
    link.href = "/assets/tabbar.css?v=4";
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

  // ── Top-bar hamburger drawer (mobile only) ─────────────────────
  // Injects a hamburger button into the existing <nav class="nav"> on
  // mobile widths, and a fullscreen drawer with all nav items + auth
  // actions. Desktop viewports keep the existing inline nav untouched.

  function getUser() {
    try { return JSON.parse(localStorage.getItem("skarbol_user") || "null"); }
    catch (e) { return null; }
  }

  function getToken() {
    return localStorage.getItem("skarbol_token") || "";
  }

  function escAttr(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]; }); }

  function buildDrawerItems() {
    var u = getUser();
    var loggedIn = !!(u && u.id);
    var role = u && u.role;
    var isAdmin = role === "admin" || role === "super_admin";
    // Logout is intentionally only shown on the Profile page (and inside
    // the mountProfile dropdown on every page) so the user has one clear
    // place to sign out — the profile page — instead of a Logout button
    // on every nav.
    var onProfile = window.location.pathname === "/profile" || window.location.pathname === "/profile.html";
    var items = [
      { href: "/",         icon: "home",    label: "Home" },
      { href: "/extract",  icon: "extract", label: "Extract", primary: true },
      { href: "/leads",    icon: "leads",   label: "Leads" },
      { href: "/qualified",icon: "qualified", label: "Qualified" },
      { href: "/trash",    icon: "trash",   label: "Trash" },
      { href: "/pricing",  icon: "pricing", label: "Pricing" },
    ];
    if (loggedIn) {
      items.push({ divider: true, label: "Account" });
      items.push({ href: "/profile", icon: "account", label: "Profile" });
      if (isAdmin) items.push({ href: "/admin", icon: "admin", label: "Admin" });
      if (onProfile) items.push({ action: "logout", icon: "logout", label: "Logout" });
    } else {
      items.push({ divider: true });
      items.push({ href: "/login",    icon: "login",    label: "Sign In", cta: true });
      items.push({ href: "/register", icon: "register", label: "Create Account" });
    }
    return items;
  }

  function iconSVG(name) {
    var extra = {
      pricing: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
      admin:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
      login:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><polyline points="10 17 15 12 10 7"/><line x1="15" y1="12" x2="3" y2="12"/></svg>',
      register:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="19" y1="8" x2="19" y2="14"/><line x1="22" y1="11" x2="16" y2="11"/></svg>',
      logout:  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
      qualified:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>',
      trash:   '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/></svg>',
    };
    return extra[name] || SVGS[name] || "";
  }

  function mountProfile() {
    var topNav = document.querySelector("nav.nav, header nav, .nav");
    if (!topNav) return;
    if (document.getElementById("navProfile")) return;

    var u = getUser();
    if (!u || !u.id) return;  // only inject when signed in

    var role = u.role;
    var isAdmin = role === "admin" || role === "super_admin";
    // Logout lives only on the Profile page. The mountProfile dropdown
    // otherwise only shows Profile (+ Admin for admins) so it doesn't
    // duplicate the Logout button on every page.
    var onProfile = window.location.pathname === "/profile" || window.location.pathname === "/profile.html";

    var profile = document.createElement("div");
    profile.id = "navProfile";
    profile.className = "nav-profile";
    profile.setAttribute("aria-label", (u.name || "Profile") + " — " + (u.email || ""));
    var initial = (u.name || u.email || "?").charAt(0).toUpperCase();
    profile.innerHTML =
      '<a href="/profile" class="nav-profile-avatar" id="navProfileAvatar" aria-hidden="true" title="' + escAttr(u.email || "") + '">' + escAttr(initial) + '</a>' +
      '<button type="button" class="nav-profile-btn" id="navProfileBtn" aria-haspopup="menu" aria-expanded="false">' +
        '<span class="nav-profile-name">' + escAttr(u.name || "Account") + '</span>' +
        '<svg class="nav-profile-caret" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>' +
      '</button>' +
      '<div class="nav-profile-menu" id="navProfileMenu" role="menu">' +
        '<div class="nav-profile-menu-head">' +
          '<div class="nav-profile-menu-avatar" id="navProfileMenuAvatar">' + escAttr(initial) + '</div>' +
          '<div class="nav-profile-menu-meta">' +
            '<div class="nav-profile-menu-name">' + escAttr(u.name || "") + '</div>' +
            '<div class="nav-profile-menu-email">' + escAttr(u.email || "") + '</div>' +
            '<div class="nav-profile-menu-role">' + escAttr(role || "user") + '</div>' +
          '</div>' +
        '</div>' +
        '<a href="/profile" class="nav-profile-menu-item" role="menuitem"><span class="di">' + iconSVG("account") + '</span><span class="dl">Profile</span></a>' +
        (isAdmin ? '<a href="/admin" class="nav-profile-menu-item" role="menuitem"><span class="di">' + iconSVG("admin") + '</span><span class="dl">Admin</span></a>' : '') +
        (onProfile ? '<button type="button" class="nav-profile-menu-item is-logout" data-action="logout" role="menuitem"><span class="di">' + iconSVG("logout") + '</span><span class="dl">Logout</span></button>' : '') +
      '</div>';

    topNav.appendChild(profile);

    // Hide any pre-existing duplicate profile / admin / logout links in
    // the page header. The new mountProfile dropdown is the single source
    // of truth for these actions. The lead usage counter is hidden on
    // every page except /profile — that page has a richer stat panel
    // and doesn't need the small nav badge cluttering every other page.
    var dup = topNav.querySelectorAll('#profileLink, .header-profile, #adminLink, #logoutBtn, .logout-btn');
    for (var i = 0; i < dup.length; i++) dup[i].style.display = 'none';
    var leadBadge = topNav.querySelector('#leadBadge, .lead-badge');
    if (leadBadge) {
      if (onProfile) leadBadge.style.display = 'inline-flex';
      else leadBadge.style.display = 'none';
    }

    var btn = document.getElementById("navProfileBtn");
    var menu = document.getElementById("navProfileMenu");
    function setOpen(open) {
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      menu.classList.toggle("is-open", open);
    }
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(btn.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("click", function (e) {
      if (menu.classList.contains("is-open") && !menu.contains(e.target) && !btn.contains(e.target)) {
        setOpen(false);
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && menu.classList.contains("is-open")) setOpen(false);
    });
    menu.addEventListener("click", function (e) {
      var link = e.target.closest && e.target.closest("[data-action], a, button");
      if (!link) return;
      if (link.dataset && link.dataset.action === "logout") {
        e.preventDefault();
        var tok = getToken();
        if (tok && window.fetch) {
          fetch(window.location.origin + "/api/auth/logout", { method: "POST", headers: { "Authorization": "Bearer " + tok } }).catch(function () {});
        }
        try { localStorage.removeItem("skarbol_token"); localStorage.removeItem("skarbol_user"); } catch (e) {}
        window.location.href = "/";
        return;
      }
      setOpen(false);
    });

    // Hydrate avatar (both header + menu) with the user's picture from Mongo
    function hydrate() {
      var imgUrl = window.location.origin + "/api/avatars/" + u.id + ".jpg?t=" + Date.now();
      var testImg = new Image();
      testImg.onload = function () {
        var targets = [
          document.getElementById("navProfileAvatar"),
          document.getElementById("navProfileMenuAvatar")
        ];
        for (var k = 0; k < targets.length; k++) {
          var t = targets[k];
          if (!t) continue;
          t.innerHTML = "";
          t.style.background = "none";
          t.style.padding = "0";
          var im = document.createElement("img");
          im.src = imgUrl;
          im.alt = "";
          im.style.width = "100%";
          im.style.height = "100%";
          im.style.objectFit = "cover";
          im.style.borderRadius = "50%";
          t.appendChild(im);
        }
      };
      testImg.onerror = function () {};
      testImg.src = imgUrl;
    }
    hydrate();
  }

  function mountBurger() {
    var topNav = document.querySelector("nav.nav, header nav, .nav");
    if (!topNav) return;
    var existingBurger = document.getElementById("navBurger");
    var existingDrawer = document.getElementById("navDrawer");

    // If a page already ships its own burger (e.g. homepage with a brand-colored one),
    // we still need to inject the drawer + wire the toggle to that burger.
    var burger = existingBurger;
    if (!burger) {
      burger = document.createElement("button");
      burger.type = "button";
      burger.id = "navBurger";
      burger.className = "nav-burger";
      burger.setAttribute("aria-label", "Open menu");
      burger.setAttribute("aria-expanded", "false");
      burger.setAttribute("aria-controls", "navDrawer");
      burger.innerHTML = '<span class="bar"></span><span class="bar"></span><span class="bar"></span>';
      topNav.appendChild(burger);
    } else {
      burger.setAttribute("aria-controls", "navDrawer");
    }

    // Hide nav-links on mobile so the burger + profile sit clean at the right.
    // The drawer replaces them on small viewports.
    var navLinks = topNav.querySelector('.nav-links');
    if (navLinks) navLinks.classList.add('tabbar-hide-mobile');

    var drawer = existingDrawer;
    if (!drawer) {
      drawer = document.createElement("div");
      drawer.id = "navDrawer";
      drawer.className = "nav-drawer";
      drawer.setAttribute("role", "dialog");
      drawer.setAttribute("aria-label", "Site navigation");
    var user = getUser();
    var userLabel = user && user.name ? user.name : "";
    var userEmail = user && user.email ? user.email : "";
    var html = '';
    if (userLabel || userEmail) {
      html += '<div class="drawer-user">' +
        '<div class="drawer-avatar" id="drawerAvatar">' + escAttr((userLabel || "?").charAt(0).toUpperCase()) + '</div>' +
        '<div class="drawer-user-meta"><div class="drawer-user-name">' + escAttr(userLabel) + '</div><div class="drawer-user-email">' + escAttr(userEmail) + '</div></div>' +
        '</div>';
    } else {
      html += '<div class="drawer-eyebrow">Scraven</div>';
    }
    html += buildDrawerItems().map(function (it) {
      if (it.divider) {
        return it.label ? '<div class="drawer-section">' + escAttr(it.label) + '</div>' : '<div class="drawer-divider"></div>';
      }
      var cls = "drawer-link";
      if (it.primary) cls += " is-primary";
      if (it.cta)     cls += " is-cta";
      if (it.action === "logout") cls += " is-logout";
      // Mark current page as active so the mobile drawer reflects where
      // the user is right now (matches the desktop top-nav + bottom tab).
      if (it.href && isCurrentPath(it.href)) cls += " is-current";
      if (it.action) {
        return '<button type="button" class="' + cls + '" data-action="' + it.action + '"><span class="di">' + iconSVG(it.icon) + '</span><span class="dl">' + escAttr(it.label) + '</span></button>';
      }
      return '<a href="' + escAttr(it.href) + '" class="' + cls + '"><span class="di">' + iconSVG(it.icon) + '</span><span class="dl">' + escAttr(it.label) + '</span></a>';
    }).join("");
    drawer.innerHTML = html;
    if (!existingDrawer) document.body.appendChild(drawer);
    }

    function setOpen(open) {
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      drawer.classList.toggle("is-open", open);
      document.body.classList.toggle("nav-drawer-open", open);
    }

    burger.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(burger.getAttribute("aria-expanded") !== "true");
    });
    drawer.addEventListener("click", function (e) {
      var link = e.target.closest && e.target.closest(".drawer-link");
      if (link) {
        if (link.dataset && link.dataset.action === "logout") {
          e.preventDefault();
          var tok = getToken();
          if (tok && window.fetch) {
            fetch(window.location.origin + "/api/auth/logout", { method: "POST", headers: { "Authorization": "Bearer " + tok } }).catch(function () {});
          }
          try {
            localStorage.removeItem("skarbol_token");
            localStorage.removeItem("skarbol_user");
          } catch (e) {}
          window.location.href = "/";
          return;
        }
        setOpen(false);
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && drawer.classList.contains("is-open")) setOpen(false);
    });
    drawer.addEventListener("click", function (e) {
      if (e.target === drawer) setOpen(false);
    });
    // Auto-close drawer if viewport grows to desktop
    var mq = window.matchMedia("(min-width: 769px)");
    var onMq = function (ev) { if (ev.matches) setOpen(false); };
    if (mq.addEventListener) mq.addEventListener("change", onMq);
    else if (mq.addListener) mq.addListener(onMq);

    // Hydrate drawer avatar with picture if available
    var av = document.getElementById("drawerAvatar");
    if (av && user && user.id) {
      var img = new Image();
      img.alt = "";
      img.onload = function () {
        av.innerHTML = "";
        av.style.background = "none";
        av.style.padding = "0";
        av.appendChild(img);
      };
      img.onerror = function () {};
      img.src = window.location.origin + "/api/avatars/" + user.id + ".jpg?t=" + Date.now();
    }
  }

  function currentPath() {
    var p = window.location.pathname || "/";
    // Treat /index.html as home
    if (p === "/index.html") p = "/";
    p = p.replace(/\/+$/, "");
    return p || "/";
  }

  // True when the given href matches the current path. Used by the mobile
  // drawer to mark the current page (so the user can see which section
  // they're in even when the drawer is open).
  function isCurrentPath(href) {
    if (!href) return false;
    var h = href.split("#")[0].replace(/\/+$/, "") || "/";
    var p = currentPath();
    if (h === "/") return p === "/";
    return p === h || p.indexOf(h + "/") === 0;
  }

  function syncActive() {
    var bar = document.getElementById("tabBar");
    if (!bar) return;
    var path = currentPath();
    var hash = window.location.hash || "";
    var tabs = bar.querySelectorAll(".tab");
    // First clear all active states
    for (var k = 0; k < tabs.length; k++) {
      tabs[k].classList.remove("is-active");
      tabs[k].removeAttribute("aria-current");
    }
    // For each tab, decide if it should be active. A tab is active when
    // its path matches the current path AND (for tabs with a #hash) the
    // current hash also matches. The PRIMARY tab (Extract) is the visual
    // center of the bottom bar but it should NEVER auto-highlight just
    // because of the `is-primary` class — it must actually match the page.
    var matched = false;
    for (var i = 0; i < tabs.length; i++) {
      var t = tabs[i];
      var href = t.getAttribute("href") || "/";
      var hParts = href.split("#");
      var hPath = (hParts[0] || "/").replace(/\/+$/, "") || "/";
      var hHash = hParts[1] ? "#" + hParts[1] : "";
      if (hPath === path) {
        // For path-only matches (no hash), accept the current hash too —
        // e.g. on /leads#history, the /leads tab can also light up.
        if (!hHash || hHash === hash || !hash) {
          t.classList.add("is-active");
          t.setAttribute("aria-current", "page");
          matched = true;
        }
      }
    }
    // Hard fallback: if no tab matched the current path, mark the tab
    // whose href starts with the current path. Prevents the Extract
    // "stuck-active" bug on pages that have no direct match in TABS.
    if (!matched) {
      for (var j = 0; j < tabs.length; j++) {
        var tj = tabs[j];
        var hp = (tj.getAttribute("href") || "/").split("#")[0].replace(/\/+$/, "") || "/";
        if (hp !== "/" && path.indexOf(hp) === 0) {
          tj.classList.add("is-active");
          tj.setAttribute("aria-current", "page");
          break;
        }
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
    mountProfile();
    mountBurger();
    syncActive();
    setupScrollHide();
    window.addEventListener("popstate", syncActive);
    window.addEventListener("hashchange", syncActive);
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
