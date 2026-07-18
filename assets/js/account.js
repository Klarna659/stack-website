/* Stack web account — magic-link auth against the SHARED Supabase project
 * (same users as the app). No SDK, no CDN — plain fetch, mirroring the app's
 * hand-rolled auth. See WEB_RAIL.md.
 *
 * Flow: enter email → POST /auth/v1/otp (create_user:true) with a redirect back
 * to /account/ → Supabase emails a magic link → click → returns with tokens in
 * the URL hash → we store the session and show the signed-in panel. */
(function () {
  "use strict";
  var CFG = window.STACK_RAIL || {};
  var SKEY = "stack_web_session_v1";
  var $ = function (id) { return document.getElementById(id); };

  if (!CFG.supabaseUrl || CFG.supabaseUrl.indexOf("PASTE_") === 0) return; // no-op until configured
  var BASE = CFG.supabaseUrl.replace(/\/$/, "");
  var HEAD = { "Content-Type": "application/json", "apikey": CFG.supabaseAnonKey };

  function saveSession(t) {
    try { localStorage.setItem(SKEY, JSON.stringify(t)); } catch (e) {}
  }
  function loadSession() {
    try { return JSON.parse(localStorage.getItem(SKEY) || "null"); } catch (e) { return null; }
  }
  function clearSession() { try { localStorage.removeItem(SKEY); } catch (e) {} }

  function fromTokens(o) {
    var expiresIn = parseInt(o.expires_in || "3600", 10);
    return {
      access_token: o.access_token,
      refresh_token: o.refresh_token,
      expires_at: Math.floor(Date.now() / 1000) + expiresIn,
      email: (o.user && o.user.email) || o.email || null,
      user_id: (o.user && o.user.id) || null
    };
  }

  var authErrorMsg = null;

  /* capture a failed magic-link return: #error=access_denied&error_code=otp_expired&…
     Strip it from the URL and stash a friendly message for render() to surface. */
  function captureError() {
    if (!location.hash || location.hash.indexOf("error") === -1) return;
    var p = {}; location.hash.replace(/^#/, "").split("&").forEach(function (kv) {
      var i = kv.indexOf("="); if (i > -1) p[decodeURIComponent(kv.slice(0, i))] = decodeURIComponent(kv.slice(i + 1).replace(/\+/g, " "));
    });
    if (!p.error && !p.error_code) return;
    history.replaceState(null, "", location.pathname + location.search);
    authErrorMsg = /expired|otp_expired/.test(p.error_code || p.error || "")
      ? "That link expired — request a new one below."
      : (p.error_description || "That sign-in link didn't work — try again below.");
  }

  /* capture a magic-link return: #access_token=…&refresh_token=… */
  function captureHash() {
    if (!location.hash || location.hash.indexOf("access_token") === -1) return null;
    var p = {}; location.hash.replace(/^#/, "").split("&").forEach(function (kv) {
      var i = kv.indexOf("="); if (i > -1) p[decodeURIComponent(kv.slice(0, i))] = decodeURIComponent(kv.slice(i + 1));
    });
    if (!p.access_token) return null;
    var sess = fromTokens(p);
    // strip the hash so tokens don't linger in the URL/history
    history.replaceState(null, "", location.pathname + location.search);
    return sess;
  }

  function decodeJwtEmail(access) {
    try {
      var payload = JSON.parse(atob(access.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      return { email: payload.email || null, user_id: payload.sub || null };
    } catch (e) { return { email: null, user_id: null }; }
  }

  function requestLink(email) {
    var url = BASE + "/auth/v1/otp?redirect_to=" + encodeURIComponent(CFG.accountRedirect || (location.origin + "/account/"));
    return fetch(url, {
      method: "POST", headers: HEAD,
      body: JSON.stringify({ email: email, create_user: true })
    });
  }

  function refresh(sess) {
    return fetch(BASE + "/auth/v1/token?grant_type=refresh_token", {
      method: "POST", headers: HEAD,
      body: JSON.stringify({ refresh_token: sess.refresh_token })
    }).then(function (r) {
      if (!r.ok) throw new Error("refresh failed");
      return r.json();
    }).then(function (j) { var s = fromTokens(j); saveSession(s); return s; });
  }

  /* returns a fresh session or null */
  function ensureSession() {
    var sess = loadSession();
    if (!sess || !sess.access_token) return Promise.resolve(null);
    if (sess.expires_at - Math.floor(Date.now() / 1000) > 60) return Promise.resolve(sess);
    if (!sess.refresh_token) return Promise.resolve(null);
    return refresh(sess).catch(function () { return sess; }); // offline-tolerant
  }

  /* read entitlement (best-effort). Until the entitlements table / RevenueCat
     web sync exists this simply returns 'free'; the panel copy handles it. */
  function readEntitlement(sess) {
    return fetch(BASE + "/rest/v1/entitlements?select=tier,current_period_end&limit=1", {
      headers: { "apikey": CFG.supabaseAnonKey, "Authorization": "Bearer " + sess.access_token }
    }).then(function (r) { return r.ok ? r.json() : []; })
      .then(function (rows) { return (rows && rows[0] && rows[0].tier) || "free"; })
      .catch(function () { return "free"; });
  }

  function signOut(sess) {
    if (sess && sess.access_token) {
      fetch(BASE + "/auth/v1/logout", { method: "POST", headers: { "apikey": CFG.supabaseAnonKey, "Authorization": "Bearer " + sess.access_token } }).catch(function () {});
    }
    clearSession();
  }

  // ---- UI wiring (only on /account/) --------------------------------------
  function render() {
    var signedOut = $("acct-signedout"), signedIn = $("acct-signedin");
    if (!signedOut || !signedIn) return;

    ensureSession().then(function (sess) {
      if (!sess) {
        signedOut.hidden = false; signedIn.hidden = true;
        if (authErrorMsg) { var m = $("acct-msg"); if (m) m.textContent = authErrorMsg; authErrorMsg = null; }
        return;
      }
      var who = sess.email ? sess : Object.assign({}, sess, decodeJwtEmail(sess.access_token));
      var emailEl = $("acct-email"); if (emailEl) emailEl.textContent = who.email || "your account";
      signedOut.hidden = true; signedIn.hidden = false;
      readEntitlement(sess).then(function (tier) {
        var badge = $("acct-tier"); if (!badge) return;
        var plus = tier && tier !== "free";
        badge.textContent = plus ? (tier === "lifetime" ? "Lifetime" : "Plus") : "Free";
        badge.classList.toggle("earned", !!plus);
        var hint = $("acct-plus-hint");
        if (hint) hint.hidden = !!plus;
      });
    });

    var form = $("acct-form");
    if (form) form.addEventListener("submit", function (e) {
      e.preventDefault();
      var input = $("acct-email-input"), msg = $("acct-msg");
      var email = (input && input.value || "").trim();
      if (!email || email.indexOf("@") === -1) { if (msg) msg.textContent = "Enter a valid email."; return; }
      if (msg) msg.textContent = "Sending your sign-in link…";
      requestLink(email).then(function (r) {
        if (msg) msg.textContent = r.ok
          ? "Check " + email + " — tap the link to sign in."
          : "Couldn't send that. Try again in a minute.";
      }).catch(function () { if (msg) msg.textContent = "Network hiccup — try again."; });
    });

    var out = $("acct-signout");
    if (out) out.addEventListener("click", function () {
      ensureSession().then(function (s) { signOut(s); render(); });
    });
  }

  // capture a magic-link return (success or error) before rendering
  captureError();
  var captured = captureHash();
  if (captured) saveSession(captured);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", render);
  else render();

  // expose for the pricing page's buy buttons
  window.StackAccount = { ensureSession: ensureSession, decodeJwtEmail: decodeJwtEmail };
})();
