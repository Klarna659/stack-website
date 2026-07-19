"""Builds the Stack compound library: static pages from assets/data/compounds.json.

  python tools/build_library.py

Emits:
  compounds/index.html           catalog (search + category chips, static list)
  compounds/<slug>/index.html    one page per compound (112)
  sitemap.xml                    every page on the site

Static HTML on purpose: AI crawlers and Google both index the full content
with zero JS. The dataset is the app's own curated seed (what-it-is /
mechanism / use-context / FDA status / half-life / storage / citations), so
every page carries unique substance — no template-only thin pages.
"""
from __future__ import annotations

import html
import json
import math
import os
import re
import unicodedata
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "https://trackyourstack.app"  # swap when DNS lands
REVIEWED = "2026-06-11"
TODAY = date(2026, 6, 11)

CATS = {
    "GLP-1": ("glp-1", "GLP-1 & incretins", "Semaglutide, tirzepatide and the wider incretin class."),
    "TRT/ester": ("trt", "Testosterone esters", "Prescription testosterone preparations used in TRT."),
    "peptide": ("peptides", "Peptides", "Research and therapeutic peptides, from BPC-157 to CJC-1295."),
    "ancillary": ("ancillaries", "Ancillaries", "Support compounds commonly run alongside a protocol."),
    "oral_compound": ("orals", "Oral compounds", "Tablets and capsules — prescription and research orals."),
    "SARM": ("sarms", "SARMs", "Selective androgen receptor modulators."),
    "supplement": ("supplements", "Supplements", "Everyday staples — creatine, vitamin D, magnesium and more."),
}
CAT_ORDER = ["GLP-1", "TRT/ester", "peptide", "ancillary", "oral_compound", "SARM", "supplement"]

STORAGE = {
    "room_temp": "Room temperature",
    "fridge": "Refrigerate (2–8 °C)",
    "fridge_after_recon": "Fridge after reconstitution",
    "freezer": "Freezer",
    "cool_dark": "Cool, dark place",
}

FORM = {
    "injection": "Injection",
    "oral": "Oral",
    "capsule": "Capsule",
    "tablet": "Tablet",
    "nasal": "Nasal spray",
    "topical": "Topical",
    "sublingual": "Sublingual",
    "powder": "Powder",
}

# Common marketed / community strengths (ported from the app's
# compound_catalog.dart — factual options, not recommendations).
def common_strengths(name: str) -> list[str]:
    n = name.lower()
    if "semaglutide" in n: return ["0.25 mg", "0.5 mg", "1 mg", "1.7 mg", "2.4 mg"]
    if "tirzepatide" in n: return ["2.5 mg", "5 mg", "7.5 mg", "10 mg", "12.5 mg", "15 mg"]
    if "retatrutide" in n: return ["2 mg", "4 mg", "8 mg", "12 mg"]
    if "liraglutide" in n: return ["0.6 mg", "1.2 mg", "1.8 mg", "3 mg"]
    if "testosterone" in n: return ["100 mg", "120 mg", "150 mg", "200 mg"]
    if "nandrolone" in n or "deca" in n: return ["100 mg", "200 mg", "300 mg"]
    if "bpc" in n: return ["250 mcg", "500 mcg", "1 mg"]
    if "tb-500" in n or "thymosin" in n: return ["2 mg", "2.5 mg", "5 mg"]
    if "ghk" in n: return ["1 mg", "2 mg", "3 mg"]
    if "ipamorelin" in n or "ghrp" in n: return ["100 mcg", "200 mcg", "300 mcg"]
    if "cjc" in n: return ["100 mcg", "200 mcg", "300 mcg"]
    if "mk-677" in n or "ibutamoren" in n: return ["10 mg", "15 mg", "25 mg"]
    if "melanotan" in n or "mt-2" in n: return ["250 mcg", "500 mcg", "1 mg"]
    if "pt-141" in n or "bremelanotide" in n: return ["0.5 mg", "1 mg", "2 mg"]
    if "semax" in n or "selank" in n: return ["300 mcg", "600 mcg", "900 mcg"]
    return []


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s


