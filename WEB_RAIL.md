# Web rail — accounts + Plus checkout (login-only app, web-sold subscription)

The business model: the app is **login-only and free to use**; **Plus is bought on
the web** (dodges the store 30% cut). This doc is the contract for how a web
purchase unlocks Plus inside the app. Store model = **Netflix now, external-link
later** (the app ships with no in-app purchase UI; a compliant "manage on web"
link is a later, optional add).

## The architecture (decided)

```
                    ┌─────────────────────────────┐
   same email       │  Supabase Auth (SHARED)      │      same email
  ┌──────────────►  │  nkxwtlfcezgehskzneqm        │  ◄──────────────┐
  │                 │  user.id = the App User ID   │                 │
  │                 └─────────────────────────────┘                 │
  │                                                                  │
┌───────────────┐         RevenueCat (universal broker)      ┌───────────────┐
│  WEBSITE      │   App User ID = Supabase user.id           │  FLUTTER APP  │
│  trackyour…   │                                            │  Stack        │
│               │   Web Billing (Stripe) ──► entitlement ──► │  reads RC     │
│  sign in      │        "plus" / "lifetime"                 │  CustomerInfo │
│  buy Plus ────┼───────────────────────────────────────►   │  → paidTier   │
└───────────────┘                                            └───────────────┘
```

- **One identity.** The website and the app both authenticate against the app's
  existing Supabase project (URL + anon key are already committed in the app's
  `AnalyticsConfig` — public, RLS-gated, safe to reuse on the web). Sign in with
  `you@email.com` on the web → the *same* `auth.users` row the app signs into.
  - Web uses **magic-link** (click the email → session in the browser).
  - App uses the **6-digit OTP** (already built: `supabase_auth_service.dart`).
  - Same project, same users, no duplicate accounts.

- **One entitlement, brokered by RevenueCat.** The app *already* derives Plus
  from RevenueCat (`revenuecat_purchase_service.dart` → CustomerInfo → writes
  `Settings.paidTier`). If the **RevenueCat App User ID == the Supabase
  `user.id`**, then a purchase made **anywhere** (web or store) lands on the same
  RevenueCat customer, and the app sees it on next refresh. This is why the web
  doesn't need its own entitlement store.

- **Web checkout = RevenueCat Web Billing** (Stripe under the hood). It issues a
  hosted purchase URL per product; we pass the Supabase `user.id` as the app
  user id so the entitlement attaches to the right customer.

### Fallback (only if RC Web Billing can't be used)
Roll our own: Stripe Payment Links → a **Supabase Edge Function** webhook writes
an `entitlements(user_id, tier, source, current_period_end)` row; the app reads
that table on login and merges it with RevenueCat. More code, two systems to
reconcile — avoid unless RC Web Billing is unavailable.

## Products (must match the app's `StackProducts.*.storeId`)

| Product | id | Price |
|---|---|---|
| Plus monthly | `stack_plus_monthly` | $9.99 / mo |
| Plus annual  | `stack_plus_annual`  | $49.99 / yr (save 58%) |
| Lifetime     | `stack_lifetime`     | $124.99 once |

Entitlements: `plus` (← monthly + annual), `lifetime` (← lifetime).

## What's built on the website (this repo)

- **`/pricing/`** — dedicated pricing page: Free vs Plus, monthly/annual toggle,
  full comparison table, FAQ, honest pre-launch trust. The checkout surface.
- **`/account/`** — magic-link sign in + a signed-in panel that reads the user's
  entitlement and shows "manage / restore". Reuses the shared Supabase project.
- **`assets/js/rail-config.js`** — the one config block. Supabase URL/anon key
  are filled (public, shared with the app). Checkout URLs are `PASTE_…`
  placeholders → until set, the buy buttons fall back to "get notified at
  launch" (same graceful no-op pattern the app uses for unconfigured keys).
- **`assets/js/account.js`** — hand-rolled Supabase auth over `fetch` (no SDK,
  no external CDN — mirrors the app's SDK-free approach), session in
  `localStorage`, entitlement read via PostgREST.

Everything degrades gracefully: with checkout URLs blank the site is a complete,
honest pre-launch page; the moment the URLs are pasted, checkout goes live with
no other code change.

## What Sim sets up (dashboards — I can't create accounts or enter secret keys)

1. **Supabase → Authentication → URL Configuration**
   - Add `https://trackyourstack.app/account/` (and `http://127.0.0.1:8891/account/`
     for local testing) to **Redirect URLs**. Without this the magic link won't
     return to the site. *(This is the only thing gating web auth — everything
     else on the site is already wired to the shared project.)*
   - Email templates → make sure the **Magic Link** template is enabled (the web
     uses the link; the app's `{{ .Token }}` requirement is app-only).

2. **RevenueCat → Web Billing**
   - Enable Web Billing (connects your Stripe account — create Stripe first if
     you don't have one; a software subscription is standard, low-risk for
     Stripe). Create web products mapped to the `plus`/`lifetime` entitlements
     with the ids above.
   - Copy the three hosted purchase URLs → paste into `rail-config.js`
     (`checkout.plusMonthly / plusAnnual / lifetime`).

3. **App side (separate task in `dose_tracker`)** — the login-only pivot:
   - Require sign-in (flip the gated `SupabaseAuthService` on).
   - After auth, call `Purchases.logIn(supabaseUserId)` so the RevenueCat App
     User ID == the Supabase user id. This is the join that makes a web purchase
     visible in the app.
   - Refresh entitlement on resume so a just-completed web purchase appears.

Once 1–3 are done the loop is closed: buy on the web → open the app → signed in
with the same email → Plus is on.

## Notes / open items
- The app still hard-codes `kFreeCompoundLimit = 5` / `kFreeHistoryDays = 30`
  (`entitlement.dart`). The website now says **no compound caps** (Sim's locked
  call). The app constants need to be retired/raised to match — flagged for the
  app repo, not this one.
- Prices here are display strings; RevenueCat/Stripe is the source of truth for
  the actual charge. Keep the two in sync.
