/* Stack email list: Cloudflare Worker + KV + Resend. Double opt-in.
 *
 * POST /subscribe     {email, source, consent: true, website, turnstileToken?}
 *                     JSON or form-encoded. Stores a PENDING signup and emails
 *                     a confirmation link. The reply is the same whether or not
 *                     the address is already known.
 * GET  /confirm?t=    The link in the confirmation email. Moves PENDING to
 *                     CONFIRMED. Safe to open twice.
 * GET|POST /unsubscribe?t=
 *                     One click. POST is the RFC 8058 List-Unsubscribe-Post
 *                     path used by mail apps. Safe to open twice.
 * GET  /export        Bearer EXPORT_TOKEN. Confirmed subscribers only, with
 *                     counts by source.
 *
 * Bindings: WAITLIST (KV). Secrets: RESEND_API_KEY, HMAC_SECRET, EXPORT_TOKEN,
 * optional TURNSTILE_SECRET. Var: ADDRESS_LINE (postal address in the footer).
 * Setup steps: DEPLOY.md.
 *
 * KV keys (the address is hashed in keys; the full address lives only in the
 * value, and is never logged):
 *   pend:<h>  pending signup, 7 days      tok:<id>  confirm token -> h, 7 days
 *   sub:<h>   confirmed subscriber        gone:<h>  unsubscribed marker (hash only)
 *   rl:<ip>   rate-limit counter, 10 min
 * Older keys "email:<address>" from the 2026-09-07 waitlist have no consent
 * record. They are never mailed and never exported.
 */

export const ORIGINS = ["https://trackyourstack.app", "https://www.trackyourstack.app"];
export const SOURCES = ["launch", "doctor-list", "tools", "newsletter"];
export const CONSENT_VERSION = "2026-10-17";
export const CONSENT_TEXT =
  "Email me about Stack: the launch, new tools and occasional tips. Unsubscribe any time.";

const SITE = "https://trackyourstack.app";
const FROM = "Stack <hello@trackyourstack.app>";
const SUPPORT = "hello@trackyourstack.app";
const RESEND_URL = "https://api.resend.com/emails";
const TURNSTILE_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify";
const LOGO_URL = "https://nkxwtlfcezgehskzneqm.supabase.co/storage/v1/object/public/brand/stack-mark-96.png";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
const PENDING_TTL = 7 * 24 * 3600;
const RESEND_COOLDOWN_MS = 10 * 60 * 1000;
const RL_MAX = 5;
const RL_TTL = 600;

/* ---------------------------------------------------------------- helpers */

const enc = new TextEncoder();

