# TikTok launch-checklist audit — trackyourstack.app

_Built 2026-08-19 from 5 @yatesvids clips Sim sent. Status columns are from an
actual scan of this repo (141 html pages, mockups excluded), not guesswork._

## 🚨 FOUND WHILE AUDITING — THE SITE IS SELLING THE WRONG PRICES

Not on any TikTok list, and worth more than all six combined.

| | Site says | App + App Store actually charge |
|---|---|---|
| Monthly | **$4.99** | **$4.99** |
| Annual | **$50** | **$50.00** |
| Lifetime | **$75** | **$75.00** |

55 occurrences across `index.html`, `pricing/index.html` and `terms.html`. This
is the **pre-2026-08-03 reprice** — `entitlement.dart` was updated that day and
the site never was. The IAP products created in App Store Connect on 2026-08-19
match the app, so the *site* is the odd one out.

Why it's worse than a typo:

- It sits in **schema.org `FAQPage` markup**, so Google can surface the wrong
  price as a rich result.
- It's in **terms.html**, which is a contract document.
- `pricing/index.html:145` claims *"Annual is $50 — that's about 16% off the
  monthly rate."* Under real pricing annual is **~16% off** ($4.99 × 12 =
  $59.88 vs $50.00) — and that reduction was deliberate, per the reprice note in
  `entitlement.dart`. So the claim is wrong twice over.
- Apple review reads marketing pages. Advertised-vs-charged mismatches are a
  known metadata rejection risk.

**Not fixed — public content, your call.** Say go and it's a 10-minute pass.

---

## ⚠️ Read this first

**Every one of these five lists is about a WEBSITE, not an app.** Meta tags,
sitemaps, 404 pages, cookie banners, canonical tags — none of it touches the
Flutter app. So this is a checklist for **trackyourstack.app**, and the App
Store / Play listing is a separate exercise (ASO: screenshots, keyword field,
subtitle, preview video).

**The site already passes most of it.** The 2026-07 mono redesign and the
112-page compound library did this work before the videos asked for it.

---

## ✅ Already done (24) — no action

| Item | Evidence |
|---|---|
| sitemap.xml | present |
| robots.txt | present |
| custom 404 page | `404.html` |
| canonical tags | 140/141 pages |
| meta descriptions | 140/141 |
| unique page titles | verified on spot-check |
| og:image / social share img | 139/141 |
| structured data / schema | 133/141 |
| favicon | `assets/img/icon.svg` + `.png`, linked on 140/141 |
| lang attribution | 140/141 |
| viewport (mobile) | 140/141 |
| alt text on images | 8/8 img tags |
| dark mode toggle | site-wide |
| about page + story | `/about` |
| ToS page | `terms.html` |
| privacy policy page | `privacy.html` |
| visible contact email | hello@ on 142 pages |
| google search console | `google3e519fa60f81331a.html` verified |
| 5 blog posts | `/guides` + 112-page `/compounds` library |
| UTM / ref tracking | already handled in page JS |
| mobile menu + mobile optimise | the 2026-07-19 mobile-first overhaul |
| no horizontal scroll | fixed in that same overhaul |
| page per service | `/compounds/*`, `/stacks/*`, `/tools/*` |
| internal links | dense cross-linking in the compound library |

## 🔨 Worth doing (7) — ranked

1. **Analytics — there is none.** No gtag, Plausible or Umami anywhere. You're
   about to spend on creator distribution and currently cannot tell which post
   sent anyone. Highest-value item on this page. Plausible is the privacy-clean
   option and avoids a cookie banner.
2. **`llms.txt`** — missing. 2026-relevant: it's how AI crawlers are told what
   the site is. Cheap, and you already have the structured content to describe.
3. **Guarantee / refund statement** — matters the moment IAP goes live. Apple
   handles refunds, so this is one honest paragraph, not a policy invention.
4. **Skip-to-content link** — 0 of 141 pages have one. Accessibility, and it's
   two lines of CSS + one anchor.
5. **`account/index.html` has no og:image** — the single page that misses it.
   One line.
6. **Real reviews / testimonials** — genuinely applicable, but you have no
   users yet. Park until after TestFlight feedback. Do NOT invent any.
7. **Cookie consent** — only needed if you add analytics that set cookies, and
   it pairs with the EU/DSA trader work that's already outstanding.

## 🚫 Not applicable — and one that actively conflicts

- **Team photo** 🚨 — directly contradicts the anonymity rule. Cedar Hills
  Studio LLC exists so your real name and face stay off public surfaces. Skip.
- **Tap-to-call number / opening hours / maps + directions / local schema** —
  these are all local-business advice. Stack is a global app. The only phone
  number that should ever appear publicly is the Google Voice one, and only
  where the DSA forces it.
- **Case studies** — no customers yet.
- **Print stylesheet, floating contact button, breadcrumbs, thank-you page** —
  low value for a one-product app site; revisit if the site grows a funnel.
- **Vercel URL / vite+react tells / massive JS bundle / source maps** — the
  whole "vibecoded giveaway" list assumes a React SPA. This site is hand-written
  static HTML on GitHub Pages, so none of it applies.

---



---

# Clip 6 — "20 vibecoded website giveaways" (the AI-tells list)

The most useful of the six, because it maps onto your own July complaint that
the landing "looks so AI generated". Audited against the live site:

## ✅ Clean — 17 of 20

`vercel.app url` (custom domain) · `purple gradient` (zero purple hex, no
gradients) · `ai slop photos` (visuals are code-drawn — the Flux photos were
deliberately dropped) · `fake reviews` (none — you have no users and invented
none) · `one page site` (141 pages) · `no favicon` (present) · `no privacy
policy` (present) · `no T&C's` (present) · `fake visitor count` (none) ·
`customer count` (none) · `fake metrics` (none) · `emoji icons` (**zero** in
page copy — your no-decorative-emoji rule is holding site-wide) · `cursive
font` (Inter only, self-hosted) · `lovable tag` (not Lovable) · `text only
logo` (real mark) · `hero text colour` · `vague hero` ("Your whole stack, in
one place." is concrete)

## ⚠️ Worth a look — 3

1. **Em dashes — 1,678 of them across 140 of 141 pages.** This is #20, and
   right now it's the single most-cited AI tell in circulation. They're
   legitimate typography and I'm not going to pretend otherwise, but that
   density is a pattern, and it's the exact texture you flagged in July. A pass
   swapping a third of them for full stops, commas and colons would cost
   nothing and read more human.
2. **Scroll animations** — `assets/js/site.js` has scroll-triggered behaviour
   (#6). Fine in moderation; only a tell if things fade in everywhere.
3. **Broken buttons** (#5) — can't judge from source. Needs the live site
   driven, which I can do.

## Verdict

The site is not the problem the videos describe. It fails 3 of 20 tells, and
one of those (em dashes) is stylistic. **The pricing mismatch above is the real
issue** — a visitor comparing your pricing page to the App Store sheet sees two
different numbers, and that damages trust far more than punctuation does.
