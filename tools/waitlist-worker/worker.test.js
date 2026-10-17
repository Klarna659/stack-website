import { test, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import worker, { CONSENT_TEXT, CONSENT_VERSION } from "./index.js";

const ORIGIN = "https://trackyourstack.app";
const BASE = "https://stack-waitlist.test.workers.dev";

class FakeKV {
  constructor() { this.m = new Map(); this.now = 0; }
  async get(k) {
    const e = this.m.get(k);
    if (!e) return null;
    if (e.exp !== null && e.exp <= this.now) { this.m.delete(k); return null; }
    return e.v;
  }
  async put(k, v, opts = {}) {
    this.m.set(k, { v, exp: opts.expirationTtl ? this.now + opts.expirationTtl * 1000 : null });
  }
  async delete(k) { this.m.delete(k); }
  async list({ prefix = "" } = {}) {
    const keys = [...this.m.keys()].filter((k) => k.startsWith(prefix)).map((name) => ({ name }));
    return { keys, list_complete: true };
  }
}

let env, sent, realFetch, realNow, skew;

// Moves the KV clock and Date.now() together.
function advance(ms) {
  env.WAITLIST.now += ms;
  skew += ms;
}

beforeEach(() => {
  env = {
    WAITLIST: new FakeKV(),
    RESEND_API_KEY: "re_test",
    HMAC_SECRET: "test-secret",
    EXPORT_TOKEN: "export-token",
    ADDRESS_LINE: "Cedar Hills Studio LLC, 1 Test St, Testville, MO 63301",
  };
  sent = [];
  skew = 0;
  realNow = Date.now;
  Date.now = () => realNow() + skew;
  realFetch = globalThis.fetch;
  globalThis.fetch = async (url, init) => {
    if (String(url).startsWith("https://api.resend.com/")) {
      sent.push(JSON.parse(init.body));
      return new Response(JSON.stringify({ id: "x" }), { status: 200 });
    }
    if (String(url).startsWith("https://challenges.cloudflare.com/")) {
      const ok = new URLSearchParams(init.body).get("response") === "good-token";
      return new Response(JSON.stringify({ success: ok }), { status: 200 });
    }
    throw new Error("unexpected fetch " + url);
  };
});

afterEach(() => { globalThis.fetch = realFetch; Date.now = realNow; });

function subscribe(body, { ip = "1.1.1.1", origin = ORIGIN } = {}) {
  return worker.fetch(
    new Request(BASE + "/subscribe", {
      method: "POST",
      headers: { "Content-Type": "application/json", Origin: origin, "CF-Connecting-IP": ip },
      body: JSON.stringify(body),
    }),
    env
  );
}
const good = (over = {}) => ({ email: "Ann@Example.com", source: "launch", consent: true, website: "", ...over });
const links = (mail) => ({
  confirm: mail.text.match(/Confirm: (\S+)/)[1],
  unsub: mail.text.match(/Unsubscribe: (\S+)/)[1],
});
const get = (url, init) => worker.fetch(new Request(url, init), env);

test("happy path: pending record, one confirmation email, same-shaped reply", async () => {
  const r = await subscribe(good());
  assert.equal(r.status, 200);
  assert.deepEqual(await r.json(), { ok: true });
  assert.equal(r.headers.get("Access-Control-Allow-Origin"), ORIGIN);
  assert.equal(sent.length, 1);
  assert.deepEqual(sent[0].to, ["Ann@Example.com"]);
  assert.equal(sent[0].from, "Stack <hello@trackyourstack.app>");
  const keys = [...env.WAITLIST.m.keys()];
  assert.ok(keys.some((k) => k.startsWith("pend:")));
  assert.ok(!keys.some((k) => k.startsWith("sub:")), "not confirmed yet");
  assert.ok(!keys.some((k) => k.includes("ann@example.com")), "address is not in any key");
});

test("missing consent is rejected, nothing stored or sent", async () => {
  for (const consent of [undefined, false, "no"]) {
    const r = await subscribe(good({ consent }), { ip: "2.2.2.2" });
    assert.equal(r.status, 400);
    assert.equal((await r.json()).error, "consent required");
  }
  assert.equal(sent.length, 0);
  assert.ok(![...env.WAITLIST.m.keys()].some((k) => k.startsWith("pend:")));
});

test("honeypot filled: looks like success, stores and sends nothing", async () => {
  const r = await subscribe(good({ website: "http://spam.example" }));
  assert.equal(r.status, 200);
  assert.deepEqual(await r.json(), { ok: true });
  assert.equal(sent.length, 0);
  assert.ok(![...env.WAITLIST.m.keys()].some((k) => k.startsWith("pend:")));
});

test("bad email and bad source are rejected", async () => {
  for (const email of ["", "nope", "a@b", "a b@c.com", "x".repeat(260) + "@e.com"]) {
    const r = await subscribe(good({ email }), { ip: "3.3.3." + (email.length % 200) });
    assert.equal(r.status, 400, "email: " + email.slice(0, 20));
  }
  const r = await subscribe(good({ source: "hacker-news" }), { ip: "4.4.4.4" });
  assert.equal(r.status, 400);
  assert.equal(sent.length, 0);
});

test("every allowed source is accepted", async () => {
  let i = 0;
  for (const source of ["launch", "doctor-list", "tools", "newsletter"]) {
    const r = await subscribe(good({ email: `u${i++}@example.com`, source }), { ip: "5.5.5." + i });
    assert.equal(r.status, 200, source);
  }
  assert.equal(sent.length, 4);
});

test("foreign Origin is refused", async () => {
  const r = await subscribe(good(), { origin: "https://evil.example" });
  assert.equal(r.status, 403);
  assert.equal(sent.length, 0);
});

test("per-IP rate limit: sixth request in the window is 429, window expires", async () => {
  for (let i = 0; i < 5; i++) {
    const r = await subscribe(good({ email: `r${i}@example.com` }), { ip: "9.9.9.9" });
    assert.equal(r.status, 200);
  }
  const blocked = await subscribe(good({ email: "r9@example.com" }), { ip: "9.9.9.9" });
  assert.equal(blocked.status, 429);
  const other = await subscribe(good({ email: "r8@example.com" }), { ip: "8.8.8.8" });
  assert.equal(other.status, 200);
  advance(601 * 1000);
  const later = await subscribe(good({ email: "r7@example.com" }), { ip: "9.9.9.9" });
  assert.equal(later.status, 200);
});

test("confirmation email: confirm link, unsubscribe link, List-Unsubscribe headers, address line", async () => {
  await subscribe(good());
  const mail = sent[0];
  const { confirm, unsub } = links(mail);
  assert.match(confirm, new RegExp("^" + BASE + "/confirm\\?t="));
  assert.match(unsub, new RegExp("^" + BASE + "/unsubscribe\\?t="));
  assert.ok(mail.html.includes(confirm.replace(/&/g, "&amp;")));
  assert.equal(mail.headers["List-Unsubscribe-Post"], "List-Unsubscribe=One-Click");
  assert.ok(mail.headers["List-Unsubscribe"].includes("<" + unsub + ">"));
  assert.ok(mail.headers["List-Unsubscribe"].includes("mailto:hello@trackyourstack.app"));
  assert.ok(mail.text.includes(env.ADDRESS_LINE));
  assert.ok(mail.html.includes(env.ADDRESS_LINE));
  assert.equal((mail.html.match(/<a [^>]*background:#175E58/g) || []).length, 1, "exactly one button");
  assert.ok(!/\bAI\b/.test(mail.text + mail.html), "no AI wording");
  assert.ok(!/[\u{1F300}-\u{1FAFF}☀-➿—]/u.test(mail.text), "no emoji or em dash");
});

test("confirm moves to CONFIRMED with source, timestamps and consent version; second click is harmless", async () => {
  await subscribe(good({ source: "tools" }));
  const { confirm } = links(sent[0]);
  const r1 = await get(confirm);
  assert.equal(r1.status, 200);
  assert.match(await r1.text(), /You are on the list/);
  const subKey = [...env.WAITLIST.m.keys()].find((k) => k.startsWith("sub:"));
  const rec = JSON.parse(await env.WAITLIST.get(subKey));
  assert.equal(rec.email, "Ann@Example.com");
  assert.equal(rec.source, "tools");
  assert.equal(rec.consentVersion, CONSENT_VERSION);
  assert.ok(rec.confirmedAt && rec.consentAt);
  assert.ok(![...env.WAITLIST.m.keys()].some((k) => k.startsWith("pend:")));

  const r2 = await get(confirm);
  assert.match(await r2.text(), /already confirmed|expired/);
  assert.equal([...env.WAITLIST.m.keys()].filter((k) => k.startsWith("sub:")).length, 1);
});

test("tampered or garbage confirm tokens do nothing", async () => {
  await subscribe(good());
  const { confirm } = links(sent[0]);
  for (const bad of [confirm.slice(0, -3) + "abc", BASE + "/confirm?t=garbage", BASE + "/confirm"]) {
    const r = await get(bad);
    assert.equal(r.status, 410);
  }
  assert.ok(![...env.WAITLIST.m.keys()].some((k) => k.startsWith("sub:")));
});

test("confirm link expires after seven days", async () => {
  await subscribe(good());
  const { confirm } = links(sent[0]);
  advance(8 * 24 * 3600 * 1000);
  const r = await get(confirm);
  assert.equal(r.status, 410);
});

test("same reply for an already-confirmed address, and no second email", async () => {
  await subscribe(good());
  await get(links(sent[0]).confirm);
  const again = await subscribe(good(), { ip: "6.6.6.6" });
  assert.equal(again.status, 200);
  assert.deepEqual(await again.json(), { ok: true });
  assert.equal(sent.length, 1);
});

test("repeat signup of a pending address inside ten minutes does not send again; later it does", async () => {
  await subscribe(good());
  const r = await subscribe(good(), { ip: "7.7.7.7" });
  assert.equal(r.status, 200);
  assert.equal(sent.length, 1);
  advance(11 * 60 * 1000);
  await subscribe(good(), { ip: "7.7.7.8" });
  assert.equal(sent.length, 2);
  // the first link is dead, the newest works
  assert.equal((await get(links(sent[0]).confirm)).status, 410);
  assert.equal((await get(links(sent[1]).confirm)).status, 200);
});

test("unsubscribe (GET and one-click POST) removes the subscriber and is idempotent", async () => {
  await subscribe(good());
  await get(links(sent[0]).confirm);
  const { unsub } = links(sent[0]);
  const r1 = await get(unsub);
  assert.equal(r1.status, 200);
  assert.match(await r1.text(), /unsubscribed/);
  assert.ok(![...env.WAITLIST.m.keys()].some((k) => k.startsWith("sub:")));
  const gone = [...env.WAITLIST.m.keys()].find((k) => k.startsWith("gone:"));
  assert.ok(!(await env.WAITLIST.get(gone)).includes("example.com"), "marker holds no address");

  const r2 = await get(unsub, { method: "POST", body: "List-Unsubscribe=One-Click", headers: { "Content-Type": "application/x-www-form-urlencoded" } });
  assert.equal(r2.status, 200);
  const bad = await get(BASE + "/unsubscribe?t=abc.def");
  assert.equal(bad.status, 400);
});

test("unsubscribing a pending address cancels the pending signup", async () => {
  await subscribe(good());
  const { confirm, unsub } = links(sent[0]);
  await get(unsub);
  assert.equal((await get(confirm)).status, 410);
});

test("export: confirmed only, counts by source, token required", async () => {
  await subscribe(good({ email: "a@example.com", source: "launch" }), { ip: "1.0.0.1" });
  await subscribe(good({ email: "b@example.com", source: "launch" }), { ip: "1.0.0.2" });
  await subscribe(good({ email: "c@example.com", source: "tools" }), { ip: "1.0.0.3" });
  await subscribe(good({ email: "pending@example.com", source: "newsletter" }), { ip: "1.0.0.4" });
  await get(links(sent[0]).confirm);
  await get(links(sent[1]).confirm);
  await get(links(sent[2]).confirm);
  await env.WAITLIST.put("email:legacy@example.com", JSON.stringify({ ts: "2026-09-07" }));

  assert.equal((await get(BASE + "/export")).status, 401);
  assert.equal((await get(BASE + "/export", { headers: { Authorization: "Bearer wrong" } })).status, 401);
  const r = await get(BASE + "/export", { headers: { Authorization: "Bearer export-token" } });
  assert.equal(r.status, 200);
  const out = await r.json();
  assert.equal(out.total, 3);
  assert.deepEqual(out.counts, { launch: 2, tools: 1 });
  const emails = out.subscribers.map((s) => s.email).sort();
  assert.deepEqual(emails, ["a@example.com", "b@example.com", "c@example.com"]);
  // the exported unsubscribe link works
  const a = out.subscribers.find((s) => s.email === "a@example.com");
  assert.equal((await get(a.unsubscribeUrl)).status, 200);
  const after = await (await get(BASE + "/export", { headers: { Authorization: "Bearer export-token" } })).json();
  assert.equal(after.total, 2);
});

test("export stays closed when EXPORT_TOKEN is not configured", async () => {
  delete env.EXPORT_TOKEN;
  const r = await get(BASE + "/export", { headers: { Authorization: "Bearer undefined" } });
  assert.equal(r.status, 401);
});

test("Turnstile: enforced only when TURNSTILE_SECRET is set", async () => {
  env.TURNSTILE_SECRET = "ts-secret";
  assert.equal((await subscribe(good(), { ip: "2.0.0.1" })).status, 400);
  assert.equal((await subscribe(good({ turnstileToken: "bad" }), { ip: "2.0.0.2" })).status, 400);
  assert.equal((await subscribe(good({ turnstileToken: "good-token" }), { ip: "2.0.0.3" })).status, 200);
  assert.equal(sent.length, 1);
});

test("a Resend failure is reported and nothing is logged with the address", async () => {
  const logs = [];
  const origLog = console.log;
  console.log = (...a) => logs.push(a.join(" "));
  globalThis.fetch = async () => new Response("{}", { status: 500 });
  try {
    const r = await subscribe(good());
    assert.equal(r.status, 502);
  } finally {
    console.log = origLog;
  }
  assert.ok(logs.length > 0 && !logs.join("\n").toLowerCase().includes("example.com"));
});

test("CORS preflight allows only the site origins", async () => {
  const ok = await worker.fetch(new Request(BASE + "/subscribe", { method: "OPTIONS", headers: { Origin: "https://www.trackyourstack.app" } }), env);
  assert.equal(ok.status, 204);
  assert.equal(ok.headers.get("Access-Control-Allow-Origin"), "https://www.trackyourstack.app");
  const no = await worker.fetch(new Request(BASE + "/subscribe", { method: "OPTIONS", headers: { Origin: "https://evil.example" } }), env);
  assert.equal(no.headers.get("Access-Control-Allow-Origin"), ORIGIN);
});

test("old POST / endpoint is gone", async () => {
  const r = await worker.fetch(new Request(BASE + "/", { method: "POST", body: "{}" }), env);
  assert.equal(r.status, 404);
});

test("the homepage form shows exactly the consent text the Worker records", () => {
  const html = readFileSync(new URL("../../index.html", import.meta.url), "utf8");
  assert.ok(html.includes(CONSENT_TEXT), "index.html consent line differs from CONSENT_TEXT");
});
