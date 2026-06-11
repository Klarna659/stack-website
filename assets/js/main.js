/* ===========================================================================
   Stack landing — interactions
   ---------------------------------------------------------------------------
   EDIT THESE 4 LINES WHEN YOU'RE READY (everything works without them):

     CONTACT_EMAIL : where feedback / referral / waitlist emails go.
     FORM_ENDPOINT : paste a Formspree / Web3Forms / Getform URL to collect
                     submissions in a dashboard. Leave "" and forms instead
                     open the visitor's email app pre-filled (works today).
     PLAY_URL      : your Google Play listing URL once the app is live.
     APP_STORE_URL : your App Store listing URL once the app is live.
                     While these are "", the store buttons say "coming soon"
                     and bounce visitors to the email-notify box.
   ========================================================================= */
const CONFIG = {
  CONTACT_EMAIL: "hello@trackyourstack.app",
  FORM_ENDPOINT: "",
  PLAY_URL: "",
  APP_STORE_URL: "",
};

/* --- screenshot gallery -------------------------------------------------- */
/* Add a screenshot = drop a 1080×2400 PNG in assets/img/screens/ and add one
   line below. That's it. */
const SCREENS = [
  { img: "assets/img/screens/today.png",  title: "Today",            sub: "Your streak, what's due, and what's still in your system" },
  { img: "assets/img/screens/stack.png",  title: "Your stack",       sub: "Every compound — grouped, dosed and scheduled" },
  { img: "assets/img/screens/trends.png", title: "Charts",           sub: "Weight, bloodwork, body-fat and adherence trends" },
  { img: "assets/img/screens/share.png",  title: "Share your stack", sub: "One card with your whole protocol — post it anywhere" },
  { img: "assets/img/screens/tools.png",  title: "All your tools",   sub: "Recon calc, doctor PDF and encrypted backup" },
];

document.addEventListener("DOMContentLoaded", () => {
  const yr = document.getElementById("year");
  if (yr) yr.textContent = new Date().getFullYear();
  buildGallery();
  wireLightbox();
  wireNav();
  wireStoreButtons();
  wireForms();
  wireEmailLinks();
  wireReveal();
  wireCounters();
});

/* --- count-up numbers in the hero showcase ------------------------------- */
function wireCounters() {
  const show = document.querySelector(".hero-showcase");
  if (!show) return;
  const run = () => show.querySelectorAll(".count").forEach(el => {
    const to = +el.dataset.to || 0, dur = 1400, start = performance.now();
    const tick = t => {
      const p = Math.min(1, (t - start) / dur);
      el.textContent = Math.round(p * to);
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });
  if (!("IntersectionObserver" in window)) return run();
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (e.isIntersecting) { run(); io.disconnect(); }
  }), { threshold: 0.15 });
  io.observe(show);
}

/* --- gallery ------------------------------------------------------------- */
function buildGallery() {
  const wrap = document.getElementById("gallery");
  if (!wrap) return;
  wrap.innerHTML = SCREENS.map(s => `
    <div class="shot">
      <figure>
        <div class="frame" data-full="${s.img}" role="button" tabindex="0" aria-label="Enlarge ${s.title}">
          <img src="${s.img}" alt="${s.title} — ${s.sub}" loading="lazy" />
        </div>
        <figcaption>${s.title}<small>${s.sub}</small></figcaption>
      </figure>
    </div>`).join("");
}

