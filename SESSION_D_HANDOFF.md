# Session D — the website. Handoff for review.

**Date:** 2026-09-01 → 02 · **Repo:** `C:\src\stack-website` · **Branch:** `master`
**Commits:** `42e05c6`, `cc8fd8f`, `490ec17`, `a981ab7`, `088c564`, `0415516`
**Nothing has been pushed. `index.html` — the live homepage — is untouched.**

This document exists so a fresh session can review the work without replaying the
conversation. It states what the section is, what changed, why, what is verified
and how to re-verify it, and where I think the weak points are.

---

## 1. What this section is

`trackyourstack.app` is a static site on GitHub Pages behind Cloudflare. It is
the front door for **Stack**, an Android app (iOS later) that logs everything a
person takes on a schedule — supplements, vitamins, prescriptions, peptides,
GLP-1s, TRT — plus supply projection, injection-site rotation, modelled
in-system levels, weight and bloodwork.

The site is roughly 130 pages:

| Surface | What it is | Touched this session |
|---|---|---|
| `index.html` | the live homepage | **no** |
| `index-v2.html` | **the replacement candidate — the deliverable** | yes, new |
| `compounds/` | 112 cited compound pages + 11 comparison pages | no |
| `guides/`, `about/`, `stacks/`, `referral.html`, `creators.html` | content | no |
| `pricing/`, `account/` | commerce + magic-link sign-in | no |
| `privacy.html`, `terms.html`, `data-deletion.html` | legal | no (see §6) |
| `tools/reconstitution/` | a working in-browser calculator | no |
| `assets/js/site.js` | shared behaviour, every page | **yes — bug fix, affects live** |
| `assets/js/social-proof.js` | new | yes, new |
| `assets/css/mono.css` | shared stylesheet, every page | no |

**The landing page is deliberately not styled from `mono.css`.** It carries its
own inline stylesheet built from the app's design tokens. That is a real
divergence and §6 covers it.

---

## 2. What the landing page does

Six sections, 4,958 px tall at a 390 px viewport (the live page is 13,589 px).

1. **Hero** — a full-bleed generated photograph with the app's three-layer
   treatment: photograph → tinted band → scrim. Headline, store button, email
   capture, and a line of honest proof. `86svh` tall.
2. **Screens** — five phone mockups on a snap-scroll shelf. **On a phone it is a
   one-up swipe** with the slide centred, neighbours peeking, dots and a `1 / 5`
   counter. **On desktop it is a three-across shelf.** The screens are *drawn*
   from the app's own CSS components, not screenshotted, because those screens
   are being redesigned in parallel sessions right now.
3. **Proof** — see §4. Ships in an honest "New here." state.
4. **The short version** — three claims, no feature grid anywhere on the page.
5. **Library** — the 112-compound SEO surface, as a band of pills.
6. **FAQ + closing CTA** — five questions, a second store button, a second
   photographic band.

**Behaviour.** Scroll-reveal animations gated behind a `.js` class with a
2.2-second watchdog; background drift that runs only while its section is on
screen; a carousel whose dots track scroll position; `prefers-reduced-motion`
respected throughout, including a live listener for mid-session changes.

**Contracts with the rest of the site.** The store buttons are
`.store-badge[data-store="play"]` and the email field is
`form[data-form="waitlist"]`, so `site.js` owns both behaviours exactly as it
does everywhere else. Until a Play URL is pasted into `site.js`, the store
button falls back to a "notify me" mailto.

---

## 3. What changed, and why

### 3.1 Four passes on the design, three of them corrections

- **Pass 1** (`42e05c6`) — three directions built from the brief's *description*
  of the app. Wrong: flat charcoal panels with hairline rules.
- **Pass 2** (`cc8fd8f`) — opened `docs/design/mockups/v9.css` in the app repo.
  The app is a photograph under glass, and line 75 of that file names the
  reference out loud: *"Oura's move: the top chrome sits on a BAND, not on the
  photograph."* Rebuilt to it. **Lesson: I designed from a sentence about the
  system instead of the system.**
