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
