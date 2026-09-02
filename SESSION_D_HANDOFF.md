# Session D — the website. Overview and handover.

**Repo:** `C:\src\stack-website` · **Branch:** `master` · **Night of 2026-09-01 → 02**
**Nothing pushed. `index.html` — the live homepage — is untouched.**

Written for a reviewer who was not in the conversation. It says what exists,
what state each piece is in, what is actively wrong, and where I think my own
work is weakest. **Section 5 is the part I would read first if I were reviewing
this** — it is where the schemes have holes.

---

## Read this first

1. **I never actually looked at the page.** The browser pane in this session
   never composited a frame all night. Every visual claim below comes from
   computed styles, DOM measurement and pixel arithmetic on the image files —
   **not from seeing it render.** The layout numbers are trustworthy; "does it
   look right" is not established. Open `index-v2.html` on a real phone before
   trusting anything aesthetic.
2. **There is a bug on the live site right now.** See §4.1. It has been quietly
   breaking the homepage email capture, and the fix needs a one-character deploy
   step that is easy to miss.
3. The deliverable is `index-v2.html`. It is not promoted, and it is `noindex`
   so it cannot be crawled as a duplicate in the meantime.

---

## 1. What this section is

`trackyourstack.app` — a static site on GitHub Pages behind Cloudflare, the
front door for **Stack**, an Android app (iOS later) that logs everything you
take on a schedule: supplements, vitamins, prescriptions, peptides, GLP-1s, TRT
— plus supply projection, injection-site rotation, modelled in-system levels,
weight and bloodwork.

~130 pages. What I touched:

| File | State |
|---|---|
| `index-v2.html` | **new — the deliverable.** Production-ready, not promoted |
| `assets/js/social-proof.js` | new. Three-state proof renderer |
| `assets/js/site.js` | **modified — shared by every page, fixes the live site** |
| `tools/gen_hero.py` | new. Local image generation + a legibility gate |
| `tools/gen_og.py` | new. Rebuilds the share card from the hero |
| `assets/img/hero/*`, `assets/img/grounds/*`, `assets/img/og-v2.jpg` | new |
| `mockups/direction-*.html`, `mockups/landing-v2.html` | superseded drafts, kept as record |
| `index.html`, `compounds/`, `mono.css`, legal pages | **not touched** |

---

## 2. What the page is

Six sections, **4,958 px** at a 390 px viewport. The live page is 13,589 px.

1. **Hero** — full-bleed generated photograph with the app's three-layer
   treatment (photograph → tinted band → scrim), headline, store button, email
   capture, an honest proof line.
2. **Screens** — five phone mockups. **Phone: a one-up swipe**, slide centred,
   neighbours peeking, dots + a `1 / 5` counter. **Desktop: a three-across shelf.**
3. **Proof** — three states, see §5.1. Ships honest.
4. **The short version** — three claims. No feature grid anywhere on the page.
5. **Library** — the 112-compound SEO surface as a band of pills.
6. **FAQ + closing CTA.**

The design language is lifted from the app's `docs/design/mockups/v9.css`, not
invented: the glass card values, the band colour, the scrim ramp, IBM Plex Mono
eyebrows over Inter, the row proportions, the easing curves.

---

## 3. Status — what is actually finished

### Done and verified
- Layout at 320 / 390 / 768 / 1440 px. No horizontal overflow anywhere.
- **Every piece of hero type clears WCAG AA**, verified by compositing the
  page's real layer stack over the real shipped JPEG. `--gate` re-checks it.
- No-JS: strip the `js` class and the whole page still renders. It cannot ship
  blank under any script failure.
- Link integrity: every `href` and asset resolves, no dangling anchors.
- Social-proof states 1, 2 and 3 exercised in a browser, including an XSS probe
  that fired zero times.
- Heading order H1 → H2 → H3 with no skips, landmarks correct, carousel
  keyboard-reachable.
- Six parallel audits (accessibility, CSS/cross-browser, JavaScript,
  performance, copy/compliance, link integrity). ~30 real defects found, fixed.

### Done but unverified in the real world
- **Anything visual.** See "Read this first".
- iOS Safari behaviour. Nothing has run on an actual iPhone.
- Whether the page converts better than the live one. There is no analytics on
  it at all.

### Not started
- Promoting `index-v2.html` over `index.html`.
- Reskinning the other ~120 pages.
- Anything that automatically fills the proof section (§5.1).
- Real screenshots in the carousel.

---

## 4. Trouble — things that are wrong right now

### 4.1 The live site's email capture is broken, and the fix is cache-gated

`site.js` bound the waitlist form **twice** — once as `form[data-form="waitlist"]`,
and again via the generic `form[data-form]`, which matches it too. Both fired;
the second overwrote the first. So on trackyourstack.app today:

