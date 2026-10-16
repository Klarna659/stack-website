# Site truth audit, 2026-10-16

Branch `truth-2026-10-16`, based on `origin/main` (c11af5a). Checked against the app code in
`C:\src\dt_bugs\lib` (branch `bugs-2026-10-13`), `docs/DATA_INVENTORY.md`, `legal/`,
`docs/growth/SITE_CHANGES_NEEDED.md`, `docs/PRICING_PLAN.md` and `StackProducts` in
`lib/features/paywall/entitlement.dart`.

## What is actually live

Since the 2026-10-12 cleanup (PR #3, merged), the only real pages are `index`, `pricing/`,
`privacy`, `terms`, `data-deletion`, `creators`, `referral`, `account/` and `404`. Every other
old URL (`about/`, `guides/*`, `compounds/*` incl. `compounds/compare/*`, `compare/*`, `stacks/`,
`tools/*`) is a 359-byte redirect stub to `/`. No competitor content and no compound,
guide or tool copy is live, so there was nothing to fix on those, and PR #2
(`no-competitor-mentions`) now only matters for the stubs' history.

## Changes

| Page | Was | Now | Why |
|---|---|---|---|
| `index.html` (FAQ + FAQ JSON-LD) | Day 5: "a notification in the app and an email"; "cancel at least 24 hours before day 7" | Day-5 reminder is a notification only, "if notifications are on"; "cancel before the trial ends"; card on file; purchase screen shows the first-charge date | The in-app timeline says "No email yet"; the lifecycle Worker is built but not deployed. The 24-hour rule is Apple's, the trial here is Google Play's |
| `index.html` (cost FAQ + JSON-LD, price fine print) | Dollar prices only | Adds that the prices are USD and Google Play charges in local currency | `StackProduct.localizedWith`: the store price replaces the display string |
| `index.html` (data FAQ + JSON-LD) | "Only three optional things send data off your phone" | Lists cloud backup, Juno, voice dictation, the updates list, feedback | The list was short: voice dictation (OS speech service) and the updates list also send data |
| `index.html` (Juno FAQ + JSON-LD) | No mention of consent or the server hop | Says the app asks permission before the first message and the text goes through our server to an AI provider | `ai_consent.dart` (one-time prompt before anything is sent); `bot_client.dart` uses the proxy Worker |
| `index.html` (delete FAQ + JSON-LD) | "Account > Delete account removes your account and any cloud backup" | `Settings > Account > Delete account` removes the account, wipes the log on that phone, removes a backup under the same email | `account_screen.dart` delete dialog and `faq_screen.dart`: it also wipes the device, and a backup under a different email stays |
| `index.html` (footer tag) | "one private app" | "one app" | Soft privacy claim that Juno, cloud backup and share links qualify |
| `pricing/index.html` (timeline) | Day 5 "notification ... and an email"; Day 7 "unless you cancel before then" | Notification only, if notifications are on; "before the trial ends" | Same as home |
| `pricing/index.html` (plans note) | "Every plan starts with 7 days free. Subscribe ... through Google Play." | Adds card on file, local-currency charge, restore with same Google account | Store shows the real price; trial needs a payment method (Terms 6.4) |
| `pricing/index.html` (FAQ + JSON-LD) | "Is there a free version?" answered "There is a 7-day free trial." | "No. There is no free plan, only a 7-day free trial ..." | Hard paywall, no freemium. The old answer read like a yes |
| `privacy.html` | Last updated Sept 4. Said updates-list sign-up stores an install identifier; said Sentry "never" sends IP; Supabase for everything optional; no consent prompt; no share links; delete = "Account > Delete account removes account and backup" | Last updated Oct 16. Install ID is local only and not sent; Sentry attaches no IP but the request still comes from the device network address; per-feature providers; Juno consent prompt; share links disclosed; creator code recorded with subscription status; full account-deletion behaviour with link to the deletion page; "nobody under 13" added to the children section; automatic transmissions now include subscription status | `newsletter_service.dart` (install_id removed 2026-09-09), `analytics.dart` comment on Sentry, `ai_consent.dart`, `share_link_service.dart` + `stack_snapshot.dart`, `account_screen.dart`, `creator_code.dart`. See "Needs Sim's decision" 2 and 1 |
| `terms.html` | Last updated Oct 12; creators link without `.html` | Last updated Oct 16; adds "prices on our website are USD for reference, the store charges in local currency"; link to `creators.html` | Matches the store-price rule. Trial, renewal, store cancellation, refunds-by-store, hard-paywall lapse wording, guest mode, Juno disclosure and 18+ were already correct and are unchanged |
| `data-deletion.html` | Last updated Sept 4; "local-first"; summary had no account deletion; sign-up record listed an install identifier; no share links | Last updated Oct 16; account deletion in the summary and Section 2 with exact behaviour (type DELETE, wipes the phone, cloud-backup-under-a-different-email case); install ID removed; share link deletion added | Same code as privacy. Google Play wants the deletion path to be findable from the page |
| `referral.html` | Perk "Custom card backgrounds for your audience" | "Your code stamped on your Stack flex card" | Terms 6.1: card backgrounds are included for everyone, so it was not a perk. The creator code on the card is real (`card_background_store.dart`) |
| `account/index.html` | Signed-in "Membership" badge "Not subscribed"; "see the same subscription status ... nothing to restore" | Panel says the subscription is managed in the app (Settings > Subscription) and in Google Play, and that this page does not show it | No migration in the app repo creates an `entitlements` table, so the badge would have shown "Not subscribed" to every paying user |
| `assets/js/account.js` | Fetched `/rest/v1/entitlements` and wrote the badge | That lookup and badge code removed | Same reason; stops a request to a table that does not exist |
| `sitemap.xml` | lastmod 2026-10-12 | 2026-10-16 for the six changed URLs (not `creators.html`) | Only where substance changed |

## Checked, no change needed

- `creators.html`, `404.html`, `robots.txt`, `CNAME`, `google3e519fa60f81331a.html` (present, untouched), `assets/js/site.js` (store buttons already relabel to "Get notified at launch" because no store URL is set), `assets/js/rail-config.js` (checkout URLs are placeholders; no checkout is live).
- No Sage, no $9.99 / $59.99 / $4.99 / $50 / $75 / $124.99, no 14-day trial (the 14 in creators/terms is the creator-code trial), no lifetime for sale, no CSV, no "free forever", no "nothing leaves your device", no widget claims, no efficacy claims, no emoji, no new scripts or analytics anywhere.
- Prices on `/` and `/pricing/`: $7.99 / $29.99 / $44.99 and the struck $95.88 (12 x $7.99) match `StackProducts` exactly, and the home and pricing pages now say the store charges in local currency. That reverses the old LAUNCH_FACTS "no prices on the site" rule on purpose, per Sim's current plan; the Play Console prices must stay identical or the site becomes the drift.
- Local serve (`python -m http.server`): `/`, `/pricing/`, `/privacy.html`, `/terms.html`, `/data-deletion.html`, `/creators.html`, `/referral.html`, `/account/`, `/404.html`, `/sitemap.xml`, `/robots.txt` and the Play verification file all return 200. A script checked every internal `href`/`src` on the nine live pages (0 broken) and that each FAQ JSON-LD answer is present in the page text (0 mismatches). Sitemap URLs all exist; `account/` is `noindex` and not in the sitemap.

## Needs Sim's decision

1. **Age.** Terms and privacy say 18+ (also what `legal/` and `legal/PLAY_DATA_SAFETY.md` say). `docs/APP_STORE_LISTING.md` says the saved Apple age rating is 13+. I kept 18+ (the stricter one) and added "nobody under 13". Pick one number and make the app's legal screen, Play target audience and Apple rating agree.
2. **Share links and Health Connect.** Both are switched OFF in release (`shareLinksEnabled` and `healthConnectEnabled` default false), so the privacy and deletion pages no longer mention them (a first pass had added share links; removed 2026-10-16 after checking the switch). Add the text back, together with the app policy, Data safety and the Play Health declaration, on the day either ships.
3. **Day-5 email.** Removed from the site until the lifecycle Worker is deployed. Put it back then.
4. **Creator "14 days free instead of 7".** The Play `creator14` offer did not exist when `CREATOR_CODES_STORE_RULES.md` was written, and the in-app redeem sheet says "30 free days" for creator-trial codes. `creators.html` and `referral.html` still promise 14. Confirm before outreach.
5. **Web checkout / Stripe wording** is still in privacy, terms and data-deletion as "if we offer". No checkout is live. Leave the hedge or delete it.
6. **Public internal docs.** `SITE_CHECKLIST.md`, `WEB_RAIL.md`, `SESSION_D_HANDOFF.md`, `DESIGN_RESEARCH.md` sit in the repo root and GitHub Pages publishes them; the first still shows the $4.99 / $50 / $75 prices. Move or delete them, or add a Pages exclude.
7. **Waitlist data.** The old hero form posted to the `stack-waitlist` Worker (KV) from 2026-09-07. No form exists on the site now and the privacy page does not describe that list. Delete the KV entries or describe them.

## Could not verify

- That Sentry's project does not store the connecting IP (the app policy claims it; the code comment says it is a dashboard setting). I removed the claim from the site instead of repeating it.
- That the bot-proxy Worker keeps no conversation logs (site says "we do not keep the conversations", copied from the app policy; the deployed Worker was not inspected).
- Whether the Play listing or any store build is live (site.js has no store URL, so the buttons say "Get notified at launch").
- Whether Google Play needs cancellation 24 hours before the trial ends. Terms keep the conservative 24-hour wording; the marketing pages say "before the trial ends".
- Home-screen widgets: none exist in the Android code (no AppWidget receiver, no widget package), so the site makes no widget claim.
- Habits, groups, half-life curves, the reconstitution calculator, bloodwork and refill projection exist in the code but are barely on the marketing pages. I added no new feature copy.
- Health Connect is off in release builds (`LaunchSwitches.healthConnectEnabled`); the privacy page still lists it because the permissions are in the manifest.

## Added later on 2026-10-16

- **Demo media re-recorded** from the current app with supplements-only example data
  (`assets/img/app/*`: build_stack, doctor_report, hero_juno, injection_sites,
  juno_actions, hero_today_still). The old ones were the pre-Photo-theme UI and the
  doctor-report clip printed "bloodwork (with flagged results)", which the report no
  longer contains; the build clip typed a prescription drug and dose.
- **Home report caption** no longer says "flagged labs" (report v2 has no labs).
- **Home "On your phone" cell** says "An account is optional" (the canon bans "no account").
- **Share links and Health Connect** removed from privacy and data-deletion (both are
  switched off in release). Add them back, with the app policy and store forms, the day
  either ships.
- Still open here: `/creators.html` and `/referral.html` promise "14 days free instead of
  7" while an in-app creator code grants 30 days; Sim to pick the number.
