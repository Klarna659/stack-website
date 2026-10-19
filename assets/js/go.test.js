/* Tests for assets/js/go.js: node --test */
const test = require("node:test");
const assert = require("node:assert");
const go = require("./go.js");

const PLAY = "https://play.google.com/store/apps/details?id=app.trackyourstack";

/* Minimal element and document stubs: just what go.js touches. */
function el(attrs) {
  const a = Object.assign({}, attrs);
  const classes = new Set((a.class || "").split(" ").filter(Boolean));
  delete a.class;
  return {
    getAttribute: (n) => (n in a ? a[n] : null),
    setAttribute: (n, v) => { a[n] = String(v); },
    removeAttribute: (n) => { delete a[n]; },
    classList: { add: (c) => classes.add(c), remove: (c) => classes.delete(c), contains: (c) => classes.has(c) },
    attrs: a,
    classes,
  };
}
function doc(map) {
  return { querySelectorAll: (sel) => map[sel] || [] };
}

test("the placeholder and odd values count as unset", () => {
  assert.strictEqual(go.PLAY_URL, "TODO_PLAY_URL");
  assert.strictEqual(go.isConfigured("TODO_PLAY_URL"), false);
  assert.strictEqual(go.isConfigured(""), false);
  assert.strictEqual(go.isConfigured("javascript:alert(1)"), false);
  assert.strictEqual(go.isConfigured("http://play.google.com/x"), false);
  assert.strictEqual(go.isConfigured(PLAY), true);
});

test("unset: no link is built and the button turns into the disabled state", () => {
  assert.strictEqual(go.buildPlayUrl("TODO_PLAY_URL", "injections", "?utm_source=tiktok"), "");
  const btn = el({ "data-play": "injections" });
  const on = el({ hidden: "" });
  const off = el({});
  const configured = go.init(doc({ "[data-play]": [btn], "[data-play-on]": [on], "[data-play-off]": [off] }), "");
  assert.strictEqual(configured, false);
  assert.strictEqual(btn.attrs.href, undefined);
  assert.strictEqual(btn.attrs["aria-disabled"], "true");
  assert.ok(btn.classes.has("is-soon"));
  assert.strictEqual(on.attrs.hidden, "");
  assert.strictEqual(off.attrs.hidden, undefined);
});

test("unset: a button that already has a fallback href keeps it", () => {
  const nav = el({ "data-play": "", href: "pricing/" });
  go.init(doc({ "[data-play]": [nav] }), "?utm_source=x");
  assert.strictEqual(nav.attrs.href, "pricing/");
  assert.strictEqual(nav.attrs["aria-disabled"], undefined);
});

test("set: the link carries the listing and the utm parameters as a referrer", () => {
  const url = go.buildPlayUrl(PLAY, "injections", "?utm_source=tiktok&utm_medium=bio&utm_campaign=launch&utm_content=hook12");
  const u = new URL(url);
  assert.strictEqual(u.searchParams.get("id"), "app.trackyourstack");
  assert.strictEqual(u.searchParams.get("listing"), "injections");
  assert.strictEqual(
    u.searchParams.get("referrer"),
    "utm_source=tiktok&utm_medium=bio&utm_campaign=launch&utm_content=hook12"
  );
  assert.ok(url.includes("&referrer=utm_source%3Dtiktok%26utm_medium%3Dbio%26utm_campaign%3Dlaunch%26utm_content%3Dhook12"));
});

test("set: no utm parameters means no referrer; no door means no listing", () => {
  assert.strictEqual(go.buildPlayUrl(PLAY, "labs", ""), PLAY + "&listing=labs");
  assert.strictEqual(go.buildPlayUrl(PLAY, "", ""), PLAY);
  assert.strictEqual(go.buildPlayUrl(PLAY, "", "?foo=bar&gclid=1"), PLAY);
});

test("set: only utm values pass through, encoded, and a bad door name is ignored", () => {
  const url = go.buildPlayUrl(PLAY, "x&y=1", "?utm_source=a b&utm_term=c%26d&other=1");
  assert.ok(!url.includes("listing"));
  const ref = new URL(url).searchParams.get("referrer");
  assert.strictEqual(ref, "utm_source=a%20b&utm_term=c%26d");
  assert.ok(!url.includes("other"));
});

test("a base without a query string starts one", () => {
  assert.strictEqual(go.buildPlayUrl("https://example.com/app", "routine", ""), "https://example.com/app?listing=routine");
});

test("set: init flips the buttons, the labels and the capture form", () => {
  const btn = el({ "data-play": "routine", role: "link", "aria-disabled": "true", class: "is-soon" });
  const nav = el({ "data-play": "", href: "pricing/" });
  const on = el({ hidden: "" });
  const off = el({});
  const configured = go.init(
    doc({ "[data-play]": [btn, nav], "[data-play-on]": [on], "[data-play-off]": [off] }),
    "?utm_source=tiktok&utm_content=hook12",
    PLAY
  );
  assert.strictEqual(configured, true);
  assert.ok(btn.attrs.href.startsWith(PLAY + "&listing=routine&referrer="));
  assert.strictEqual(btn.attrs["aria-disabled"], undefined);
  assert.strictEqual(btn.attrs.role, undefined);
  assert.strictEqual(btn.classes.has("is-soon"), false);
  assert.strictEqual(nav.attrs.href, PLAY + "&referrer=utm_source%3Dtiktok%26utm_content%3Dhook12");
  assert.strictEqual(on.attrs.hidden, undefined);
  assert.strictEqual(off.attrs.hidden, "");
});