- every launch-list signup opens a mail draft titled **"[Stack] Feedback"**;
- an invalid address bypasses the validation the first handler already rejected
  it with, and opens an empty draft anyway.

Fixed in `site.js`. **But `index.html` loads `assets/js/site.js?v=4`, and I
verified that the cached `?v=4` response still contains the old code.** Deploying
the fix without bumping that to `?v=5` leaves the bug in place for exactly the
people who have already visited.

I did not edit `index.html` — the brief said leave the live page alone, and if
you promote `index-v2.html` the question disappears. **But one of those two
things has to happen or the fix does not reach anyone.**

Also fixed in the same file: `site.js` used `NodeList.prototype.forEach` in ten
places with no shim, so on Safari < 10 the whole file threw on its first call and
nothing bound at all.

### 4.2 Two agents are committing to this branch

`21bc38e` — "Three rebrand directions, with photography generated on the box",
17 files, 2,388 lines under `mockups/` plus `tools/gen_header.py` — is **not
mine**. I checked it: it touches none of my files, and my work is intact at HEAD.

But the branch now carries **two independent design directions** produced by two
agents who could not see each other. Mine is `index-v2.html`. Theirs is
`mockups/rebrand-*.html`. A reviewer should look at both and choose, rather than
assume one supersedes the other. I have never used `git add -A`; every commit of
mine lists its files by name.

### 4.3 Your terms and your privacy policy contradict each other

- `terms.html`: *"Using the App requires a Stack account."*
- `privacy.html`: *"You can use Stack without an account."*

The page says no account is needed, which matches the app's actual "Continue
without an account". **I did not edit the legal documents** — one of them is
wrong, that is a decision rather than a typo, and guessing wrong in the other
direction is worse than leaving it. Settle it before store review.

### 4.4 The front door and the interior are different products

This page is dark and photographic. The other ~120 pages are light paper with a
gold accent — the hue that was retired. One click off the homepage and you can
see the seam. Reskinning `mono.css` and the library is the next real piece of
work, and it is large.

### 4.5 Smaller, known, unfixed

- **HTML comments ship.** The file is heavily commented, and some comments name
  competitors and explain positioning. Strip at deploy, or move them to a doc.
- **No AVIF/WebP.** The hero would be roughly half its size again.
- **Mandatory scroll-snap plus a programmatic smooth scroll** is a known WebKit
  conflict. Flagged by the audit, not reproduced, not fixed — needs a real phone.
- **No mobile nav.** Below 900 px the header is the logo and one button; the nav
  links are footer-only.
- **Dark only.** No theme bootstrap, so someone who pinned light mode elsewhere
  on the site gets a hard-dark homepage.

---

## 5. Holes in the schemes — the part worth attacking

### 5.1 The reviews workaround has a hole in the middle of it

**What I built.** `social-proof.js` renders one of three states from a config
block: (1) honest **"New here."** with three things a visitor can verify instead
— ships today, and is written into the HTML so it survives JS being off; (2) a
labelled beta-feedback wall; (3) real store reviews with the score off the
listing. The page never claims something untrue in any of them.

**The hole: nothing updates it.** It is a hand-edited JavaScript object. In
practice that means one of two things, and both are bad:

- it sits in state 1 forever because nobody remembers to edit it; or
- somebody hand-types a rating — which is **exactly the failure the whole scheme
  exists to prevent.** A number on the site that does not match the store is the
  first thing a sceptical visitor checks.

**Worse, the page makes a promise I did not build.** The proof section says
*"When there are reviews, they will be pulled from the Play listing and shown
here — including the ones that are not five stars."* Nothing pulls anything.
That sentence is a statement about the future, and it only stays honest if
someone builds the pull.

**It is not trivial.** There is no public reviews API. Google Play's Developer
API can return your own app's reviews, but it needs an OAuth service account and
a server — and this is a static site with no backend. So it needs one of:

- a **GitHub Action** on a schedule that authenticates, fetches, and commits a
  `social-proof.json` the page reads. No new infrastructure, roughly an hour.
- a **Cloudflare Worker** on a cron into KV. You already run Cloudflare and
  already have a Worker doing the Supabase keepalive.

Until one exists: build it, or **soften that sentence** so the page is not
writing a cheque it has not cashed. I would build the Action.

**Second hole: the honest state is an untested bet.** No competitor does it,
because they all have numbers and would never give them up. I believe *"we have
not launched, here is what you can check instead"* reads as confidence. **I have
no evidence.** It could equally read as "unfinished". There is no analytics on
the page, so we cannot even find out. That gamble is mine, not yours, and it
deserves a second opinion.