- **Pass 3** (`490ec17`, `a981ab7`) — cut to a store gateway. Feature deep-dives,
  the derived-palette section and most prose removed.
- **Pass 4** (`088c564`, `0415516`) — production-readiness and the gauntlet.

### 3.2 The hero photograph is generated locally and chosen by measurement

`tools/gen_hero.py` drives ComfyUI + flux-dev on the local 5070 Ti — the same
pipeline the app's own grounds came from. Original images, no licence.

**The first pool was wrong, and the prompt was why.** It inherited the app's
composition rule verbatim: *"a vast empty gradient sky … with no clouds and no
detail."* Correct behind a phone's day strip; on a 4K web hero it produces an
empty blue rectangle. That rule was solving the app's problem on the site's
canvas. The second pool asked for real places, and the finding inverted:

| pool | detail (stddev) | white-headline contrast |
|---|---|---|
| first (empty skies) | 13 – 33 | 2.59 – 6.08, **two failed the 3:1 floor** |
| second (environments) | 49 – 82 | 4.04 – 15.92, **all twelve passed** |

The detailed images are the legible ones, because they are darker. Shipped
`alpine_b`; `pines_b` ships as `hero-alt` (swap two filenames).

### 3.3 The contrast work — the part most worth reviewing

The original `headline_contrast()` reported the shipped ground at **7.05:1**.
That number was measuring the wrong thing: one horizontal band the headline does
not occupy, ignoring the tinted band, ignoring the text scrim, and never looking
at the 11 px eyebrow, which is the hardest element on the page because small
text needs 4.5:1 rather than 3:1. **Composited properly, that ground put the
eyebrow at 1.67:1.**

A radial scrim behind the text block could not fix it — the failing rows sit in
a dead zone above the radial's useful area and below where the band has faded
out. Solved by search instead: band `24% → 30%`, plus a vertical text scrim,
optimising for how much photograph survives.

`python tools/gen_hero.py --gate` now reproduces the page's entire layer stack
and checks every piece of hero type at its real size and position. **Both
shipped grounds pass.** Swapping the ground re-validates rather than silently
regressing.

### 3.4 Bugs found and fixed

**In the live site, not just the candidate:**

- `site.js` bound *both* `form[data-form="waitlist"]` and the generic
  `form[data-form]` to the same form. Both fired; the generic one won. **Every
  launch-list signup on the live homepage opens a mail draft titled "[Stack]
  Feedback"**, and an invalid address bypasses the validation the first handler
  had already rejected it with. Fixed.
- `site.js` used `NodeList.prototype.forEach` in ten places with no shim, so on
  Safari < 10 the whole IIFE threw and nothing bound. Shimmed.

**Two that were invisible to an overflow check,** because `body{overflow-x:hidden}`
was swallowing them — `document.scrollWidth` reported clean while the layout was
broken:

- `.wrap` sets `padding:0 var(--gut)`; `.hero`, `.sec` and `.close` each set the
  `padding` **shorthand** afterwards, resetting left/right to 0. Hero, library
  band and closing CTA rendered edge-to-edge with no gutter. *Same
  shorthand-vs-longhand collision that hit 100+ pages in the July overhaul.*
- `.wrap` also sets `margin:0 auto`. Auto **cross-axis** margins switch off
  stretch in a column flex container, so `.hero` laid out at max-content —
  362 px inside a 320 px parent.

**In `social-proof.js`, the file written to prevent fabricated ratings:**

- `stars(q.stars)` defaulted to `Math.round(n || 5)`, so a beta quote with no
  `stars` value rendered five gold stars and `aria-label="5 out of 5"`.
- `esc()` blocked attribute breakout but not a `javascript:` scheme in the
  listing URL.
- The rating-present-but-no-quotes state wiped the three "check it yourself"
  links off the page.

**In `tools/gen_hero.py`:** the `if __name__ == "__main__"` block sat mid-file,
so every helper appended after it was undefined when `main()` ran. Importing the
module hid it completely.

**Other:** five phone mockups had four page dots between them and the last two
marked the same one active; `#pen` was a dead SVG def; `.on-page .btn`,
`.stage .lede`, `-webkit-overflow-scrolling` and a `min-height` were dead CSS;
`min-height:86svh` was written before `86vh` so the `svh` never applied.

