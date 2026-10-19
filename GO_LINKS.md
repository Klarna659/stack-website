# Campaign links: /go/ pages and the Google Play button

Working note, not published (listed in `_config.yml` under `exclude`).

## What exists

| Page | Custom Play listing it sends to | Use it for |
|---|---|---|
| `/go/` | default listing (no `listing` parameter) | general bio links, paid ads that name no side door |
| `/go/routine/` | `routine` | printable templates, most paid ads, vitamin and supplement audiences |
| `/go/injections/` | `injections` | weekly-shot audiences, creators who post about injections |
| `/go/labs/` | `labs` | unit-converter pages, coaches, hormone-therapy audiences |

The three door names match the drafts in `docs/growth/CUSTOM_STORE_LISTINGS_2026-10-17.md`
(`injections`, `labs`, `routine`). Every `/go/` page is `noindex,follow`
and is not in `sitemap.xml`. Do not Disallow `/go/` in `robots.txt`: noindex only
works if the page can be crawled.

## The one constant

`assets/js/go.js`:

```js
var PLAY_URL = "TODO_PLAY_URL";
```

Replace it with the store listing URL, no listing or referrer parameters:

```js
var PLAY_URL = "https://play.google.com/store/apps/details?id=app.trackyourstack";
```

Anything that is not an `https://` URL, and anything still containing `TODO`,
counts as "not set". Bump the `?v=1` on the `go.js` script tags (home and the
four `/go/` pages) so browsers fetch the new file.

### While it is not set

- `/go/` buttons read "Coming soon to Google Play", look disabled, have no link
  and are skipped by the keyboard.
- The email capture form on those pages shows only when `assets/js/capture.js`
  has a real Worker URL (`WORKER_URL`). Until then it stays hidden.
- Homepage buttons marked `data-play` keep their old behaviour: the nav pill and
  the sticky bar go to `/pricing/`, the hero badge says "Get notified at launch"
  and opens the same mail draft as before.

### After it is set

- Every `[data-play]` element gets `href` = the Play URL, plus
  `&listing=<door>` (from the attribute value: `data-play="injections"`) and,
  if the page address carries `utm_*` parameters,
  `&referrer=<url-encoded utm_source=...&utm_medium=...&utm_campaign=...&utm_content=...>`.
  Google Play passes `referrer` to the app's install referrer, and the Play
  Console acquisition reports show the `utm_*` values.
- `[data-play-on]` shows, `[data-play-off]` hides (the "Coming soon" label and
  the capture form). The hero badge switches to the Google Play glyph and label.
- Only `utm_source`, `utm_medium`, `utm_campaign`, `utm_content` and `utm_term`
  pass through. Nothing else in the page address goes anywhere.

### Markup

```html
<a class="btn ..." data-play="routine" role="link" aria-disabled="true">   <!-- door button -->
<a href="pricing/" data-play>Get the app</a>                              <!-- default listing, keeps href while unset -->
<span data-play-on hidden>Get Stack on Google Play</span>                 <!-- label shown once set -->
<span data-play-off>Coming soon to Google Play</span>                     <!-- label shown while unset -->
```

The pricing page badges (`/pricing/`) are older and still use the `urls`
object in `assets/js/site.js`; set both when the listing goes live, or convert
those two buttons to `data-play` the same way as the homepage hero badge.

## Link patterns

```
https://trackyourstack.app/go/injections/?utm_source=tiktok&utm_medium=bio&utm_campaign=launch&utm_content=hook12
https://trackyourstack.app/go/labs/?utm_source=newsletter&utm_medium=email&utm_campaign=launch&utm_content=coach-a
https://trackyourstack.app/go/routine/?utm_source=meta&utm_medium=paid&utm_campaign=test1&utm_content=concept1
https://trackyourstack.app/go/?utm_source=youtube&utm_medium=shorts&utm_campaign=launch&utm_content=demo
```

Keep `utm_content` short and lowercase (a hook number, a creator code). Never
put a person's name, email or anything about what they take in a link. Per the
growth plan, do not point a paid ad at a custom listing until it has been live a
week without a policy notice.

## How to test

1. Unit tests: `node --test` at the repo root (`assets/js/go.test.js`).
2. Serve the folder (`python -m http.server 8000`) and open
   `http://localhost:8000/go/injections/?utm_source=tiktok&utm_medium=bio&utm_campaign=launch&utm_content=hook12`.
   - Not set: the button is greyed and says "Coming soon to Google Play".
   - Set `PLAY_URL` in a scratch copy: the button reads "Get Stack on Google Play"
     and its `href` is
     `https://play.google.com/store/apps/details?id=app.trackyourstack&listing=injections&referrer=utm_source%3Dtiktok%26utm_medium%3Dbio%26utm_campaign%3Dlaunch%26utm_content%3Dhook12`.
3. On a phone with Stack not installed, open the link from a TikTok bio or a
   message and confirm Google Play opens on the matching custom listing.
4. After a test install, the Play Console acquisition report (and the app's
   install-referrer read, if it reads one) should show the `utm_*` values.

## CSP note

The `/go/` pages use the same strict pattern as the tool pages (scripts from
`self` plus the hash of the theme snippet, no inline handlers) with one change:
`connect-src https://*.workers.dev`, so the capture form can reach the
Cloudflare Worker once it is deployed. If the Worker gets a custom domain,
change that one value on the four pages.