function hex(buf) {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function sha256(s) {
  return hex(await crypto.subtle.digest("SHA-256", enc.encode(s)));
}

async function hmac(secret, msg) {
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  return hex(await crypto.subtle.sign("HMAC", key, enc.encode(msg)));
}

/** Compares two strings without bailing at the first differing character. */
export function safeEqual(a, b) {
  const x = enc.encode(String(a));
  const y = enc.encode(String(b));
  let diff = x.length ^ y.length;
  const n = Math.max(x.length, y.length);
  for (let i = 0; i < n; i++) diff |= (x[i] || 0) ^ (y[i] || 0);
  return diff === 0;
}

function corsHeaders(origin) {
  const allow = ORIGINS.includes(origin) ? origin : ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(body, status, origin) {
  return new Response(JSON.stringify(body), {
    status: status || 200,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin) },
  });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function baseUrl(request, env) {
  return (env.PUBLIC_BASE_URL || new URL(request.url).origin).replace(/\/$/, "");
}

/* ---------------------------------------------------------------- tokens */

// Confirm token: "<uuid>.<hmac(uuid)>". The signature is checked before any KV
// read, so random guesses never touch storage.
async function makeConfirmToken(env) {
  const id = crypto.randomUUID();
  return { id, token: id + "." + (await hmac(env.HMAC_SECRET, "confirm:" + id)) };
}

async function readConfirmToken(env, token) {
  const [id, sig] = String(token || "").split(".");
  if (!id || !sig) return null;
  return safeEqual(sig, await hmac(env.HMAC_SECRET, "confirm:" + id)) ? id : null;
}

// Unsubscribe token: "<h>.<hmac(h)>". Stateless, so it stays valid in every
// email ever sent to that address.
async function makeUnsubToken(env, h) {
  return h + "." + (await hmac(env.HMAC_SECRET, "unsub:" + h));
}

async function readUnsubToken(env, token) {
  const [h, sig] = String(token || "").split(".");
  if (!h || !sig) return null;
  return safeEqual(sig, await hmac(env.HMAC_SECRET, "unsub:" + h)) ? h : null;
}

/* ----------------------------------------------------------------- email */

export function confirmationEmail({ confirmUrl, unsubUrl, addressLine }) {
  const subject = "Confirm your email for Stack";
  const lines = [
    "Hi there,",
    "",
    "Someone, hopefully you, asked to get email from Stack: the launch, new tools and occasional tips. Confirm that it was you and you are on the list.",
    "",
    "Confirm: " + confirmUrl,
    "",
    "If it was not you, ignore this email. Nothing happens until you confirm, and the request expires in a week.",
    "",
    "Stack",
    "",
    "--",
    "You are getting this because this address was entered on trackyourstack.app.",
    "Stack - Cedar Hills Studio LLC",
  ];
  if (addressLine) lines.push(addressLine);
  lines.push(SUPPORT, "Unsubscribe: " + unsubUrl);
  const text = lines.join("\n");

  const font = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif";
  const html = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark"><title>${escapeHtml(subject)}</title>
<style>@media (prefers-color-scheme: dark){body,.bg{background:#121110!important}.ink{color:#F3F0E9!important}.ink2{color:#DAD5CA!important}.muted,.muted a{color:#A8A397!important}}</style></head>
<body class="bg" style="margin:0;padding:0;background:#FFFFFF;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" class="bg" style="background:#FFFFFF;"><tr>
<td align="center" style="padding:44px 24px 56px 24px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:520px;"><tr><td align="left" style="text-align:left;">
<img src="${LOGO_URL}" width="30" height="30" alt="Stack" style="display:block;width:30px;height:30px;border-radius:7px;margin:0 0 34px 0;">
<p class="ink2" style="margin:0 0 10px 0;font:400 15px/1.65 ${font};color:#2E2A25;">Hi there,</p>
<p class="ink" style="margin:0 0 22px 0;font:500 18px/1.5 ${font};letter-spacing:-0.012em;color:#1A1815;">Confirm your email and you are on the Stack list: the launch, new tools and occasional tips.</p>
<p style="margin:0 0 22px 0;"><a href="${escapeHtml(confirmUrl)}" style="display:inline-block;background:#175E58;color:#FFFFFF;font:600 15px/1 ${font};text-decoration:none;padding:14px 26px;border-radius:999px;">Confirm my email</a></p>
<p class="ink2" style="margin:0 0 14px 0;font:400 15px/1.65 ${font};color:#2E2A25;">If it was not you, ignore this email. Nothing happens until you confirm, and the request expires in a week.</p>
<p class="ink" style="margin:26px 0 0 0;font:600 15px/1.4 ${font};color:#1A1815;">Stack</p>
<div style="margin:40px 0 18px 0;border-top:1px solid #ECE8E0;height:0;line-height:0;font-size:0;">&nbsp;</div>
<p class="muted" style="margin:0;font:400 12px/1.7 ${font};color:#6B6862;">You are getting this because this address was entered on trackyourstack.app.<br>
Stack &middot; Cedar Hills Studio LLC<br>${addressLine ? escapeHtml(addressLine) + "<br>" : ""}
<a href="mailto:${SUPPORT}" style="color:#6B6862;">${SUPPORT}</a> &middot; <a href="${escapeHtml(unsubUrl)}" style="color:#6B6862;">Unsubscribe</a></p>
</td></tr></table></td></tr></table></body></html>`;
  return { subject, text, html };
}

async function sendConfirmation(env, to, confirmUrl, unsubUrl) {
  const { subject, text, html } = confirmationEmail({
    confirmUrl, unsubUrl, addressLine: env.ADDRESS_LINE || "",
  });
  const resp = await fetch(RESEND_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + env.RESEND_API_KEY },
    body: JSON.stringify({
      from: FROM,
      to: [to],
      subject,
      text,
      html,
      headers: {
        "List-Unsubscribe": "<" + unsubUrl + ">, <mailto:" + SUPPORT + "?subject=unsubscribe>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
      },
    }),
  });
  if (!resp.ok) throw new Error("resend " + resp.status);
}

/* ------------------------------------------------------------------ pages */

function page(title, message, status) {
  const body = `<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>${escapeHtml(title)} - Stack</title>
<style>body{margin:0;font:16px/1.6 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#FAF8F4;color:#1A1815}
main{max-width:480px;margin:0 auto;padding:72px 24px}h1{font-size:24px;letter-spacing:-.02em;margin:0 0 12px}
a{color:#175E58}@media (prefers-color-scheme:dark){body{background:#121110;color:#F3F0E9}a{color:#5FBFB3}}</style></head>
<body><main><h1>${escapeHtml(title)}</h1><p>${escapeHtml(message)}</p>
<p><a href="${SITE}/">Back to Stack</a></p></main></body></html>`;
  return new Response(body, {
    status: status || 200,
    headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store", "Referrer-Policy": "no-referrer" },
  });
}

/* --------------------------------------------------------------- handlers */

async function readBody(request) {
  const ct = request.headers.get("Content-Type") || "";
  try {
    if (ct.includes("application/json")) return (await request.json()) || {};
    const fd = await request.formData();
    return Object.fromEntries(fd.entries());
  } catch (e) {
    return {};
  }
}

async function verifyTurnstile(env, token, ip) {
  if (!token) return false;
  try {
    const form = new URLSearchParams({ secret: env.TURNSTILE_SECRET, response: String(token) });
    if (ip) form.set("remoteip", ip);
    const r = await fetch(TURNSTILE_URL, { method: "POST", body: form });
    return !!(await r.json()).success;
  } catch (e) {
    return false;
  }
}

async function handleSubscribe(request, env) {
  const origin = request.headers.get("Origin") || "";
  if (origin && !ORIGINS.includes(origin)) return json({ ok: false, error: "forbidden" }, 403, origin);

  // Per-IP rate limit (the IP is hashed before it is used as a key). Not atomic;
  // good enough to blunt a script, and the real brake on one inbox is the
  // per-address cooldown below.
  const ip = request.headers.get("CF-Connecting-IP") || "unknown";
  const rlKey = "rl:" + (await hmac(env.HMAC_SECRET, "ip:" + ip)).slice(0, 32);
  const hits = parseInt((await env.WAITLIST.get(rlKey)) || "0", 10);
  if (hits >= RL_MAX) return json({ ok: false, error: "slow down" }, 429, origin);
  await env.WAITLIST.put(rlKey, String(hits + 1), { expirationTtl: RL_TTL });

  const body = await readBody(request);

  // Honeypot: a hidden field real visitors never fill. Answer like a success so
  // the bot learns nothing, and store and send nothing.
  if (body.website) return json({ ok: true }, 200, origin);

  const consent = body.consent === true || body.consent === "true" || body.consent === "on";
  if (!consent) return json({ ok: false, error: "consent required" }, 400, origin);

  const email = String(body.email || "").trim();
  if (email.length > 254 || !EMAIL_RE.test(email)) {
    return json({ ok: false, error: "invalid email" }, 400, origin);
  }
  const source = SOURCES.includes(body.source) ? body.source : null;
  if (!source) return json({ ok: false, error: "invalid source" }, 400, origin);

  if (env.TURNSTILE_SECRET && !(await verifyTurnstile(env, body.turnstileToken, ip))) {
    return json({ ok: false, error: "verification failed" }, 400, origin);
  }

  const h = await sha256(email.toLowerCase());
  const reply = () => json({ ok: true }, 200, origin);

  // Already confirmed: say nothing different and send nothing.
  if (await env.WAITLIST.get("sub:" + h)) return reply();

  const now = Date.now();
  const prior = await env.WAITLIST.get("pend:" + h);
  const prev = prior ? JSON.parse(prior) : null;
  // Same address asked again within the cooldown: no second email, so the form
  // cannot be used to flood someone's inbox.
  if (prev && now - prev.sent < RESEND_COOLDOWN_MS) return reply();

  const { id, token } = await makeConfirmToken(env);
  const record = {
    email,
    source,
    ts: new Date(now).toISOString(),
    consentVersion: CONSENT_VERSION,
    id,
    sent: now,
  };
  await env.WAITLIST.put("pend:" + h, JSON.stringify(record), { expirationTtl: PENDING_TTL });
  await env.WAITLIST.put("tok:" + id, h, { expirationTtl: PENDING_TTL });
  if (prev && prev.id) await env.WAITLIST.delete("tok:" + prev.id);

  const base = baseUrl(request, env);
  const confirmUrl = base + "/confirm?t=" + encodeURIComponent(token);
  const unsubUrl = base + "/unsubscribe?t=" + encodeURIComponent(await makeUnsubToken(env, h));
  try {
    await sendConfirmation(env, email, confirmUrl, unsubUrl);
  } catch (e) {
    console.log("confirmation send failed: " + (e && e.message));
    return json({ ok: false, error: "could not send" }, 502, origin);
  }
  return reply();
}

async function handleConfirm(request, env) {
  const url = new URL(request.url);
  const id = await readConfirmToken(env, url.searchParams.get("t"));
  const expired = () =>
    page("This link has expired", "Confirmation links last a week. Sign up again on trackyourstack.app and we will send a new one.", 410);
  if (!id) return expired();

  const h = await env.WAITLIST.get("tok:" + id);
  if (!h) return expired();

  if (await env.WAITLIST.get("sub:" + h)) {
    await env.WAITLIST.delete("tok:" + id);
    return page("You are on the list", "This address was already confirmed. Nothing more to do.");
  }
  const raw = await env.WAITLIST.get("pend:" + h);
  if (!raw) return expired();
  const p = JSON.parse(raw);
  if (p.id !== id) return expired();

  await env.WAITLIST.put(
    "sub:" + h,
    JSON.stringify({
      email: p.email,
      source: p.source,
      confirmedAt: new Date().toISOString(),
      consentAt: p.ts,
      consentVersion: p.consentVersion,
    })
  );
  await env.WAITLIST.delete("gone:" + h);
  await env.WAITLIST.delete("pend:" + h);
  await env.WAITLIST.delete("tok:" + id);
  return page("You are on the list", "Thanks. We will email you when there is something worth saying. Every email has an unsubscribe link.");
}

async function handleUnsubscribe(request, env) {
  const url = new URL(request.url);
  const h = await readUnsubToken(env, url.searchParams.get("t"));
  if (!h) return page("That link is not valid", "Email " + SUPPORT + " and we will remove your address by hand.", 400);

  const pend = await env.WAITLIST.get("pend:" + h);
  if (pend) {
    const p = JSON.parse(pend);
    if (p.id) await env.WAITLIST.delete("tok:" + p.id);
    await env.WAITLIST.delete("pend:" + h);
  }
  await env.WAITLIST.delete("sub:" + h);
  // Keep the hash only, so we remember the opt-out without keeping the address.
  await env.WAITLIST.put("gone:" + h, JSON.stringify({ ts: new Date().toISOString() }));
  return page("You are unsubscribed", "We removed your address and will not email you again unless you sign up again.");
}

async function handleExport(request, env) {
  const auth = request.headers.get("Authorization") || "";
  if (!env.EXPORT_TOKEN || !safeEqual(auth, "Bearer " + env.EXPORT_TOKEN)) {
    return new Response("nope", { status: 401 });
  }
  const base = baseUrl(request, env);
  const subscribers = [];
  const counts = {};
  let cursor;
  do {
    const pg = await env.WAITLIST.list({ prefix: "sub:", cursor });
    for (const k of pg.keys) {
      const v = await env.WAITLIST.get(k.name);
      if (!v) continue;
      const s = JSON.parse(v);
      // Ready-made one-click unsubscribe link for the launch email.
      s.unsubscribeUrl = base + "/unsubscribe?t=" + encodeURIComponent(await makeUnsubToken(env, k.name.slice(4)));
      subscribers.push(s);
      counts[s.source] = (counts[s.source] || 0) + 1;
    }
    cursor = pg.list_complete ? undefined : pg.cursor;
  } while (cursor);
  return new Response(JSON.stringify({ total: subscribers.length, counts, subscribers }, null, 2), {
    headers: { "Content-Type": "application/json", "Cache-Control": "no-store" },
  });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }
    const path = new URL(request.url).pathname;
    const m = request.method;

    if (m === "POST" && path === "/subscribe") return handleSubscribe(request, env);
    if (m === "GET" && path === "/confirm") return handleConfirm(request, env);
    if ((m === "GET" || m === "POST") && path === "/unsubscribe") return handleUnsubscribe(request, env);
    if (m === "GET" && path === "/export") return handleExport(request, env);
    return new Response("Not found", { status: 404 });
  },
};