### 3.5 Performance

- Added the missing **1280w** hero candidate. A DPR-3 phone was taking 1920w for
  a ~1275 px box — **96 KB instead of 184 KB on the LCP of the most common
  device class there is.**
- The closing band's `srcset` stopped at 1920w while `sizes` said `100vw`, so a
  2× desktop fetched the same photograph twice (188 KB wasted).
- `drift` now runs only while its section is on screen. Previously both grounds
  animated from t=0 forever, and seven glass elements over them recomputed their
  backdrop blur every frame to match — a 60 fps cost that never idled.
- Dropped `backdrop-filter` from the six panels **inside the scrolling
  carousel** (they measure 8:1 without it), which is the classic iOS jank shape.
- Removed the 876 KB `InterVariable.ttf` `@font-face` fallback: `src` fallback
  fires on a 404, not only on an unsupported format.
- Deferred `rail-config.js`; added `?v=5` cache-busters.

**Weight today:** DPR-3 phone ≈ 154 KB above the fold (96 KB hero + 58 KB font). 4K hero 515 KB, 1920
184 KB, 1280 96 KB, 960 62 KB.

### 3.6 Accessibility

`<header>` was not a banner (it is inside a `<section>`), and the hero and
closing CTA sat outside every landmark — so the `h1`, both store buttons and the
email form were in none. The carousel claimed `role="tablist"`/`role="tab"` with
no `aria-selected`, no `aria-controls`, no tabpanels and no arrow keys, and the
scroller had **zero focusable children** — at ≥900 px, where the dots are
hidden, slides 2–5 were unreachable by keyboard. Five phone mockups dumped ~180
unstructured nodes into the accessibility tree. The form's status line had no
live region while `novalidate` had switched off the browser's own announcement.
All fixed. Heading order is now H1 → H2 ×3 → H3 ×3 → H2 ×3 with no skips.

### 3.7 Copy, cross-checked against the legal docs

Dropped "permanently" and "ever" (terms reserve the right to modify); made "the
account only ever knows your email" conditional on backup being off (the policy
explicitly carves that out); replaced an "export on any plan" claim on a card
pointing at a policy that never mentions plans; added the **3-per-week Sage cap**
the pricing page enforces and the page did not mention; removed an active price
`Offer` from JSON-LD for a product the page says has not launched; matched the
FAQ questions to the marked-up ones.

Rotation copy said "Next · right abdomen" and "Clear", which reads as the app
adjudicating which injection site is safe to use. It now reports where you have
been. Dropped a specific **250 mcg** dose of an unapproved peptide from the
promotional art and moved **retatrutide** behind the library index — the two
highest-risk elements for Play review.

Restored the contact route (the page had no `mailto` at all) and re-linked
`stacks/` and `referral.html`, which were orphaned.

---

## 4. The social-proof design — review this hardest

**The constraint.** Every competitor leads with a number. Stack has none, and the
plan was for friends and family to leave 5-star reviews at launch.

**Why that plan is dangerous.** Play does not need to prove anyone is a relative.
A cluster of new accounts rating five stars days apart, most installed minutes
before reviewing, some never having opened the app, with a rating distribution
that is 100% five stars — that pattern is itself the finding. Reviews are
removed silently, the rating goes with them, and it lands in launch week. There
is no hearing and the appeal path is thin. (The FTC's 2024 review rule does cover
undisclosed relatives and *would* need evidence, but it is aimed at a much larger
class of business; Play enforcement is the practical risk.)

**The workaround, built as code rather than advice.** `assets/js/social-proof.js`
drives three states from one config block:

| state | when | what renders |
|---|---|---|
| 1 | no rating, no quotes | **"New here."** Says so plainly, then three things you can verify now: 112 cited pages, a calculator that runs in the browser, the privacy policy. **Written into the HTML**, so it survives JS being off — this is what ships today. |
| 2 | quotes, no rating | a beta-feedback wall, labelled as beta feedback, not dressed as store reviews |
| 3 | rating + quotes | the real thing, score and count off the live listing |