def fmt_half_life(hours: float | None) -> str | None:
    if not hours:
        return None
    if hours < 1:
        return f"≈ {int(round(hours * 60))} minutes"
    if hours < 48:
        v = int(hours) if float(hours).is_integer() else round(hours, 1)
        return f"≈ {v} hours"
    days = hours / 24.0
    d = int(days) if days.is_integer() else round(days, 1)
    return f"≈ {d} days ({int(hours)} h)"


def clearance_note(hours: float | None) -> str | None:
    """~97% cleared after 5 half-lives — a tracking-relevant, neutral fact."""
    if not hours:
        return None
    total = hours * 5
    if total < 48:
        return f"≈ {int(round(total))} hours"
    return f"≈ {round(total / 24)} days"


def esc(s: str | None) -> str:
    return html.escape(s or "", quote=True)


def head(title: str, desc: str, canonical: str, assets: str, jsonld: list | None = None,
         og_type: str = "article") -> str:
    blocks = ""
    for j in jsonld or []:
        blocks += f'\n  <script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(desc)}" />
  <meta name="theme-color" content="#FBFBFA" media="(prefers-color-scheme: light)" />
  <meta name="theme-color" content="#0B0B0F" media="(prefers-color-scheme: dark)" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(desc)}" />
  <meta property="og:type" content="{og_type}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:image" content="{BASE_URL}/assets/img/og.png" />
  <meta property="og:site_name" content="Stack" />
  <meta name="twitter:card" content="summary_large_image" />
  <link rel="icon" type="image/svg+xml" href="{assets}/img/icon.svg" />
  <link rel="icon" type="image/png" href="{assets}/img/icon.png" />
  <link rel="apple-touch-icon" href="{assets}/img/icon.png" />
  <link rel="preload" href="{assets}/fonts/inter-subset.woff2" as="font" type="font/woff2" crossorigin />
  <link rel="stylesheet" href="{assets}/css/mono.css?v=4" />{blocks}
  <script>(function(){{try{{var t=localStorage.getItem("stack-theme");if(t==="dark"||t==="light")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}}})();</script>
</head>"""


def mark(size: int = 36) -> str:
    # Three stacked discs — the app icon. Theme-aware ink tones (never gold:
    # the brand mark isn't an "earned" moment). Fills resolve from mono.css vars.
    return f"""<svg class="brand-mark" width="{size}" height="{size}" viewBox="0 0 40 40" aria-hidden="true">
          <ellipse cx="20" cy="13" rx="13" ry="3.4" fill="var(--brand-1)"/>
          <ellipse cx="20" cy="21" rx="13" ry="3.4" fill="var(--brand-2)"/>
          <ellipse cx="20" cy="29" rx="13" ry="3.4" fill="var(--brand-3)"/>
        </svg>"""


def theme_toggle() -> str:
    return """<button class="theme-toggle" id="themeToggle" type="button" aria-label="Switch theme" title="Switch theme">
        <svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M4.2 4.2l1.8 1.8M18 18l1.8 1.8M2 12h2.5M19.5 12H22M4.2 19.8 6 18M18 6l1.8-1.8"/></svg>
        <svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>
      </button>"""


def nav(root: str, current: str = "") -> str:
    def cur(k: str) -> str:
        return ' aria-current="page"' if k == current else ""
    return f"""
  <header class="nav" id="nav">
    <div class="container nav-inner">
      <a href="{root}" class="brand" aria-label="Stack — home">
        {mark(36)}
        <span class="brand-word">Stack</span>
      </a>
      <div class="nav-right">
        <nav class="nav-links" id="navLinks">
          <a href="{root}#features"{cur('features')}>Features</a>
          <a href="{root}pricing/"{cur('pricing')}>Pricing</a>
          <a href="{root}compounds/"{cur('compounds')}>Compounds</a>
          <a href="{root}guides/"{cur('guides')}>Guides</a>
        </nav>
        {theme_toggle()}
        <a href="{root}#download" class="nav-cta">Get the app</a>
        <button class="nav-toggle" id="navToggle" aria-label="Menu" aria-expanded="false">
          <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
        </button>
      </div>
    </div>
  </header>"""


def footer(root: str) -> str:
    return f"""
  <footer class="footer">
    <div class="container footer-inner">
      <div class="footer-brand-col">
        <a href="{root}" class="brand">
          {mark(32)}
          <span class="brand-word">Stack</span>
        </a>
        <p class="tag">Track your stack. Supplements, peptides, meds and more — one quiet, private app.</p>
      </div>
      <div>
        <h4>Product</h4>
        <ul>
          <li><a href="{root}#features">Features</a></li>
          <li><a href="{root}pricing/">Pricing</a></li>
          <li><a href="{root}#download">Get the app</a></li>
          <li><a href="{root}account/">Sign in</a></li>
          <li><a href="{root}referral.html">Referral program</a></li>
        </ul>
      </div>
      <div>
        <h4>Learn</h4>
        <ul>
          <li><a href="{root}compounds/">Compound library</a></li>
          <li><a href="{root}guides/">Guides</a></li>
          <li><a href="{root}tools/reconstitution/">Reconstitution calculator</a></li>
          <li><a href="{root}stacks/">Share your stack</a></li>
        </ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="{root}about/">About &amp; sourcing</a></li>
          <li><a href="{root}privacy.html">Privacy</a></li>
          <li><a href="{root}terms.html">Terms</a></li>
          <li><a href="{root}data-deletion.html">Data deletion</a></li>
          <li><a href="#" data-email-link>Contact</a></li>
        </ul>
      </div>
    </div>
    <div class="disclaimer-band">
      Stack is a logging tool and an educational reference. Nothing on this site is medical
      advice, a recommendation, or an endorsement of any compound. Information is summarized
      from public sources and may contain errors — always verify against the original label
      or literature and talk to a clinician about anything you take.
    </div>
    <div class="container footer-bottom">
      <span>© 2026 Stack</span>
      <span><a href="#" data-email-link>hello@trackyourstack.app</a></span>
    </div>
  </footer>
  <script src="{root}assets/js/site.js?v=4"></script>"""


def decay_bars(hours: float | None) -> str:
    if not hours:
        return ""
    bars = "".join(
        f'<i style="--o:{max(0.04, 0.5 ** i):.3f}" title="{int(round(100 * 0.5 ** i))}% after {i} half-li{"fe" if i == 1 else "ves"}"></i>'
        for i in range(0, 6)
    )
    return f"""
        <div class="decay">
          <h2>Relative level by half-life</h2>
          <div class="decay-bar" role="img" aria-label="Relative amount remaining at 0 through 5 half-lives: 100, 50, 25, 12.5, 6 and 3 percent">{bars}</div>
          <div class="decay-cap"><span>dose</span><span>5 half-lives ≈ cleared</span></div>
        </div>"""


def compound_page(c: dict, by_cat: dict[str, list[dict]]) -> str:
    name = c["name"]
    slug = c["slug"]
    cat = c["category"]
    cat_slug, cat_label, _ = CATS[cat]
    assets = "../../assets"
    root = "../../"
    url = f"{BASE_URL}/compounds/{slug}/"

    aka = [a for a in (c.get("aliases") or []) if a.lower() != name.lower()]
    hl = fmt_half_life(c.get("half_life_hours"))
    clr = clearance_note(c.get("half_life_hours"))
    storage = STORAGE.get(c.get("typical_storage") or "", None)
    form = FORM.get(c.get("form") or "", (c.get("form") or "").title())
    units = ", ".join(c.get("common_units") or [])
    strengths = common_strengths(name)
    fda = (c.get("fda_approved_for") or "").strip()
    fda_is_approved = fda and not fda.lower().startswith(("not fda", "not approved", "none"))
    recon = (c.get("reconstitution_note") or "").strip()
    cite = (c.get("source_citation") or "").strip()

    desc = f"{name}: what it is, how it works, half-life, storage and tracking facts. " \
           f"Educational reference from the Stack compound library — not medical advice."

    # Related: same category, up to 4 others.
    related = [r for r in by_cat[cat] if r["slug"] != slug][:4]

    facts_rows = ""
    def row(k: str, v: str) -> str:
        return f"<tr><td>{esc(k)}</td><td>{v}</td></tr>"
    facts_rows += row("Class", f'<a href="../#{cat_slug}">{esc(cat_label)}</a>')
    facts_rows += row("Form", esc(form))
    if hl: facts_rows += row("Half-life", esc(hl))
    if clr: facts_rows += row("≈ Cleared in", esc(clr) + ' <span class="dim">(5 × t½)</span>')
    if storage: facts_rows += row("Storage", esc(storage))
    if units: facts_rows += row("Dose units", esc(units))
    if strengths:
        facts_rows += row("Common strengths", esc(" · ".join(strengths)))
    facts_rows += row("FDA status", ("Approved" if fda_is_approved else "Not FDA-approved"))

    fda_block = ""
    if fda:
        label = "FDA-approved use" if fda_is_approved else "Regulatory status"
        fda_block = f"""
        <h2>{label}</h2>
        <p>{esc(fda)}</p>"""

    recon_block = ""
    if recon:
        recon_block = f"""
        <h2>Reconstitution</h2>
        <p>{esc(recon)}</p>
        <div class="callout"><b>Do the math once, not every pin.</b> The
        <a href="../../tools/reconstitution/">reconstitution calculator</a> converts vial mg +
        bacteriostatic water into exact syringe units for any target dose.</div>"""

    cite_block = ""
    if cite:
        cite_block = f"""
        <h2>Source</h2>
        <p class="dim">{esc(cite)}</p>"""

    related_block = ""
    if related:
        cards = "".join(
            f"""<a class="comp-card" href="../{r['slug']}/">
              <h3>{esc(r['name'])}</h3>
              <div class="meta"><span class="tag">{esc(FORM.get(r.get('form') or '', (r.get('form') or '').title()))}</span></div>
              <p>{esc((r.get('what_it_is') or '')[:110])}…</p>
            </a>"""
            for r in related
        )
        related_block = f"""
      <div class="related">
        <h2>More {esc(cat_label)}</h2>
        <div class="lib-grid">{cards}</div>
      </div>"""

    aka_line = f'<p class="comp-aka">Also known as: {esc(" · ".join(aka))}</p>' if aka else ""

    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": f"{name} — facts, half-life and tracking reference",
            "description": desc,
            "datePublished": REVIEWED,
            "dateModified": REVIEWED,
            "author": {"@type": "Organization", "name": "Stack"},
            "publisher": {"@type": "Organization", "name": "Stack", "url": BASE_URL},
            "mainEntityOfPage": url,
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Stack", "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Compound library", "item": BASE_URL + "/compounds/"},
                {"@type": "ListItem", "position": 3, "name": name, "item": url},
            ],
        },
    ]

    return f"""{head(f"{name} — half-life, facts & tracking reference | Stack", desc, url, assets, jsonld)}
<body>
{nav(root, "compounds")}
  <main>
    <div class="container comp-hero">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="{root}">Home</a> <span>/</span>
        <a href="../">Compounds</a> <span>/</span>
        <a href="../#{cat_slug}">{esc(cat_label)}</a> <span>/</span>
        <span>{esc(name)}</span>
      </nav>
      <span class="eyebrow">{esc(cat_label)} · {esc(form)}</span>
      <h1>{esc(name)}</h1>
      {aka_line}
    </div>

    <div class="container comp-cols">
      <article class="comp-body">
        <h2>What it is</h2>
        <p>{esc(c.get("what_it_is"))}</p>

        <h2>How it works</h2>
        <p>{esc(c.get("mechanism_brief"))}</p>

        <h2>Where it's used</h2>
        <p>{esc(c.get("common_use_context"))}</p>
        {fda_block}
        {recon_block}

        <h2>Tracking it</h2>
        <p>{tracking_paragraph(c, hl)}</p>
        {cite_block}

        <div class="callout">
          <b>Not medical advice.</b> This page is an educational summary compiled from public
          sources for people who log what they take. It is not a recommendation to use
          {esc(name)}, a dosing guide, or a substitute for a clinician.
          <a href="../../about/">How we source →</a>
        </div>
        <p class="updated">Last reviewed {REVIEWED}</p>
        {related_block}
      </article>

      <aside class="facts panel">
        <h2>Key facts</h2>
        <table>{facts_rows}</table>
        {decay_bars(c.get("half_life_hours"))}
        <div class="track-cta">
          <h3>Track {esc(short_name(name))} in Stack</h3>
          <p>Log doses, schedules, reminders and supply{', with injection-site rotation,' if c.get('form') == 'injection' else ''} — free.
          Its "in your system" level curve comes with Plus. Your health data stays encrypted on your device.</p>
          <a class="btn btn-primary" href="{root}#download">Get the app</a>
        </div>
      </aside>
    </div>
  </main>
{footer(root)}
</body>
</html>
"""


def short_name(name: str) -> str:
    return name.split("(")[0].strip()


def tracking_paragraph(c: dict, hl: str | None) -> str:
    """Per-compound tracking guidance derived from the data — varies by
    form/half-life/category so no two pages read the same."""
    name = short_name(c["name"])
    form = c.get("form")
    cat = c["category"]
    bits = []
    if form == "injection":
        bits.append(f"{esc(name)} is injectable, so two things matter in a log: "
                    "<strong>when</strong> you dosed and <strong>where</strong>. "
                    "Rotating sites and writing both down prevents the classic "
                    "“did I already pin the left side?” problem")
    elif form in ("capsule", "tablet", "oral"):
        bits.append(f"{esc(name)} is oral, which makes consistency the whole game — "
                    "a simple daily check-off with a reminder beats memory every time")
    elif form == "nasal":
        bits.append(f"As a nasal spray, {esc(name)} is easy to lose count of — "
                    "logging each administration keeps the daily total honest")
    else:
        bits.append(f"Logging every administration of {esc(name)} builds the record "
                    "that makes patterns visible")
    if hl:
        bits.append(f"with a half-life of {esc(hl.replace('≈ ', 'about '))}, a dose log also lets a tracker "
                    "model the relative amount still in your system between doses")
    if cat == "GLP-1":
        bits.append("for titrated compounds like this one, a log that records the dose "
                    "<em>at each step</em> is the difference between knowing your history and guessing it")
    if c.get("typical_storage") in ("fridge", "fridge_after_recon"):
        bits.append("it's also worth noting opened-vial dates, since this one lives in the fridge")
    # Capitalize each fragment so joined sentences don't read "…problem. with a
    # half-life…". Safe: every fragment starts with a plain letter, not a tag.
    return ". ".join(b[0].upper() + b[1:] for b in bits) + "."


def catalog_page(compounds: list[dict], by_cat: dict[str, list[dict]]) -> str:
    assets = "../assets"
    root = "../"
    url = f"{BASE_URL}/compounds/"
    desc = ("The Stack compound library: plain-English facts, mechanisms, half-lives and "
            "storage for 112 compounds — GLP-1s, peptides, TRT esters, orals and supplements. "
            "Educational reference, not medical advice.")

    chips = '<button class="cat-chip active" data-cat="all">All</button>' + "".join(
        f'<button class="cat-chip" data-cat="{esc(k)}">{esc(CATS[k][1])}</button>'
        for k in CAT_ORDER
    )

    sections = ""
    for k in CAT_ORDER:
        cat_slug, label, blurb = CATS[k]
        cards = ""
        for c in by_cat[k]:
            hl = fmt_half_life(c.get("half_life_hours"))
            meta = f'<span class="tag">{esc(FORM.get(c.get("form") or "", (c.get("form") or "").title()))}</span>'
            if hl:
                meta += f'<span class="tag">t½ {esc(hl.replace("≈ ", ""))}</span>'
            search = " ".join([c["name"]] + (c.get("aliases") or []))
            cards += f"""
          <a class="comp-card" href="{c['slug']}/" data-cat="{esc(k)}" data-search="{esc(search)}">
            <h3>{esc(c['name'])}</h3>
            <div class="meta">{meta}</div>
            <p>{esc((c.get('what_it_is') or '')[:128])}…</p>
          </a>"""
        sections += f"""
      <section class="lib-section" id="{cat_slug}">
        <h2>{esc(label)} <span class="dim">— {esc(blurb)}</span></h2>
        <div class="lib-grid">{cards}
        </div>
      </section>"""

    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": "Stack compound library",
            "description": desc,
            "url": url,
            "isPartOf": {"@type": "WebSite", "name": "Stack", "url": BASE_URL},
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Stack", "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Compound library", "item": url},
            ],
        },
    ]

    return f"""{head("Compound library — facts, half-lives & mechanisms for 112 compounds | Stack", desc, url, assets, jsonld, "website")}
<body>
{nav(root, "compounds")}
  <main>
    <div class="container lib-head">
      <span class="eyebrow">Compound library</span>
      <h1>Know what you take.</h1>
      <p class="lead" style="max-width:56ch;margin-top:20px">Plain-English facts for {len(compounds)} compounds —
      what each one is, how it works, half-life, storage and what matters when you track it.
      Summarized from public sources. <a href="../about/">How we source</a>. Not medical advice.</p>
      <div class="lib-search">
        <input class="input" id="libSearch" type="search" placeholder="Search by name or alias…" aria-label="Search compounds" />
        <span class="lib-count" id="libCount">{len(compounds)} compounds</span>
      </div>
      <div class="cat-row" role="group" aria-label="Filter by category">{chips}</div>
      <p class="muted" style="margin-top:18px;font-size:14px">Comparing two?
      See the <a href="compare/" style="text-decoration:underline;text-underline-offset:3px">head-to-head comparisons</a> —
      semaglutide vs tirzepatide, test cyp vs enanthate and more.</p>
    </div>
    <div class="container">{sections}
    </div>
  </main>
{footer(root)}
</body>
</html>
"""


def build_sitemap(slugs: list[str], extra: list[str] | None = None) -> str:
    """`slugs` are compound slugs (→ /compounds/<slug>/). `extra` are
    site-relative paths already including their full path (e.g.
    'compounds/compare/semaglutide-vs-tirzepatide/')."""
    # NOTE: compounds/compare/ is emitted by build_compare (it leads `extra`),
    # so it is intentionally NOT listed here to avoid a duplicate sitemap entry.
    static = [
        "", "pricing/", "compounds/", "tools/reconstitution/",
        "guides/", "guides/reconstitution-explained/",
        "guides/injection-site-rotation/", "guides/glp1-tracking/",
        "about/", "stacks/", "privacy.html", "terms.html", "referral.html",
        "creators.html", "data-deletion.html",
    ]
    urls = ""
    for p in static:
        urls += f"  <url><loc>{BASE_URL}/{p}</loc><lastmod>{TODAY}</lastmod></url>\n"
    for s in slugs:
        urls += f"  <url><loc>{BASE_URL}/compounds/{s}/</loc><lastmod>{TODAY}</lastmod></url>\n"
    for p in extra or []:
        urls += f"  <url><loc>{BASE_URL}/{p}</loc><lastmod>{TODAY}</lastmod></url>\n"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}</urlset>\n")


def main() -> None:
    with open(os.path.join(ROOT, "assets", "data", "compounds.json"), encoding="utf-8") as f:
        compounds = json.load(f)

    for c in compounds:
        c["slug"] = slugify(c["name"])
    slugs = [c["slug"] for c in compounds]
    assert len(slugs) == len(set(slugs)), "slug collision"

    by_cat: dict[str, list[dict]] = {k: [] for k in CAT_ORDER}
    for c in compounds:
        by_cat.setdefault(c["category"], []).append(c)
    for k in by_cat:
        by_cat[k].sort(key=lambda c: c["name"].lower())

    out_root = os.path.join(ROOT, "compounds")
    os.makedirs(out_root, exist_ok=True)

    with open(os.path.join(out_root, "index.html"), "w", encoding="utf-8") as f:
        f.write(catalog_page(compounds, by_cat))

    for c in compounds:
        d = os.path.join(out_root, c["slug"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(compound_page(c, by_cat))

    # Comparison pages (separate module; returns site-relative paths for sitemap).
    extra: list[str] = []
    try:
        import build_compare
        extra = build_compare.main()
    except Exception as e:  # never let a compare error nuke the whole build
        print(f"  (compare skipped: {e})")

    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(build_sitemap(sorted(slugs), extra))

    print(f"built compounds/index.html + {len(compounds)} pages + sitemap.xml")


if __name__ == "__main__":
    main()