**Third: the process parts are not code.** The beta-quote state needs written
permission from each tester and honest labelling. And if a quoted tester is a
friend or a family member, the FTC's disclosure rule applies to that quote too —
being on your own website rather than in the store does not exempt it.

### 5.2 The mobile implementation is designed, not proven

The one-up swipe is the right pattern and I am confident in the *code*: the dots
are built from the slides, labelled from their captions, and track scroll
position, so a swipe and a tap always agree. The maths is verified.

What is not verified:

- **It has never run on a phone.** Not iOS, not Android. Not once.
- `86svh` on the hero is exactly the sort of thing that behaves differently once
  there is a real URL bar.
- Momentum scrolling + mandatory snapping + a smooth programmatic scroll from a
  dot press is the classic iOS carousel failure. I removed the backdrop blur
  from the six panels inside the scroller specifically because that combination
  is where jank lives, but I could not test the result.
- **Keyboard access is minimal.** The shelf is focusable and scrollable, which
  meets the requirement, but there are no arrow-key handlers and no VoiceOver
  pass has been done.

### 5.3 The generated imagery has a maintenance cost

The hero is original, free and regenerable — but:

- **The scrim constants are tuned to this one photograph.** `--gate` enforces
  them, so a bad swap fails loudly instead of silently. But a new ground may
  need the geometry *re-solved*, not just re-checked.
- The margin is **thin**: the 11 px eyebrow passes at 4.61:1 against a floor of
  4.5. A brighter ground fails.
- **The gate's band positions are estimates.** `HERO_TYPE` in `gen_hero.py`
  encodes where each element sits as a fraction of the hero. I derived those
  from the layout, not by measuring rendered positions. If they are wrong, the
  pass is wrong. **This is the single assumption I would most want checked.**

### 5.4 The five phone screens are drawn, not screenshotted

Correct today — three other sessions are redesigning those exact screens this
week, so a pasted PNG would be stale within days. But it means the marketing art
is a **hand-maintained replica** of the app, and replicas drift. It needs
revisiting once the app screens settle, and nothing will remind anyone.

---

## 6. Questions I cannot answer for you

1. **Terms or privacy — which is right about accounts?** (§4.3)
2. **Promote `index-v2.html`, or keep iterating?** If you promote: rename,
   delete the `noindex`, bump the sitemap `lastmod`, confirm the canonical.
3. **Build the review pull, or soften the promise in the copy?** (§5.1)
4. **Mine or theirs?** Two design directions now live on this branch. (§4.2)
5. **Is the honest proof state an acceptable conversion risk to you?** I would
   ship it. It is your launch, not mine.
6. **Do you want analytics?** Nothing on this page is measurable today, so every
   claim about what converts — mine included — is an opinion.

---

## 7. How to re-verify

```bash
cd C:/src/stack-website
python tools/gen_hero.py --gate            # every piece of hero type, 7 checks
python tools/gen_hero.py --gate pines_b    # the alternate ground
python tools/gen_hero.py --rank            # tone / detail / contrast for the pool
python tools/gen_og.py                     # rebuild the share card
```

Serve the repo (`.claude/launch.json` defines the server) and open
`index-v2.html`. Worth repeating: 320 / 390 / 768 / 1440 px; strip the `js`
class off `<html>` and confirm everything is still visible; submit the email
form and confirm the subject is the launch-list one, not "[Stack] Feedback".

**And open it on a phone.** Nothing in this document substitutes for that.

---

## 8. Commits

| | |
|---|---|
| `42e05c6` | three landing directions — superseded, wrong visual premise |
| `cc8fd8f` | rebuilt in the app's real design language |
| `490ec17` | cut to a store gateway |
| `a981ab7` | hero chosen by measurement |
| `585e472` | environment hero, real mobile carousel, named reviews |
| `088c564` | production candidate + the social-proof scheme |
| `0415516` | the six-audit gauntlet |
| `b8403fb`, `fdd6869`, and this | handover |

`21bc38e` between them belongs to the other session.

---

## 9. What I would tell a critic to check first

1. **`HERO_TYPE` in `gen_hero.py`** — the assumption the entire contrast pass
   rests on. (§5.3)
2. **The review-pull gap.** The page promises something that does not exist yet.
   (§5.1)
3. **Open it on an iPhone** and look for carousel jank and hero height. (§5.2)
4. **Whether cutting the feature detail went too far.** The page is a door now.
   If someone needs to understand supply projection *before* downloading, that
   information is no longer on the homepage.
5. **`social-proof.js` with malformed config** — I tested hostile strings, not
   wrong shapes (`quotes` as a string, `play` as null).
6. **Whether any of this is actually more persuasive than what is live.** Six
   audits proved the page is *correct*. Not one of them proved it is *better*.