Moving between states is editing `window.STACK_PROOF`. **At no point does the
page claim something untrue**, which removes the temptation. The honest state is
also a position no competitor can copy.

**Filling it legitimately, fast:** Play's In-App Review API, fired once, on a
moment where the app has visibly done something — for Stack that is the first
time the refill projection warns someone early enough to reorder. Not first
open, not launch day, not twice. That is an app-side change and is **not built**.

All three states and an XSS probe were exercised in a browser; the probe fired
zero times.

---

## 5. How to re-verify

```bash
cd C:/src/stack-website
python tools/gen_hero.py --gate            # hero type legibility, all 7 elements
python tools/gen_hero.py --gate pines_b    # the alternate ground
python tools/gen_hero.py --rank            # tone / detail / contrast for the pool
python tools/gen_og.py                     # rebuild the share card
```

Serve and open `index-v2.html` (`.claude/launch.json` defines the server).
Checks worth repeating: 320 / 390 / 768 / 1440 px; strip the `js` class off
`<html>` and confirm everything is still visible; submit the email form and
confirm the mail subject is the launch-list one, not "[Stack] Feedback".

---

## 6. Open questions and known weak points — attack these

1. **`terms.html` and `privacy.html` contradict each other on accounts.** Terms
   §Account: *"Using the App requires a Stack account."* Privacy line 94: *"You
   can use Stack without an account."* The page says "No", matching privacy and
   the app's actual "Continue without an account". **I did not edit the legal
   docs** — that is a decision, not a typo. One of them is wrong and it should be
   fixed before store review.
2. **The interior is a different product.** This page is dark and photographic;
   the other ~120 pages are light paper with gold. One click and you see it.
   Reskinning `mono.css` and the library is the next real job and is not started.
3. **Dark-only.** The page has no `data-theme` bootstrap. Someone who pinned
   light mode elsewhere gets a hard-dark homepage. Deliberate, but a decision.
4. **No mobile nav.** Below 900 px the header is brand + "Get the app"; the four
   nav links are footer-only. Defensible for a landing page, worth a second
   opinion.
5. **The scrim constants are tuned to `alpine_b`.** The gate enforces them, but
   changing the ground means re-running it and possibly re-solving.
6. **The phone mockups are drawn, not real screenshots.** Correct while the app
   screens are mid-redesign; needs revisiting once they settle.
7. **`index-v2.html` is `noindex` and lives beside `index.html`.** Promoting it
   means renaming over `index.html`, deleting the `noindex`, bumping the
   sitemap `lastmod`, and re-checking the canonical.
8. **HTML comments ship.** The file is heavily commented with engineering
   rationale. Some of it names competitors. Consider stripping at deploy.
9. **No AVIF/WebP.** `hero-1920.jpg` would be ~90–100 KB in AVIF.
10. **Another session is COMMITTING to this branch.** `21bc38e` ("Three rebrand
    directions, with photography generated on the box") is not mine — 17 files,
    2,388 lines, under `mockups/` plus `tools/gen_header.py`. I checked it for
    overlap: it touches nothing of mine, and my files are intact at HEAD. But two
    agents committing to one working tree on one branch is a real hazard, and it
    means the branch now contains two independent design directions. Whoever
    reviews this should know both exist: mine is `index-v2.html`, theirs is
    `mockups/rebrand-*.html`. I have never used `git add -A`; every commit of
    mine lists its files by name.

---

## 7. What I would tell a critic to check first

- Re-run `--gate` and disagree with my type-position constants in `HERO_TYPE`.
  They are estimates of where each element sits as a fraction of the stage; if
  they are wrong, the pass is wrong.
- The `.js`-gated animation plus watchdog: convince yourself the page cannot
  ship blank under any JS failure.
- `social-proof.js` states 2 and 3 with hostile config — I tested XSS, but not
  malformed shapes (`quotes` as a string, `play` as null).
- Whether cutting the feature detail went too far. The page is now a door; if
  someone needs to understand supply projection before downloading, it is gone.
- The claim in §4 that the honest proof state converts. I believe it and I have
  not tested it.