/* --- lightbox ------------------------------------------------------------ */
function wireLightbox() {
  const lb = document.getElementById("lightbox");
  const lbImg = document.getElementById("lbImg");
  const gallery = document.getElementById("gallery");
  const close = () => { if (!lb) return; lb.classList.remove("open"); lb.setAttribute("aria-hidden", "true"); lbImg && (lbImg.src = ""); };
  if (!lb || !lbImg || !gallery) return; // page may not have a gallery
  const open = (src, alt) => { lbImg.src = src; lbImg.alt = alt || ""; lb.classList.add("open"); lb.setAttribute("aria-hidden", "false"); };

  gallery.addEventListener("click", e => {
    const frame = e.target.closest(".frame");
    if (frame) open(frame.dataset.full, frame.querySelector("img").alt);
  });
  gallery.addEventListener("keydown", e => {
    if ((e.key === "Enter" || e.key === " ") && e.target.classList.contains("frame")) {
      e.preventDefault(); open(e.target.dataset.full, e.target.querySelector("img").alt);
    }
  });
  const lbClose = document.getElementById("lbClose");
  if (lbClose) lbClose.addEventListener("click", close);
  lb.addEventListener("click", e => { if (e.target === lb) close(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
}

/* --- nav (scrolled border + mobile menu) --------------------------------- */
function wireNav() {
  const nav = document.getElementById("nav");
  if (!nav) return;
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 8);
  onScroll();
  window.addEventListener("scroll", onScroll, { passive: true });

  const toggle = document.getElementById("navToggle");
  const links = document.getElementById("navLinks");
  if (!toggle || !links) return;
  toggle.addEventListener("click", () => {
    const open = links.classList.toggle("open");
    toggle.setAttribute("aria-expanded", open);
  });
  links.querySelectorAll("a").forEach(a => a.addEventListener("click", () => {
    links.classList.remove("open"); toggle.setAttribute("aria-expanded", "false");
  }));
}

/* --- store buttons ------------------------------------------------------- */
function wireStoreButtons() {
  document.querySelectorAll(".store-badge").forEach(btn => {
    const url = btn.dataset.store === "play" ? CONFIG.PLAY_URL : CONFIG.APP_STORE_URL;
    btn.addEventListener("click", () => {
      if (url) { window.open(url, "_blank", "noopener"); return; }
      // pre-launch: bounce to the notify box and gently flash it
      const notify = document.getElementById("notify");
      notify.scrollIntoView({ behavior: "smooth", block: "center" });
      const input = notify.querySelector("input");
      setTimeout(() => input && input.focus(), 500);
    });
  });
}

/* --- forms (POST to endpoint, else mailto fallback) ---------------------- */
function wireForms() {
  document.querySelectorAll("form[data-form]").forEach(form => {
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const kind = form.dataset.form;
      const msg = form.querySelector("[data-msg]");
      const btn = form.querySelector("button[type=submit]");
      const data = Object.fromEntries(new FormData(form).entries());

      // minimal validation
      for (const f of form.querySelectorAll("[required]")) {
        if (!String(f.value).trim()) { f.focus(); return showMsg(msg, "Please fill in the required fields.", "err"); }
      }
      const email = data.email;
      if (email && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
        return showMsg(msg, "That email doesn’t look right.", "err");
      }

      if (CONFIG.FORM_ENDPOINT) {
        try {
          btn.disabled = true; const old = btn.textContent; btn.textContent = "Sending…";
          const res = await fetch(CONFIG.FORM_ENDPOINT, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify({ _subject: subjectFor(kind), formType: kind, ...data }),
          });
          btn.disabled = false; btn.textContent = old;
          if (res.ok) { form.reset(); return showMsg(msg, successFor(kind), "ok"); }
          return showMsg(msg, "Something went wrong — email us at " + CONFIG.CONTACT_EMAIL, "err");
        } catch {
          btn.disabled = false;
          return mailtoFallback(kind, data, form, msg);
        }
      }
      return mailtoFallback(kind, data, form, msg);
    });
  });
}

function mailtoFallback(kind, data, form, msg) {
  const body = Object.entries(data)
    .filter(([, v]) => String(v).trim())
    .map(([k, v]) => `${cap(k)}: ${v}`).join("\n");
  const href = `mailto:${CONFIG.CONTACT_EMAIL}?subject=${encodeURIComponent(subjectFor(kind))}&body=${encodeURIComponent(body + "\n\n— sent from trackyourstack.app")}`;
  window.location.href = href;
  showMsg(msg, "Opening your email app — just hit send.", "ok");
}

const subjectFor = k => ({ referral: "Stack — Referral application", feedback: "Stack — Feedback", waitlist: "Stack — Notify me at launch" }[k] || "Stack");
const successFor = k => ({
  referral: "Thanks — your application’s in. We’ll be in touch.",
  feedback: "Got it — thanks. We read every message.",
  waitlist: "You’re on the list. We’ll email you at launch.",
}[k] || "Thanks!");
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);

function showMsg(el, text, type) {
  if (!el) return;
  el.textContent = text;
  el.className = "form-msg show " + type;
  if (type === "ok") setTimeout(() => el.classList.remove("show"), 6000);
}

/* --- email links --------------------------------------------------------- */
function wireEmailLinks() {
  document.querySelectorAll("[data-email-link]").forEach(a => {
    a.setAttribute("href", "mailto:" + CONFIG.CONTACT_EMAIL);
  });
}

/* --- reveal on scroll ---------------------------------------------------- */
function wireReveal() {
  const els = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) { els.forEach(el => el.classList.add("in")); return; }
  // Immediately reveal anything already in viewport (avoids flash on load)
  els.forEach(el => { const r = el.getBoundingClientRect(); if (r.top < window.innerHeight) el.classList.add("in"); });
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en, i) => {
      if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
  els.forEach(el => io.observe(el));
}
