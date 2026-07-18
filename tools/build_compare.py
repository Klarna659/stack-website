"""Builds head-to-head comparison pages — the highest-intent searches in the
niche ("semaglutide vs tirzepatide" etc.). python tools/build_compare.py

Each page is a real comparison, not a template: a side-by-side facts table
pulled from the dataset PLUS a hand-written "how they differ" section so the
page carries unique substance (thin programmatic comparisons get filtered).
Returns the list of slugs so build_all can fold them into the sitemap.
"""
from __future__ import annotations

import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_library import (  # noqa: E402
    BASE_URL, REVIEWED, CATS, FORM, STORAGE, esc, head, nav, footer,
    fmt_half_life, slugify, short_name,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Curated pairs. `intro` and `diff` are hand-written (the unique value);
# everything else comes from the dataset. `takeaway` is the BLUF answer search
# engines quote. Keep every line factual + neutral — no dosing, no "better".
PAIRS = [
    {
        "a": "Semaglutide", "b": "Tirzepatide",
        "title": "Semaglutide vs Tirzepatide",
        "desc": "Semaglutide vs tirzepatide compared: mechanism, half-life, dosing cadence and what each one is approved for. Educational reference, not medical advice.",
        "takeaway": "Both are once-weekly injectable incretin drugs for type-2 diabetes and weight management. The core difference is receptor coverage: semaglutide is a single GLP-1 receptor agonist, while tirzepatide is a dual GIP/GLP-1 agonist. Their half-lives are similar (about a week), so both titrate over months and both reward a written dose history.",
        "intro": "These are the two most-searched compounds in the whole category, and they're genuinely close cousins — both weekly, both injectable, both titrated slowly upward. The questions people actually have are about how they differ mechanistically and what that means for tracking, not which is 'best' (that's a clinician's call).",
        "diff": [
            ("Receptor targets", "Semaglutide acts on the <b>GLP-1</b> receptor alone. Tirzepatide is a <b>dual agonist</b> — it activates both the <b>GIP</b> and GLP-1 receptors. That added GIP activity is the headline pharmacological distinction between them."),
            ("Titration ladders", "Both climb through defined steps over months. Semaglutide's common ladder is 0.25 → 0.5 → 1 → 1.7 → 2.4 mg; tirzepatide's is 2.5 → 5 → 7.5 → 10 → 12.5 → 15 mg. Because the numbers aren't interchangeable, a log that records the dose <em>at each step</em> is the only reliable history."),
            ("Half-life &amp; cadence", "Both sit around a one-week half-life, so both are once-weekly and both take roughly a month to approach steady levels. A missed week halves the level rather than zeroing it — which is exactly the kind of thing an 'in your system' curve makes visible."),
            ("Brand context", "Each molecule is marketed under multiple brand names for diabetes and for weight management. We never use brand names in the library — the molecule is what matters for tracking, and brands are trademarks."),
        ],
    },
    {
        "a": "Tirzepatide", "b": "Retatrutide",
        "title": "Tirzepatide vs Retatrutide",
        "desc": "Tirzepatide vs retatrutide: dual vs triple incretin agonism, development status, half-life and dosing. Educational reference, not medical advice.",
        "takeaway": "Tirzepatide is an approved dual GIP/GLP-1 agonist. Retatrutide is an investigational triple agonist that adds glucagon-receptor activity on top. The practical headline: one is a marketed drug, the other is still in clinical development.",
        "intro": "This is the 'next-generation' comparison people search when they've heard about triple agonists. The honest framing is that these aren't on the same footing — tirzepatide is approved and widely used, retatrutide is investigational.",
        "diff": [
            ("Receptor coverage", "Tirzepatide hits two receptors (GIP + GLP-1). Retatrutide is a <b>triple agonist</b> — GIP, GLP-1 <em>and</em> glucagon. The glucagon arm is the new ingredient and the reason it's studied separately."),
            ("Approval status", "Tirzepatide is FDA-approved. Retatrutide is <b>investigational</b> — in clinical trials, not approved for any use. The library labels this plainly on each page."),
            ("Cadence", "Both are weekly injectables under study/use with multi-day half-lives, so both fit the weekly-reminder + titration-log pattern."),
            ("Why it matters for tracking", "For anything investigational, the value of a meticulous log goes up, not down — dose, date and any noted effects are the record you'd actually want later."),
        ],
    },
    {
        "a": "Testosterone Cypionate", "b": "Testosterone Enanthate",
        "title": "Testosterone Cypionate vs Enanthate",
        "desc": "Test cypionate vs enanthate: ester length, half-life, injection cadence and how they differ in practice. Educational reference, not medical advice.",
        "takeaway": "Both are long-acting injectable testosterone esters used in TRT, and in practice they're close to interchangeable. The only real difference is the ester: cypionate is marginally longer than enanthate, giving it a slightly longer half-life — small enough that injection schedules usually look identical.",
        "intro": "This is the classic TRT question, and the honest answer is that the two are far more alike than different. Both deliver testosterone; the ester just changes the release curve slightly.",
        "diff": [
            ("The ester", "Cypionate has an 8-carbon ester; enanthate has 7. That single carbon makes cypionate release marginally slower and gives it a slightly longer half-life."),
            ("Half-life in practice", "The difference is small — both are measured in days, and most protocols inject on the same cadence regardless. For tracking purposes they behave the same: log the date, the dose and the site."),
            ("Availability", "Cypionate is the most commonly prescribed injectable testosterone in the US; enanthate is more common elsewhere. Neither distinction affects how you'd log it."),
            ("Site rotation matters more than the ester", "With any oil-based IM or subq testosterone, <a href=\"../../../guides/injection-site-rotation/\">rotating sites</a> and recording where you injected does more for a clean experience than the cypionate-vs-enanthate choice."),
        ],
    },
    {
        "a": "BPC-157", "b": "TB-500",
        "title": "BPC-157 vs TB-500",
        "desc": "BPC-157 vs TB-500: two recovery peptides compared by origin, half-life, storage and how people stack them. Educational reference, not medical advice.",
        "takeaway": "Both are research peptides associated with recovery, and they're frequently discussed together rather than as either/or — they come from different parent molecules (a gastric protein fragment vs a thymosin-beta-4 fragment) and are often run side by side. Neither is FDA-approved for human use.",
        "intro": "People rarely actually pick between these two — the more common question is how they differ and why they're so often paired. There's even a combined entry in the library.",
        "diff": [
            ("Origin", "BPC-157 is a synthetic fragment of a protein found in gastric juice. TB-500 is a synthetic fragment of <b>thymosin beta-4</b>. Different parent molecules, different proposed mechanisms."),
            ("Half-life &amp; dosing rhythm", "Their pharmacokinetics differ, which is why people who run both often log them on separate schedules. A per-compound dose log keeps two overlapping cadences straight."),
            ("Reconstitution &amp; storage", "Both ship lyophilized and are reconstituted with bacteriostatic water, and both are typically refrigerated after mixing — so the <a href=\"../../../tools/reconstitution/\">reconstitution calculator</a> and an opened-vial date apply to each."),
            ("Regulatory status", "Neither is approved for human use anywhere. Their inclusion in the library is documentation, not endorsement."),
        ],
    },
    {
        "a": "CJC-1295 (no DAC)", "b": "Ipamorelin",
        "title": "CJC-1295 vs Ipamorelin",
        "desc": "CJC-1295 vs ipamorelin: GHRH analog vs ghrelin-mimetic, why they're stacked, half-life and reconstitution. Educational reference, not medical advice.",
        "takeaway": "These work on two different levers of the same axis, which is why they're classically combined rather than compared. CJC-1295 is a GHRH analog; ipamorelin is a selective growth-hormone secretagogue (a ghrelin-receptor agonist). Neither is FDA-approved.",
        "intro": "The search is 'vs' but the real-world relationship is 'and' — these two are the textbook peptide pairing, each pushing a different button.",
        "diff": [
            ("Mechanism", "CJC-1295 mimics <b>GHRH</b>. Ipamorelin mimics <b>ghrelin</b> and is prized for being selective (it raises GH with comparatively little effect on other hormones). Two different signals, often used together."),
            ("Why they're stacked", "Because they act on separate receptors, they're frequently logged as a pair on the same schedule. Stack groups them under one protocol you can pause together."),
            ("DAC vs no-DAC", "CJC-1295 comes with and without DAC (drug affinity complex), which dramatically changes its half-life and dosing cadence — see the separate library entries. Ipamorelin is short-acting."),
            ("Handling", "Both are reconstituted peptides, typically refrigerated. The same <a href=\"../../../tools/reconstitution/\">vial math</a> and opened-date tracking apply to each."),
        ],
    },
    {
        "a": "MK-677", "b": "Ipamorelin",
        "title": "MK-677 vs Ipamorelin",
        "desc": "MK-677 vs ipamorelin: oral daily secretagogue vs injectable peptide, half-life and cadence. Educational reference, not medical advice.",
        "takeaway": "Both are growth-hormone secretagogues, but the practical split is route and duration: MK-677 (ibutamoren) is an oral, long-acting daily compound; ipamorelin is a short-acting injectable peptide. That difference drives how you'd schedule and log each.",
        "intro": "This one is a genuine fork, because the two are taken completely differently — a daily pill versus an injection — even though they nudge the same hormone.",
        "diff": [
            ("Route", "MK-677 is <b>oral</b> — no needles, no reconstitution. Ipamorelin is <b>injectable</b> and has to be mixed from powder. That alone changes the logging workflow."),
            ("Duration &amp; cadence", "MK-677's long half-life supports once-daily dosing; ipamorelin is short-acting. A daily oral and a short-acting injectable produce very different 'in your system' curves."),
            ("Tracking implications", "For MK-677, consistency is the whole game — a daily check-off with a reminder. For ipamorelin, site and timing matter. Same app, different logging emphasis."),
            ("Status", "Both are research compounds, not approved for human use. Labeled as such in the library."),
        ],
    },
    {
        "a": "Magnesium Glycinate", "b": "Magnesium L-Threonate",
        "title": "Magnesium Glycinate vs L-Threonate",
        "desc": "Magnesium glycinate vs L-threonate: two chelated forms compared by what they're typically used for. Educational reference, not medical advice.",
        "takeaway": "Both are well-absorbed chelated magnesium forms, and the usual distinction people draw is the use context: glycinate is commonly taken for general supplementation and sleep, while L-threonate is the form discussed specifically for cognitive contexts because of how it's studied crossing into the brain.",
        "intro": "A friendlier, fully-legal comparison — two supplement forms of the same mineral. The question is which form, and the answer is mostly about context of use.",
        "diff": [
            ("The chelate", "Glycinate binds magnesium to glycine; L-threonate binds it to threonic acid. Both improve tolerability over cheap oxide forms; the carrier is the difference."),
            ("Typical context", "Glycinate shows up in general and sleep-oriented routines. L-threonate is the form specifically researched for cognitive endpoints. Neither claim is medical advice — just how each is commonly discussed."),
            ("Stacking note", "Some people log both for different times of day. A tracker keeps the AM/PM split honest."),
            ("Everyday staple", "Both are everyday supplements — the point of logging them is consistency and seeing the routine actually stick, which is what streaks are for."),
        ],
    },
    {
        "a": "Enclomiphene", "b": "Clomiphene",
        "title": "Enclomiphene vs Clomiphene",
        "desc": "Enclomiphene vs clomiphene (Clomid): isomer difference, why enclomiphene is the isolated form, and context of use. Educational reference, not medical advice.",
        "takeaway": "Clomiphene is a mix of two isomers; enclomiphene is one of them, isolated. That's the entire relationship — enclomiphene is the purified trans-isomer of clomiphene, separated out because the two isomers behave differently.",
        "intro": "A precise, factual comparison: same molecule family, one is a subset of the other. Worth getting right because the names get used interchangeably when they shouldn't be.",
        "diff": [
            ("Isomers", "Clomiphene is a <b>mixture</b> of enclomiphene (trans) and zuclomiphene (cis). <b>Enclomiphene is just the trans-isomer on its own.</b> Isolating it is the whole point of the distinction."),
            ("Why isolate it", "The two isomers have different durations and properties, which is why enclomiphene is discussed as a more 'targeted' option than the combined molecule. Specifics are clinician territory."),
            ("Tracking", "Both are oral compounds where daily consistency is what a log captures. Route and cadence are identical for logging purposes."),
            ("Status", "Check each library entry for its current regulatory status, which the pages state plainly."),
        ],
    },
    {
        "a": "Anastrozole", "b": "Exemestane",
        "title": "Anastrozole vs Exemestane",
        "desc": "Anastrozole vs exemestane: two aromatase inhibitors compared by type (reversible vs irreversible) and class. Educational reference, not medical advice.",
        "takeaway": "Both are aromatase inhibitors, and the textbook distinction is reversible vs irreversible: anastrozole is a non-steroidal, reversible AI, while exemestane is a steroidal, irreversible ('suicide') inhibitor. They're different chemical classes that reach a similar end.",
        "intro": "A clean factual split between two ancillaries that get compared constantly. The mechanism difference is real and easy to state without giving any dosing guidance.",
        "diff": [
            ("Class", "Anastrozole is <b>non-steroidal</b> and binds the aromatase enzyme <b>reversibly</b>. Exemestane is <b>steroidal</b> and binds <b>irreversibly</b> — the enzyme has to be remade. Same target, different chemistry."),
            ("Practical implication", "The reversible-vs-irreversible difference is the main thing people mean when they compare these. How that maps to any individual's use is strictly a clinician's call."),
            ("Tracking", "Both are orals taken on a schedule alongside other compounds; both fit cleanly into a protocol group you can pause as a unit."),
            ("Status", "See each entry for FDA status — stated plainly on every library page."),
        ],
    },
    {
        "a": "Sermorelin", "b": "Tesamorelin",
        "title": "Sermorelin vs Tesamorelin",
        "desc": "Sermorelin vs tesamorelin: two GHRH analogs compared by stability, approval status and use context. Educational reference, not medical advice.",
        "takeaway": "Both are GHRH analogs (growth-hormone-releasing peptides), and the main differences are stability and regulatory status: tesamorelin is a stabilized analog with an FDA-approved indication, while sermorelin is the older, shorter-acting GHRH fragment.",
        "intro": "Two peptides on the same pathway, separated mostly by how modern and how regulated each is. A useful factual comparison for anyone logging GH-axis compounds.",
        "diff": [
            ("Molecule", "Sermorelin is a fragment of GHRH (the first 29 amino acids). Tesamorelin is a <b>stabilized</b> GHRH analog engineered for a longer functional life."),
            ("Approval", "Tesamorelin has a specific FDA-approved indication; sermorelin's regulatory history is different. Each page states its status — read them rather than assuming."),
            ("Cadence", "Both are injectable peptides reconstituted from powder, so the <a href=\"../../../tools/reconstitution/\">calculator</a>, refrigeration and opened-vial dates apply to each."),
            ("Tracking", "GH-axis peptides reward careful timing logs; record the dose, time and site each administration."),
        ],
    },
]


def find(compounds_by_name, name):
    c = compounds_by_name.get(name.lower())
    if not c:
        raise SystemExit(f"compare: '{name}' not in dataset")
    return c


def facts_table(a, b):
    def cell(c, key):
        if key == "class":
            return esc(CATS[c["category"]][1])
        if key == "form":
            return esc(FORM.get(c.get("form") or "", (c.get("form") or "").title()))
        if key == "half":
            return esc(fmt_half_life(c.get("half_life_hours")) or "—")
        if key == "storage":
            return esc(STORAGE.get(c.get("typical_storage") or "", "—"))
        if key == "fda":
            fda = (c.get("fda_approved_for") or "").strip()
            ok = fda and not fda.lower().startswith(("not fda", "not approved", "none"))
            return "Approved" if ok else "Not FDA-approved"
        if key == "units":
            return esc(", ".join(c.get("common_units") or [])) or "—"
        return "—"

    rows = [
        ("Class", "class"), ("Form", "form"), ("Half-life", "half"),
        ("Storage", "storage"), ("Dose units", "units"), ("FDA status", "fda"),
    ]
    body = ""
    for label, key in rows:
        body += f"<tr><td>{esc(label)}</td><td>{cell(a, key)}</td><td>{cell(b, key)}</td></tr>"
    return body


def compare_page(pair, compounds_by_name):
    a = find(compounds_by_name, pair["a"])
    b = find(compounds_by_name, pair["b"])
    a_slug, b_slug = slugify(a["name"]), slugify(b["name"])
    slug = pair.get("slug") or f"{slugify(short_name(a['name']))}-vs-{slugify(short_name(b['name']))}"
    url = f"{BASE_URL}/compounds/compare/{slug}/"
    assets = "../../../assets"
    root = "../../../"
    title = f"{pair['title']} — compared | Stack"

    diff_html = ""
    for h, body in pair["diff"]:
        diff_html += f"""
        <h3>{h}</h3>
        <p>{body}</p>"""

    jsonld = [
        {
            "@context": "https://schema.org", "@type": "Article",
            "headline": pair["title"], "description": pair["desc"],
            "datePublished": REVIEWED, "dateModified": REVIEWED,
            "author": {"@type": "Organization", "name": "Stack"},
            "publisher": {"@type": "Organization", "name": "Stack", "url": BASE_URL},
            "mainEntityOfPage": url,
        },
        {
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Stack", "item": BASE_URL + "/"},
                {"@type": "ListItem", "position": 2, "name": "Compounds", "item": BASE_URL + "/compounds/"},
                {"@type": "ListItem", "position": 3, "name": pair["title"], "item": url},
            ],
        },
    ]

    return slug, f"""{head(title, pair["desc"], url, assets, jsonld)}
<body>
{nav(root, "compounds")}
  <main>
    <div class="container comp-hero">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="{root}">Home</a> <span>/</span>
        <a href="{root}compounds/">Compounds</a> <span>/</span>
        <span>{esc(pair["title"])}</span>
      </nav>
      <span class="eyebrow">Head to head</span>
      <h1>{esc(pair["title"])}</h1>
      <p class="lead" style="max-width:60ch;margin-top:18px">{esc(pair["intro"])}</p>
    </div>

    <div class="prose-w prose" style="padding-top:8px">
      <div class="callout"><b>The short answer.</b> {pair["takeaway"]}</div>

      <h2>Side by side</h2>
      <table>
        <tr><th>&nbsp;</th><th>{esc(short_name(a["name"]))}</th><th>{esc(short_name(b["name"]))}</th></tr>
        {facts_table(a, b)}
      </table>
      <p class="dim" style="font-size:13px">Facts from the Stack compound library. See the full pages:
      <a href="{root}compounds/{a_slug}/">{esc(a["name"])}</a> ·
      <a href="{root}compounds/{b_slug}/">{esc(b["name"])}</a>.</p>

      <h2>How they differ</h2>{diff_html}

      <h2>Tracking either one</h2>
      <p>Whichever you log, the workflow is the same in Stack: add it once, set the schedule,
      and let the app handle reminders, supply projection and an "in your system" curve from
      the half-life. Run both? Group them into one protocol you can pause together.</p>

      <div class="track-cta" style="margin-top:22px">
        <h3>Track your stack in Stack</h3>
        <p>Free to track — doses, schedules, supply and reminders in one quiet app. Your health data stays encrypted on your device.</p>
        <a class="btn btn-primary" href="{root}#download">Get the app</a>
      </div>

      <div class="callout" style="margin-top:24px"><b>Not medical advice.</b> This page compares
      publicly-documented properties of two compounds for educational purposes. It does not
      recommend either one, or any dose. <a href="{root}about/">How we source →</a></div>
      <p class="updated">Last reviewed {REVIEWED}</p>
    </div>
  </main>
{footer(root)}
</body>
</html>
"""


