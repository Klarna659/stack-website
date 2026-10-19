/* Google Play link for every "Get Stack" button on the site.

   One constant flips them all: replace TODO_PLAY_URL below with the store
   listing URL, e.g.
     https://play.google.com/store/apps/details?id=app.trackyourstack
   Until then buttons marked data-play keep their honest fallback ("Coming soon
   to Google Play" on /go/ pages, the old link elsewhere). Nothing here sends
   data anywhere: it only builds a link from the page's own address.

   Markup contract (see GO_LINKS.md):
     <a data-play="injections" ...>   a button for the custom listing "injections"
     <a data-play ...>                the default listing (no listing parameter)
     [data-play-on]                   shown only once the URL is set
     [data-play-off]                  shown only while it is not
   When the URL is set the link gets &listing=<door> and the page's utm_*
   parameters go to Google Play as its "referrer" parameter. */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root && root.document) {
    var run = function () { api.init(root.document, root.location.search); };
    if (root.document.readyState === "loading") root.document.addEventListener("DOMContentLoaded", run);
    else run();
  }
})(typeof window !== "undefined" ? window : null, function () {
  "use strict";

  /* TODO_PLAY_URL: replace with the Google Play listing URL. */
  var PLAY_URL = "TODO_PLAY_URL";

  var UTM_KEYS = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"];

  /* A real, https URL only. The placeholder (and anything odd) counts as unset. */
  function isConfigured(base) {
    return typeof base === "string" && /^https:\/\/[^\s]+$/.test(base) && base.indexOf("TODO") === -1;
  }

  /* Pull the utm_* values out of a query string, in a fixed order. */
  function utmFrom(search) {
    var out = [];
    var params = new URLSearchParams(search || "");
    UTM_KEYS.forEach(function (k) {
      var v = params.get(k);
      if (v) out.push(encodeURIComponent(k) + "=" + encodeURIComponent(v));
    });
    return out.join("&");
  }

  /* Build the Play link, or "" while the base is unset.
     door: custom listing name ("injections"), "" for the default listing. */
  function buildPlayUrl(base, door, search) {
    if (!isConfigured(base)) return "";
    var url = base;
    var sep = function () { return url.indexOf("?") === -1 ? "?" : "&"; };
    if (door && /^[a-z0-9-]+$/.test(door)) url += sep() + "listing=" + door;
    var referrer = utmFrom(search);
    if (referrer) url += sep() + "referrer=" + encodeURIComponent(referrer);
    return url;
  }

  function setHidden(list, hidden) {
    for (var i = 0; i < list.length; i++) {
      if (hidden) list[i].setAttribute("hidden", "");
      else list[i].removeAttribute("hidden");
    }
  }

  /* Apply the state to a document-like object (a real one, or a test stub). */
  function init(doc, search, base) {
    var configured = isConfigured(base === undefined ? PLAY_URL : base);
    var useBase = base === undefined ? PLAY_URL : base;
    var buttons = doc.querySelectorAll("[data-play]");
    for (var i = 0; i < buttons.length; i++) {
      var el = buttons[i];
      if (configured) {
        el.setAttribute("href", buildPlayUrl(useBase, el.getAttribute("data-play") || "", search));
        el.setAttribute("rel", "noopener");
        el.removeAttribute("aria-disabled");
        if (el.getAttribute("role") === "link") el.removeAttribute("role");
        if (el.classList) el.classList.remove("is-soon");
      } else if (el.getAttribute("href") === null) {
        /* No fallback link: say so, and keep it out of the tab order. */
        el.setAttribute("aria-disabled", "true");
        el.setAttribute("role", "link");
        if (el.classList) el.classList.add("is-soon");
      }
    }
    setHidden(doc.querySelectorAll("[data-play-on]"), !configured);
    setHidden(doc.querySelectorAll("[data-play-off]"), configured);
    return configured;
  }

  return { PLAY_URL: PLAY_URL, isConfigured: isConfigured, utmFrom: utmFrom, buildPlayUrl: buildPlayUrl, init: init };
});
