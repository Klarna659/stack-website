"""Builds the prose pages (guides hub, 3 guides, about, 404) with the same
chrome as the library generator. python tools/build_pages.py"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_library import BASE_URL, REVIEWED, head, nav, footer  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def page(path: str, title: str, desc: str, body: str, depth: int, current: str = "guides",
         og_type: str = "article", extra_jsonld: list | None = None) -> None:
    rel = "../" * depth
    assets = rel.rstrip("/") + "/assets" if depth else "assets"
    url = f"{BASE_URL}/{path}" if path else BASE_URL + "/"
    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "Article" if og_type == "article" else "WebPage",
            "headline": title.split("|")[0].strip(),
            "description": desc,
            "datePublished": REVIEWED,
            "dateModified": REVIEWED,
            "author": {"@type": "Organization", "name": "Stack"},
            "publisher": {"@type": "Organization", "name": "Stack", "url": BASE_URL},
            "mainEntityOfPage": url,
        },
    ] + (extra_jsonld or [])
    doc = f"""{head(title, desc, url, assets, jsonld, og_type)}
<body>
{nav(rel if depth else "./", current)}
  <main>
{body}
  </main>
{footer(rel if depth else "./")}
</body>
</html>
"""
    out = os.path.join(ROOT, path.replace("/", os.sep))
    if path.endswith("/") or path == "":
        os.makedirs(os.path.join(ROOT, path.replace("/", os.sep)), exist_ok=True)
        out = os.path.join(ROOT, path.replace("/", os.sep), "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    print("wrote", os.path.relpath(out, ROOT))


# ============================================================== guides hub ==
GUIDES = [
    ("reconstitution-explained", "Reconstitution, explained",
     "The vial math from first principles — concentration, dose volume, syringe units, worked examples and the classic mistakes."),
    ("injection-site-rotation", "Injection site rotation",
     "Why rotating sites matters, the common subcutaneous and intramuscular sites, and how to keep an honest rotation log."),
    ("glp1-tracking", "Tracking a GLP-1 protocol",
     "Titration steps, long half-lives and why a written dose history beats memory for semaglutide and tirzepatide."),
]

hub_cards = "".join(
    f"""
        <a class="comp-card" href="{slug}/">
          <h3>{t}</h3>
          <p>{d}</p>
        </a>"""
    for slug, t, d in GUIDES
)
page(
    "guides/",
    "Guides — tracking, reconstitution & rotation | Stack",
    "Practical guides for people who track what they take: reconstitution math, injection-site rotation and GLP-1 protocol logging. Educational, not medical advice.",
    f"""
    <div class="container lib-head">
      <span class="eyebrow">Guides</span>
      <h1>Practical, no-hype guides.</h1>
      <p class="lead" style="max-width:54ch;margin-top:20px">The mechanics of tracking done well —
      written for people who run real protocols. Educational only; nothing here is medical advice.</p>
    </div>
    <div class="container" style="padding-bottom:80px">
      <div class="lib-grid">{hub_cards}
      </div>
      <div class="callout" style="margin-top:26px">Looking for a specific compound instead?
      The <a href="../compounds/">compound library</a> covers 112 of them — half-lives, mechanisms and storage.</div>
    </div>""",
    1, "guides", "website",
)

# ===================================================== guide: reconstitution ==
page(
    "guides/reconstitution-explained/",
    "Reconstitution, explained — vial math from first principles | Stack",
    "How peptide reconstitution actually works: concentration, dose volume and syringe units, with worked examples and the mistakes that ruin vials.",
    f"""
    <div class="prose-w prose">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="../../">Home</a> <span>/</span> <a href="../">Guides</a> <span>/</span> <span>Reconstitution</span>
      </nav>
      <span class="eyebrow">Guide</span>
      <h1>Reconstitution, explained</h1>
      <p class="updated">Last reviewed {REVIEWED} · 6 min read</p>

      <p><strong>Bottom line:</strong> reconstitution is three divisions.
      Concentration = peptide ÷ water. Dose volume = dose ÷ concentration.
      Syringe units = volume × 100. Everything else is unit conversion —
      and the <a href="../../tools/reconstitution/">calculator</a> does all of it.</p>

      <h2>What reconstitution is</h2>
      <p>Most research peptides ship as a lyophilized (freeze-dried) powder in a small vial.
      Before it can be drawn into a syringe, the powder is dissolved in a measured amount of
      bacteriostatic water. That measured amount is the single most important number you'll
      write down: it sets the concentration, and the concentration decides what every mark on
      your syringe means.</p>

      <h2>The three numbers</h2>
      <table>
        <tr><th>Number</th><th>Formula</th><th>Example (5 mg vial + 2 mL water)</th></tr>
        <tr><td>Concentration</td><td>peptide ÷ water</td><td>5 mg ÷ 2 mL = 2.5 mg/mL</td></tr>
        <tr><td>Dose volume</td><td>dose ÷ concentration</td><td>250 mcg ÷ 2,500 mcg/mL = 0.1 mL</td></tr>
        <tr><td>Syringe units</td><td>volume × 100</td><td>0.1 mL = 10 units (U-100)</td></tr>
      </table>
      <p>The "× 100" works because a U-100 insulin syringe is defined as 100 units per mL —
      that's what U-100 means. A 0.5 mL syringe holds 50 units; a 0.3 mL holds 30. The units
      are a volume scale, nothing more.</p>

      <h2>Worked example, end to end</h2>
      <p>Say a vial holds 10 mg of a peptide, and the target dose is 500 mcg.</p>
      <ul>
        <li><strong>Add 3 mL</strong> of bacteriostatic water → concentration is 10 ÷ 3 ≈ 3.33 mg/mL
        (3,333 mcg/mL).</li>
        <li><strong>Dose volume</strong>: 500 ÷ 3,333 ≈ 0.15 mL.</li>
        <li><strong>Draw to 15 units</strong> on a U-100 syringe. The vial holds 10,000 ÷ 500 = 20 doses.</li>
      </ul>

      <h2>Choosing how much water</h2>
      <p>More water = more dilute = more units per dose, which is <em>easier to measure
      accurately</em>. Less water = concentrated = small draws, which fit small syringes but
      amplify any measuring error. Two rules of thumb keep you out of trouble:</p>
      <ul>
        <li>Pick a volume that puts your usual dose <strong>between roughly 5 and 30 units</strong> —
        big enough to measure, small enough to leave headroom.</li>
        <li>Pick a round number that makes the mental math clean (1, 2 or 3 mL beats 1.7 mL).</li>
      </ul>

      <h2>The classic mistakes</h2>
      <ul>
        <li><strong>Forgetting the water amount.</strong> Without it, the vial is a mystery solution.
        Write it on the vial or log it the moment you reconstitute.</li>
        <li><strong>mg/mcg confusion.</strong> 1 mg = 1,000 mcg. Most dosing errors are a
        thousand-fold unit slip — sanity-check that your dose volume is a fraction of a mL,
        not multiple mL.</li>
        <li><strong>Assuming all syringes are U-100.</strong> They almost always are, but check the
        barrel — the math above is U-100 math.</li>
        <li><strong>Spraying water directly onto the powder.</strong> Run it down the glass wall
        slowly and swirl gently; peptides are fragile molecules and foaming degrades some of them.</li>
        <li><strong>Skipping the fridge.</strong> Most reconstituted peptides are stored cold —
        check the <a href="../../compounds/">compound library</a> entry for storage notes.</li>
      </ul>

      <h2>Track it once, reuse it every pin</h2>
      <p>This math only needs doing once per vial — if it's logged. Stack stores the vial size and
      water volume when you add a vial, shows the unit draw for your scheduled dose, counts doses
      remaining and projects the refill date. <a href="../../#download">Get the app →</a></p>

      <div class="callout"><b>Not medical advice.</b> This guide explains arithmetic and handling
      conventions. It does not recommend any compound or dose.</div>
    </div>""",
    2,
)

# ======================================================= guide: site rotation ==
page(
    "guides/injection-site-rotation/",
    "Injection site rotation — why it matters and how to log it | Stack",
    "Why rotating injection sites matters, the common subcutaneous and intramuscular sites, and how a rotation log prevents lumps, soreness and double-ups.",
    f"""
    <div class="prose-w prose">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="../../">Home</a> <span>/</span> <a href="../">Guides</a> <span>/</span> <span>Site rotation</span>
      </nav>
      <span class="eyebrow">Guide</span>
      <h1>Injection site rotation</h1>
      <p class="updated">Last reviewed {REVIEWED} · 5 min read</p>

      <p><strong>Bottom line:</strong> injecting the same spot over and over irritates the tissue
      under it. Rotating across a handful of sites — and writing down which one you used — keeps
      skin and muscle healthy and absorption consistent.</p>

      <h2>Why rotation matters</h2>
      <p>Repeated injections into one spot can cause lipohypertrophy — a rubbery thickening of the
      fat layer that's been documented for decades in insulin users. Beyond the lump itself,
      scarred or thickened tissue absorbs drugs erratically, which quietly changes what a "stable"
      dose actually delivers. Rotation is the boring fix: give each site time to recover before
      it's used again.</p>

      <h2>Common subcutaneous sites</h2>
      <p>Subcutaneous (subq) injections go into the fat layer. The usual map:</p>
      <ul>
        <li><strong>Abdomen</strong> — at least two finger-widths from the navel, left and right.
        The most common choice for GLP-1s and many peptides.</li>
        <li><strong>Thighs</strong> — front-outer middle third, left and right.</li>
        <li><strong>Back of the upper arms</strong> — the fatty area, left and right.</li>
        <li><strong>Upper buttock / flank ("love handle")</strong> — left and right.</li>
      </ul>
      <p>That's already an 8-spot rotation — with one injection a day you return to a site about
      once a week, which is plenty of recovery time.</p>

      <h2>Common intramuscular sites</h2>
      <p>Intramuscular (IM) injections — typical for testosterone esters — go deeper:</p>
      <ul>
        <li><strong>Ventrogluteal</strong> (side of the hip) — large muscle, away from major nerves;
        widely taught as the preferred glute site.</li>
        <li><strong>Vastus lateralis</strong> (outer thigh) — easy to self-inject, left and right.</li>
        <li><strong>Deltoid</strong> — fine for small volumes (commonly ≤ 1 mL).</li>
        <li><strong>Dorsogluteal</strong> (upper-outer buttock) — traditional, but requires care to
        stay in the safe quadrant.</li>
      </ul>

      <h2>What a rotation log looks like</h2>
      <p>A useful log answers two questions instantly: <em>where did the last shot go,</em> and
      <em>which site has rested longest?</em> On paper that's a column next to your dose log.
      In Stack it's a body map: every dose records its site, and the app recommends the
      least-recently-used one next — so "did I already pin the left side this week?" stops being
      a memory game. <a href="../../#download">Get the app →</a></p>

      <h2>Soreness notes are data</h2>
      <p>If a site is unusually sore, red or warm afterwards, write that down too. A pattern at one
      site (but not others) is exactly the kind of signal a log surfaces and memory loses — and
      it's worth showing a clinician.</p>

      <div class="callout"><b>Not medical advice.</b> This guide summarizes commonly taught
      injection-site conventions for educational purposes. Technique, needle choice and whether an
      injection is appropriate at all are questions for your clinician.</div>
    </div>""",
    2,
)

# ========================================================= guide: GLP-1 log ==
page(
    "guides/glp1-tracking/",
    "Tracking a GLP-1 protocol — titration, half-lives & honest logs | Stack",
    "Why GLP-1 protocols (semaglutide, tirzepatide) deserve a real dose log: titration steps, week-long half-lives, missed-dose context and trend lines that mean something.",
    f"""
    <div class="prose-w prose">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="../../">Home</a> <span>/</span> <a href="../">Guides</a> <span>/</span> <span>GLP-1 tracking</span>
      </nav>
      <span class="eyebrow">Guide</span>
      <h1>Tracking a GLP-1 protocol</h1>
      <p class="updated">Last reviewed {REVIEWED} · 5 min read</p>

      <p><strong>Bottom line:</strong> GLP-1s are weekly, titrated and long-lived in the body.
      All three properties make memory a bad logbook — and make a written dose history
      unusually valuable.</p>

      <h2>Titration means your dose has a history</h2>
      <p>Semaglutide and tirzepatide protocols typically climb through defined steps
      (for example 0.25 → 0.5 → 1 → 1.7 → 2.4 mg for semaglutide, or 2.5 → 5 → 7.5 → 10 →
      12.5 → 15 mg for tirzepatide) with several weeks at each step. Six months in, "what was I
      taking in week 9?" is a real question — for you, your clinician, and for making sense of
      your own weight curve. A log that records the dose <em>at each injection</em> answers it
      in one glance.</p>

      <h2>A week is a long time to remember</h2>
      <p>Daily habits are self-reinforcing; weekly ones aren't. The single most common GLP-1
      logging failure is the honest blank: <em>"did I inject last Tuesday or the Tuesday
      before?"</em> A reminder on the right weekday plus a one-tap "taken" mark closes that gap
      permanently — and the streak it builds is its own motivation.</p>

      <h2>Half-life context</h2>
      <p>Semaglutide's half-life is about a week, tirzepatide's around five days. Practical
      consequences worth understanding (both are visible on a half-life chart):</p>
      <ul>
        <li>Levels build for roughly 4–5 half-lives before flattening — early weeks aren't
        steady-state.</li>
        <li>A missed week doesn't drop you to zero; levels roughly halve. The official labels have
        specific guidance for late or missed doses — that's clinician/label territory, not
        guesswork territory.</li>
        <li>Side-effect timing often tracks the level curve, which is why noting <em>when</em>
        nausea or appetite changes happen (not just <em>that</em> they happen) is informative.</li>
      </ul>
      <p>Stack draws this curve for you: an "in your system" model from each compound's published
      half-life, anchored to your actual logged doses. See the
      <a href="../../compounds/semaglutide/">semaglutide</a> and
      <a href="../../compounds/tirzepatide/">tirzepatide</a> library pages for the numbers.</p>

      <h2>What's worth logging alongside</h2>
      <ul>
        <li><strong>Weight</strong> — same scale, same time of day; the weekly EMA trend beats any
        single weigh-in.</li>
        <li><strong>Injection site</strong> — abdomen/thigh/arm rotation, see the
        <a href="../injection-site-rotation/">rotation guide</a>.</li>
        <li><strong>Side effects</strong> — a one-tap note ("nausea, mild, day 2 post-dose")
        becomes a pattern after a month.</li>
        <li><strong>Supply</strong> — pens and vials run out on schedule; a projection beats a
        pharmacy surprise.</li>
      </ul>

      <h2>One place, not five apps</h2>
      <p>The point of tracking isn't the data, it's the correlations: dose step ↔ weight trend ↔
      side effects ↔ adherence. They only line up when they live in the same log. That's the whole
      design thesis of Stack. <a href="../../#download">Get the app →</a></p>

      <div class="callout"><b>Not medical advice.</b> This guide is about logging practices.
      Dose changes, missed-dose handling and whether a GLP-1 is right for you are decisions for
      you and your clinician, guided by the official label.</div>
    </div>""",
    2,
)

# =================================================================== about ==
page(
    "about/",
    "About Stack & how we source — editorial standard | Stack",
    "What Stack is, who builds it, and the sourcing standard behind the compound library: public primary sources, plain English, no hype, no medical advice.",
    f"""
    <div class="prose-w prose">
      <nav class="crumbs" aria-label="Breadcrumb">
        <a href="../">Home</a> <span>/</span> <span>About</span>
      </nav>
      <span class="eyebrow">About</span>
      <h1>About Stack</h1>

      <p><strong>Stack is a private tracking app</strong> for people who take more than one thing —
      supplements, medications, peptides, GLP-1s, TRT — and want one honest log of all of it.
      No account, no ads, no cloud requirement; data stays encrypted on your device.</p>

      <h2>Why we publish a compound library</h2>
      <p>People who track are people who look things up. The
      <a href="../compounds/">library</a> exists so a person logging a compound can read, in plain
      English, what it is, how it works, how long it lasts and how it's stored — without wading
      through hype or sales pages. It is a <em>reference for trackers</em>, not a catalog of
      recommendations.</p>

      <h2>The sourcing standard</h2>
      <ul>
        <li><strong>Public, primary-leaning sources.</strong> Entries are summarized from public
        literature and regulatory materials (FDA labels for approved drugs, published
        pharmacology for the rest), and each entry carries its source line.</li>
        <li><strong>FDA status stated plainly.</strong> Approved uses are quoted as approved;
        everything else is labeled not FDA-approved. We never blur that line.</li>
        <li><strong>No dosing advice, ever.</strong> Where common marketed strengths exist as
        public facts, we list them as facts. We do not suggest doses, cycles or protocols.</li>
        <li><strong>No sourcing, no sales.</strong> We never link to vendors or imply where to buy
        anything.</li>
        <li><strong>Dated and revisable.</strong> Every page shows its last-reviewed date.
        Spot an error? <a href="#" data-email-link>Email us</a> — corrections ship fast.</li>
      </ul>

      <h2>Who builds it</h2>
      <p>Stack is built by a small independent team that tracks its own stacks. We're not
      clinicians and don't pretend to be — that's exactly why the app and this site never give
      medical advice, and why every health decision belongs with you and your clinician.</p>

      <h2>The blunt disclaimer</h2>
      <p>Nothing on this site or in the app is medical advice, a diagnosis, a treatment
      recommendation, or an endorsement of any compound. Information may contain errors and can
      go stale; verify against the original label or literature. Some compounds in the library
      are not approved for human use anywhere — their inclusion is documentation, not approval.</p>

      <p class="updated">Last reviewed {REVIEWED}</p>
    </div>""",
    1, "",
)

# ===================================================================== 404 ==
with open(os.path.join(ROOT, "404.html"), "w", encoding="utf-8") as f:
    f.write(f"""{head("Page not found | Stack", "That page doesn't exist. Head back to Stack.", BASE_URL + "/404.html", "assets", None, "website")}
<body>
{nav('./')}
  <main>
    <div class="container center" style="padding:120px 22px 140px">
      <span class="eyebrow">404</span>
      <h1 class="display" style="font-size:clamp(40px,7vw,80px)">Nothing here.</h1>
      <p class="lead" style="max-width:40ch;margin:22px auto 34px">That page doesn't exist — but the
      compound library and the app very much do.</p>
      <a class="btn btn-primary btn-lg" href="./">Back to Stack</a>
      <a class="btn btn-lg" href="compounds/" style="margin-left:8px">Compound library</a>
    </div>
  </main>
{footer('./')}
</body>
</html>
""")
print("wrote 404.html")
