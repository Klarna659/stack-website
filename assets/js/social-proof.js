/* Stack — social proof, without ever lying about it.
 *
 * THE PROBLEM THIS SOLVES
 * -----------------------
 * Every landing page that converts in this category leads with a number:
 * Shotsy's 4.8 stars, MyFitnessPal's 5.5 million reviews, Ro's 3,000,000
 * members. Stack has not launched and has none of that, and the obvious
 * shortcut — friends and family five-starring it on day one — is the one
 * thing that can actually take the listing down. Play does not need to prove
 * anyone is a relative; a burst of new accounts rating five stars minutes
 * after install, some never having opened the app, is itself the signal. The
 * reviews get removed silently and the rating goes with them, in launch week,
 * with no hearing.
 *
 * THE WORKAROUND
 * --------------
 * Make the page tell the truth *and* upgrade itself, so there is never a
 * moment where lying is tempting. Three states, one config block:
 *
 *   1. NO RATING, NO QUOTES  → "New here." The page says so plainly and shows
 *      the things it CAN prove: 112 cited compound pages you can read now, a
 *      calculator that runs in the browser, an export that is not paywalled.
 *      Verifiable artifacts instead of testimonials. This state is written
 *      into the HTML, so it survives JS being off and it is what ships today.
 *
 *   2. QUOTES, NO RATING     → a beta-feedback wall, labelled as beta feedback
 *      rather than dressed up as store reviews. Legitimate on day one: these
 *      are testers you have permission to quote.
 *
 *   3. RATING + QUOTES       → the real thing, with the score and count coming
 *      from the live listing rather than being typed in by hand.
 *
 * Moving between states is editing `window.STACK_PROOF` below. Nothing else
 * changes, and at no point does the page claim something that is not true.
 *
 * WHY THE HONEST STATE IS NOT A CONSOLATION PRIZE
 * -----------------------------------------------
 * "We launched three weeks ago and have no reviews yet — here is what you can
 * check instead" is a position no competitor can copy and no generated page
 * would ever take. It reads as confidence. The alternative reads as a risk to
 * the listing.
 *
 * FILLING IT LEGITIMATELY, FAST
 * -----------------------------
 * Play's In-App Review API, fired once, on a moment where the app has visibly
 * done something for the person. For Stack that moment is specific and nobody
 * else has it: the first time the refill projection warns them early enough
 * that they order in time. Not first open, not launch day, not twice.
 */
(function () {
  "use strict";

  /* ── THE ONLY BLOCK TO EDIT ────────────────────────────────────────────
     rating/count stay null until the Play listing actually has them. Do not
     type a number in here that the store does not show: it is the first thing
     a sceptical visitor checks, and being caught out costs more than the
     number was ever worth. */
  var CFG = window.STACK_PROOF || {
    play: {
      rating: null,        // e.g. 4.7  — read off the live listing
      count: null,         // e.g. 128
      url: ""              // the listing URL, once it exists
    },
    /* `source` is load-bearing and must be honest:
         "beta" → rendered and labelled as beta feedback
         "play" → rendered as a store review
       Only publish a quote you have written permission to use. */
    quotes: []             // {text, name, context, source, stars}
  };

  var host = document.getElementById("proof-body");
  var head = document.getElementById("proof-h");
  var rating = document.getElementById("proof-rating");
  if (!host) return;

  var play = CFG.play || {};
  var quotes = (CFG.quotes || []).filter(function (q) { return q && q.text; });
  var hasRating = typeof play.rating === "number" && play.rating > 0 &&
                  typeof play.count === "number" && play.count > 0;

  /* State 1 is already in the HTML. If there is nothing to upgrade to, leave
     it exactly as the server sent it — no flash, no work, no JS dependency. */
  if (!hasRating && !quotes.length) return;

  function esc(t) {
    return String(t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function stars(n) {
    var full = Math.round(n || 5), out = "";
    for (var i = 0; i < 5; i++) {
      out += '<svg viewBox="0 0 24 24"' + (i >= full ? ' class="off"' : "") +
             '><use href="#star"/></svg>';
    }
    return '<span class="stars" role="img" aria-label="' +
           esc((n || 5) + " out of 5") + '">' + out + "</span>";
  }

  function initial(name) {
    var n = (name || "").trim();
    return esc(n ? n.charAt(0).toUpperCase() : "•");
  }

  var isBeta = !hasRating;
  var html = "";

  if (hasRating) {
    html += '<div class="score">' +
      '<div class="big">' + esc(play.rating.toFixed(1)) + "</div>" +
      '<div class="meta">' + stars(play.rating) +
      "<div>Google Play &middot; " + esc(play.count.toLocaleString()) + " ratings" +
      (play.url ? '<br><a href="' + esc(play.url) + '" rel="noopener">See them on the listing</a>'
                : "") +
      "</div></div></div>";
  } else {
    html += '<p class="proof-lead">These are testers who have been running Stack for a few ' +
            "weeks, quoted with their permission. They are not store reviews, and we will not " +
            "dress them up as any.</p>";
  }

  if (quotes.length) {
    html += '<div class="revs">';
    quotes.slice(0, 6).forEach(function (q, i) {
      var beta = (q.source || "beta") !== "play";
      html += '<article class="rev an in" style="--d:' + i + '">' +
        stars(q.stars) +
        "<p>&ldquo;" + esc(q.text) + "&rdquo;</p>" +
        '<div class="who"><span class="av" aria-hidden="true">' + initial(q.name) + "</span>" +
        '<span><span class="nm">' + esc(q.name || "Anonymous") + "</span>" +
        '<span class="cx">' + esc(q.context || (beta ? "Beta tester" : "Google Play review")) +
        "</span></span></div></article>";
    });
    html += "</div>";
  }

  host.innerHTML = html;
  if (head) head.textContent = isBeta ? "What testers say." : "What people say.";

  /* The hero line only earns stars once the store shows them. */
  if (rating && hasRating) {
    rating.innerHTML = stars(play.rating) +
      "<span><b>" + esc(play.rating.toFixed(1)) + "</b> on Google Play</span>" +
      '<span class="sep">&middot;</span><span>Free, no compound limit</span>';
  }
})();
