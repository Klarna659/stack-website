/* Email capture. Markup contract:

     <form class="capture" data-capture data-source="launch" novalidate> ... </form>

   data-source is one of: launch, doctor-list, tools, newsletter (the Worker
   rejects anything else). The form needs an email input, an unticked consent
   checkbox, a hidden "website" honeypot, and a [data-capture-msg] status
   element. An optional Cloudflare Turnstile widget adds its own
   "cf-turnstile-response" field, which is forwarded when present.
   Posts to tools/waitlist-worker (double opt-in): the person gets a
   confirmation email and is on the list only after clicking it. */
(function () {
  "use strict";

  /* TODO_WORKER_URL: replace with the deployed Worker URL, e.g.
     https://stack-waitlist.<account>.workers.dev  (see tools/waitlist-worker/DEPLOY.md).
     While it still contains TODO the form says sign-up is not open yet and
     points to the email address instead of pretending to work. */
  var WORKER_URL = "TODO_WORKER_URL";
  var EMAIL = "hello@trackyourstack.app";

  function say(msg, text, state) {
    if (!msg) return;
    msg.textContent = text;
    msg.setAttribute("data-state", state || "");
  }

  document.querySelectorAll("form[data-capture]").forEach(function (form) {
    var msg = form.querySelector("[data-capture-msg]");
    var button = form.querySelector('button[type="submit"]');
    var emailInput = form.querySelector('input[name="email"]');
    var consent = form.querySelector('input[name="consent"]');
    var honeypot = form.querySelector('input[name="website"]');
    var busy = false;

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (busy) return;

      var email = (emailInput && emailInput.value || "").trim();
      if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
        say(msg, "Enter a valid email address.", "error");
        if (emailInput) emailInput.focus();
        return;
      }
      if (!consent || !consent.checked) {
        say(msg, "Tick the box so we know you want these emails.", "error");
        if (consent) consent.focus();
        return;
      }
      if (WORKER_URL.indexOf("TODO") !== -1) {
        say(msg, "Sign-up is not open yet. Email " + EMAIL + " and we will add you by hand.", "error");
        return;
      }

      var ts = form.querySelector('[name="cf-turnstile-response"]');
      busy = true;
      if (button) button.disabled = true;
      say(msg, "Sending…", "");

      fetch(WORKER_URL.replace(/\/$/, "") + "/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({
          email: email,
          source: form.getAttribute("data-source") || "",
          consent: true,
          website: honeypot ? honeypot.value : "",
          turnstileToken: ts ? ts.value : undefined
        })
      }).then(function (r) {
        if (r.ok) {
          say(msg, "Check your inbox to confirm.", "ok");
          if (emailInput) emailInput.value = "";
          if (consent) consent.checked = false;
        } else if (r.status === 429) {
          say(msg, "Too many tries. Wait a few minutes and try again.", "error");
        } else {
          say(msg, "That did not go through. Email " + EMAIL + " instead.", "error");
        }
      }).catch(function () {
        say(msg, "Could not reach the server. Email " + EMAIL + " instead.", "error");
      }).then(function () {
        busy = false;
        if (button) button.disabled = false;
      });
    });
  });
})();
