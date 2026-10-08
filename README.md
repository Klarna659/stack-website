# Stack — website

Marketing + SEO + premium-conversion surface for the Stack app. Plain
HTML/CSS/vanilla JS, no build step, no runtime dependencies. Live at
**https://trackyourstack.app** (GitHub Pages behind Cloudflare, DNS-only).

## Brand
Split-S mark, ported 2026-09-28 from `../dose_tracker/docs/growth/brand_world/`
(that repo's `README.md` there explains the build). Locked: a teal tile
(`#5FBFB3`) with a white S, deep teal `#175E58` for text/accents on paper,
paper/ink/night grounds. Paper/light is the default world; dark follows the
OS + a nav toggle, except the homepage, which is a fixed dark photo hero and
doesn't use the toggle. Exactly one accent hue (**teal = earned**, never
decoration/buttons) — carried by the `--gold`/`--gold-fill`/`--gold-line`
tokens in `assets/css/mono.css` (kept that internal name rather than a
150-file variable rename; the *value* is teal everywhere, nothing reads
"gold" anywhere in the UI). The mark itself renders from
`assets/js/mark.js` (exact geometry, do not alter) into every
`<span class="brand-mark" data-mark>` in nav/footer. Inter only, tabular
figures, no emoji, the word "AI" never appears — the assistant is **Juno**
(not "Sage", retired 2026-09).

## Run it locally
```
python -m http.server 8891   # then open http://127.0.0.1:8891/
```
(A plain file open works for most pages, but the account sign-in + relative
routing behave like production only when served.)

## Config — `assets/js/rail-config.js`
One config block for the web rail (see `WEB_RAIL.md`). Supabase URL + anon key
are the app's own committed public (RLS-gated) values. The `checkout.*` RevenueCat
Web Billing URLs are `PASTE_…` until launch; while unset, the buy buttons fall
back to a "notify at launch" mailto. Shared site JS (nav, theme toggle, pricing
toggle, gallery, forms, buy buttons) lives in `assets/js/site.js`; account
sign-in in `assets/js/account.js`.

## Generated content — re-run the generators, don't hand-edit output
```
python tools/build_library.py   # compounds/ (index + 112 pages + 10 compares) + sitemap.xml
python tools/build_pages.py      # guides/, about/, 404.html
```
Compound data lives in `assets/data/compounds.json`. Shared page chrome
(`head`/`nav`/`footer`/`mark`) is defined in `tools/build_library.py` and imported
by `tools/build_pages.py` + `tools/build_compare.py`. Editing a generated
`.html` directly will be overwritten on the next build.

## Deploy
Push to `main` → GitHub Pages publishes. `CNAME` = trackyourstack.app (apex);
GitHub owns the TLS cert (Cloudflare is DNS-only/grey — do not proxy it).
Hosted legal URLs for the store listings:
- `https://trackyourstack.app/privacy.html`
- `https://trackyourstack.app/terms.html`
- `https://trackyourstack.app/data-deletion.html`

## Structure
```
index.html         landing (hero, in-system + rotation visuals, features, pricing teaser, library funnel, FAQ)
pricing/           dedicated pricing + comparison + FAQ (the checkout surface)
account/           magic-link sign-in (noindex)
compounds/         112-compound SEO library + 10 head-to-head compares (generated)
guides/  about/    prose pages (generated)
stacks/ referral.html creators.html   share + creator/partner funnels
privacy.html terms.html data-deletion.html   hosted legal
assets/css/mono.css   the single design system
assets/js/            site.js · account.js · rail-config.js
assets/img/ assets/fonts/   icons/og + self-hosted Inter (subset)
tools/                page generators + reconstitution calculator
```