def hub_page(pairs_with_slugs):
    url = f"{BASE_URL}/compounds/compare/"
    assets = "../../assets"
    root = "../../"
    desc = "Head-to-head compound comparisons — semaglutide vs tirzepatide, test cypionate vs enanthate, BPC-157 vs TB-500 and more. Facts side by side, plus how they differ."
    cards = ""
    for pair, slug in pairs_with_slugs:
        cards += f"""
        <a class="comp-card" href="{slug}/">
          <h3>{esc(pair['title'])}</h3>
          <p>{esc(pair['takeaway'][:120])}…</p>
        </a>"""
    jsonld = [{
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "Compound comparisons", "description": desc, "url": url,
    }]
    return f"""{head("Compound comparisons — head to head | Stack", desc, url, assets, jsonld, "website")}
<body>
{nav(root, "compounds")}
  <main>
    <div class="container lib-head">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="{root}">Home</a> <span>/</span>
        <a href="{root}compounds/">Compounds</a> <span>/</span> <span>Comparisons</span>
      </nav>
      <span class="eyebrow">Head to head</span>
      <h1>Compound comparisons</h1>
      <p class="lead" style="max-width:54ch;margin-top:18px">The questions people actually search —
      answered with the facts side by side and a plain explanation of how each pair differs.
      Educational only, never a recommendation.</p>
    </div>
    <div class="container" style="padding-bottom:80px">
      <div class="lib-grid">{cards}
      </div>
    </div>
  </main>
{footer(root)}
</body>
</html>
"""


def main():
    with open(os.path.join(ROOT, "assets", "data", "compounds.json"), encoding="utf-8") as f:
        compounds = json.load(f)
    by_name = {c["name"].lower(): c for c in compounds}

    out = os.path.join(ROOT, "compounds", "compare")
    os.makedirs(out, exist_ok=True)

    pairs_with_slugs = []
    for pair in PAIRS:
        slug, html_doc = compare_page(pair, by_name)
        d = os.path.join(out, slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_doc)
        pairs_with_slugs.append((pair, slug))

    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(hub_page(pairs_with_slugs))

    slugs = ["compounds/compare/"] + [f"compounds/compare/{s}/" for _, s in pairs_with_slugs]
    print(f"built compare hub + {len(pairs_with_slugs)} comparison pages")
    return slugs


if __name__ == "__main__":
    main()
