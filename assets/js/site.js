/* Stack — shared site JS. Progressive enhancement only: every page works
   with JS disabled (static HTML); this adds nav toggle, scroll reveal,
   gallery lightbox, mailto fallback links and the library filter. */
(function () {
  "use strict";

  /* nav scrolled border + mobile toggle */
  var nav = document.getElementById("nav");
  if (nav) {
    var onScroll = function () {
      nav.classList.toggle("scrolled", window.scrollY > 8);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }
  var toggle = document.getElementById("navToggle");
  var links = document.getElementById("navLinks");
  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  /* theme toggle — default follows the OS; a click pins the choice (localStorage).
     Mirrors the app's "one world per theme, system default" behaviour. */
  var themeBtn = document.getElementById("themeToggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var root = document.documentElement;
      var cur = root.getAttribute("data-theme");
      var sysDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
      var isDark = cur ? cur === "dark" : sysDark;
      var next = isDark ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try { localStorage.setItem("stack-theme", next); } catch (e) {}
    });
  }

  /* pricing month/year toggle (landing) */
  var priceToggle = document.querySelector(".price-toggle");
  if (priceToggle) {
    var pbtns = priceToggle.querySelectorAll("button");
    var show = function (sel, on) {
      document.querySelectorAll(sel).forEach(function (el) { el.hidden = !on; });
    };
    pbtns.forEach(function (b) {
      b.addEventListener("click", function () {
        pbtns.forEach(function (x) { x.classList.remove("active"); });
        b.classList.add("active");
        var year = b.getAttribute("data-bill") === "year";
        show("[data-price-month]", !year); show("[data-price-year]", year);
        show("[data-anchor-month]", !year); show("[data-anchor-year]", year);
        var per = document.querySelector("[data-per]");
        if (per) per.textContent = year ? "/yr" : "/mo";
        // Keep the Plus buy button's SKU in sync with the toggle, else a Yearly
        // selection would check out on the monthly plan.
        var buyBtn = document.querySelector("[data-plan-toggle]");
        if (buyBtn) buyBtn.setAttribute("data-plan", year ? "plusAnnual" : "plusMonthly");
      });
    });
  }

  /* reveal on scroll (finite, once) */
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("in");
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    document.querySelectorAll(".reveal").forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("in"); });
  }

  /* email links */
  var EMAIL = "hello@trackyourstack.app";
  document.querySelectorAll("[data-email-link]").forEach(function (a) {
    a.setAttribute("href", "mailto:" + EMAIL);
  });

  /* ---- config: paste a real endpoint at launch and the forms POST to it ----
     WAITLIST_ENDPOINT: a Formspark/Buttondown/Formspree URL that accepts a JSON
     or form POST with an "email" field. Empty string → mailto fallback so the
     site still captures interest today with zero backend. */
  var WAITLIST_ENDPOINT = ""; // e.g. "https://submit-form.com/abcd1234"

  /* waitlist (hero) — POST to endpoint when set, else mailto */
  document.querySelectorAll('form[data-form="waitlist"]').forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = form.querySelector('[name="email"]');
      var email = (input && input.value || "").trim();
      var note = document.querySelector(".hero-note[data-msg]") || form.querySelector("[data-msg]");
      if (!email || email.indexOf("@") === -1) {
        if (note) note.textContent = "Enter a valid email and we'll keep you posted.";
        return;
      }
      if (WAITLIST_ENDPOINT) {
        if (note) note.textContent = "Adding you…";
        fetch(WAITLIST_ENDPOINT, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Accept": "application/json" },
          body: JSON.stringify({ email: email, source: "stack-website-hero" })
        }).then(function (r) {
          if (note) note.textContent = r.ok
            ? "You're on the list — we'll email you at launch."
            : "Hmm, that didn't go through. Email us at " + EMAIL + ".";
          if (r.ok && input) { input.value = ""; }
        }).catch(function () {
          if (note) note.textContent = "Network hiccup — email us at " + EMAIL + " instead.";
        });
      } else {
        window.location.href = "mailto:" + EMAIL +
          "?subject=" + encodeURIComponent("Notify me when Stack launches") +
          "&body=" + encodeURIComponent("Add me to the launch list: " + email);
        if (note) note.textContent = "Opening your email app — hit send and you're on the list.";
      }
    });
  });

  /* Plus buy buttons ([data-plan]) — go to the RevenueCat Web Billing checkout
     when it's configured (carrying the signed-in user id so the entitlement
     attaches to the right account), else fall back to the notify flow. */
  var RAIL = window.STACK_RAIL;
  document.querySelectorAll("[data-plan]").forEach(function (b) {
    b.addEventListener("click", function () {
      var key = b.getAttribute("data-plan");
      if (RAIL && RAIL.checkoutReady && RAIL.checkoutReady(key)) {
        var url = RAIL.checkout[key];
        var go = function (uid) {
          if (uid) url += (url.indexOf("?") === -1 ? "?" : "&") + "app_user_id=" + encodeURIComponent(uid);
          window.location.href = url;
        };
        if (window.StackAccount) {
          window.StackAccount.ensureSession().then(function (s) {
            go(s && (s.user_id || (window.StackAccount.decodeJwtEmail(s.access_token) || {}).user_id));
          }).catch(function () { go(null); });
        } else { go(null); }
        return;
      }
      // not configured yet → notify at launch
      var email = (RAIL && RAIL.contactEmail) || "hello@trackyourstack.app";
      window.location.href = "mailto:" + email +
        "?subject=" + encodeURIComponent("Notify me when Stack Plus launches") +
        "&body=" + encodeURIComponent("Tell me when I can get Plus.");
    });
  });

  /* store badges — until store URLs exist, scroll to the notify line */
  document.querySelectorAll(".store-badge[data-store]").forEach(function (b) {
    b.addEventListener("click", function () {
      var urls = { play: "", apple: "" }; // paste real store URLs at launch
      var u = urls[b.getAttribute("data-store")];
      if (u) { window.open(u, "_blank", "noopener"); return; }
      window.location.href = "mailto:" + EMAIL +
        "?subject=Notify%20me%20when%20Stack%20launches&body=Tell%20me%20when%20Stack%20is%20live.";
    });
  });

  /* screens gallery (landing only) */
  var gallery = document.getElementById("gallery");
  if (gallery) {
    var shots = [
      ["assets/img/screens/today.png", "Today screen — protocol ledger with check-rings"],
      ["assets/img/screens/stack.png", "Your stack — compounds grouped by category"],
      ["assets/img/screens/trends.png", "Charts — weight, lifts, adherence and bloodwork"],
      ["assets/img/screens/tools.png", "Tools — calculators, reports and backups"],
      ["assets/img/screens/share.png", "Flex card — share your stack as an image"]
    ];
    shots.forEach(function (s) {
      var btn = document.createElement("button");
      btn.className = "shot reveal";
      var img = document.createElement("img");
      img.src = s[0];
      img.alt = s[1];
      img.loading = "lazy";
      img.width = 1080; img.height = 2400;
      btn.appendChild(img);
      btn.addEventListener("click", function () { openLB(s[0], s[1]); });
      gallery.appendChild(btn);
      if (io) io.observe(btn);
    });
  }
  var lb = document.getElementById("lightbox");
  var lbImg = document.getElementById("lbImg");
  function openLB(src, alt) {
    if (!lb) return;
    lbImg.src = src; lbImg.alt = alt;
    lb.classList.add("open");
    lb.setAttribute("aria-hidden", "false");
  }
  if (lb) {
    lb.addEventListener("click", function (e) {
      if (e.target === lb || e.target.id === "lbClose") {
        lb.classList.remove("open");
        lb.setAttribute("aria-hidden", "true");
      }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { lb.classList.remove("open"); lb.setAttribute("aria-hidden", "true"); }
    });
  }

  /* forms → mailto fallback (no backend yet); serializes every named field */
  document.querySelectorAll("form[data-form]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var kind = form.getAttribute("data-form") || "form";
      var subjBits = [];
      var lines = [];
      form.querySelectorAll("input[name], select[name], textarea[name]").forEach(function (el) {
        if (!el.value) return;
        if (el.name === "type" || el.name === "name") subjBits.push(el.value);
        lines.push(el.name.charAt(0).toUpperCase() + el.name.slice(1) + ": " + el.value);
      });
      var subject = "[Stack] " + (kind === "referral" ? "Referral application" : (subjBits[0] || "Feedback"));
      window.location.href = "mailto:" + EMAIL +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(lines.join("\n"));
      var out = form.querySelector("[data-msg]");
      if (out) out.textContent = "Opening your email app…";
    });
  });

  /* library filter (compounds index) */
  var libSearch = document.getElementById("libSearch");
  if (libSearch) {
    var cards = Array.prototype.slice.call(document.querySelectorAll(".comp-card"));
    var sections = Array.prototype.slice.call(document.querySelectorAll(".lib-section"));
    var chips = Array.prototype.slice.call(document.querySelectorAll(".cat-chip"));
    var count = document.getElementById("libCount");
    var activeCat = "all";

    function apply() {
      var q = libSearch.value.trim().toLowerCase();
      var shown = 0;
      cards.forEach(function (c) {
        var hay = (c.getAttribute("data-search") || "").toLowerCase();
        var cat = c.getAttribute("data-cat");
        var ok = (activeCat === "all" || cat === activeCat) && (!q || hay.indexOf(q) !== -1);
        c.style.display = ok ? "" : "none";
        if (ok) shown++;
      });
      sections.forEach(function (s) {
        var any = s.querySelector('.comp-card:not([style*="none"])');
        s.style.display = any ? "" : "none";
      });
      if (count) count.textContent = shown + " compound" + (shown === 1 ? "" : "s");
    }
    libSearch.addEventListener("input", apply);
    chips.forEach(function (ch) {
      ch.addEventListener("click", function () {
        chips.forEach(function (x) { x.classList.remove("active"); });
        ch.classList.add("active");
        activeCat = ch.getAttribute("data-cat");
        apply();
      });
    });
    apply();
  }
})();
