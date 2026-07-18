/* Stack web rail — single config block. See WEB_RAIL.md.
 *
 * Supabase URL + anon key are the app's OWN committed values (public,
 * RLS-gated — safe to ship, identical to lib/core/analytics/analytics_config).
 * Sharing the project is the whole point: same email == same account as the app.
 *
 * checkout.* are the RevenueCat Web Billing (Stripe) purchase URLs. While they
 * are "PASTE_…" the buy buttons fall back to "get notified at launch" — the site
 * stays a complete, honest pre-launch page. Paste the URLs and checkout goes
 * live with no other change. */
window.STACK_RAIL = {
  supabaseUrl: "https://nkxwtlfcezgehskzneqm.supabase.co",
  supabaseAnonKey: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5reHd0bGZjZXpnZWhza3puZXFtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkxMTE4MzEsImV4cCI6MjA5NDY4NzgzMX0.c5BjasGU87S8VM93wOS4KtBGTP10MLVvH2JzjhUwXrk",

  // Where the magic link returns to. Must be in Supabase → Auth → Redirect URLs.
  accountRedirect: (location.origin || "https://trackyourstack.app") + "/account/",

  // RevenueCat Web Billing (Stripe) hosted purchase URLs — paste at launch.
  checkout: {
    plusMonthly: "PASTE_RC_WEB_URL_MONTHLY",
    plusAnnual: "PASTE_RC_WEB_URL_ANNUAL",
    lifetime: "PASTE_RC_WEB_URL_LIFETIME"
  },

  contactEmail: "hello@trackyourstack.app"
};

window.STACK_RAIL.checkoutReady = function (key) {
  var u = (window.STACK_RAIL.checkout || {})[key] || "";
  return u && u.indexOf("PASTE_") !== 0;
};
