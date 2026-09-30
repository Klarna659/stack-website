/* Stack waitlist — Cloudflare Worker + KV.
 *
 * POST /            {email} as JSON or form-encoded → stored in KV,
 *                   deduped by address, light per-IP rate limit.
 * GET  /export      Bearer EXPORT_TOKEN → JSON array of signups.
 *
 * Deployed with wrangler from tools/waitlist-worker; the site's
 * WAITLIST_ENDPOINT points here. CORS allows the production origins and
 * localhost for the dev server.
 */

const ORIGINS = [
  "https://trackyourstack.app",
  "https://www.trackyourstack.app",
  "http://localhost:4321",
  "http://10.0.0.39:4321",
];

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function cors(origin) {
  const allow = ORIGINS.includes(origin) ? origin : ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }

    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/export") {
      const auth = request.headers.get("Authorization") || "";
      if (auth !== "Bearer " + env.EXPORT_TOKEN) {
        return new Response("nope", { status: 401 });
      }
      const out = [];
      let cursor;
      do {
        const page = await env.WAITLIST.list({ prefix: "email:", cursor });
        for (const k of page.keys) {
          const v = await env.WAITLIST.get(k.name);
          out.push({ email: k.name.slice(6), meta: v ? JSON.parse(v) : null });
        }
        cursor = page.list_complete ? undefined : page.cursor;
      } while (cursor);
      return new Response(JSON.stringify(out, null, 2), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (request.method !== "POST") {
      return new Response("POST an email.", { status: 405, headers: cors(origin) });
    }

    // light per-IP rate limit: 5 posts / 10 minutes
    const ip = request.headers.get("CF-Connecting-IP") || "unknown";
    const rlKey = "rl:" + ip;
    const hits = parseInt((await env.WAITLIST.get(rlKey)) || "0", 10);
    if (hits >= 5) {
      return new Response(JSON.stringify({ ok: false, error: "slow down" }), {
        status: 429,
        headers: { "Content-Type": "application/json", ...cors(origin) },
      });
    }
    await env.WAITLIST.put(rlKey, String(hits + 1), { expirationTtl: 600 });

    let email = "";
    const ct = request.headers.get("Content-Type") || "";
    try {
      if (ct.includes("application/json")) {
        email = ((await request.json()).email || "").trim();
      } else {
        email = ((await request.formData()).get("email") || "").trim();
      }
    } catch (e) {
      /* fall through to validation */
    }

    if (!EMAIL_RE.test(email) || email.length > 254) {
      return new Response(JSON.stringify({ ok: false, error: "invalid email" }), {
        status: 400,
        headers: { "Content-Type": "application/json", ...cors(origin) },
      });
    }

    const key = "email:" + email.toLowerCase();
    const existing = await env.WAITLIST.get(key);
    if (!existing) {
      await env.WAITLIST.put(
        key,
        JSON.stringify({
          ts: new Date().toISOString(),
          ua: request.headers.get("User-Agent") || "",
          ref: request.headers.get("Referer") || "",
        })
      );
    }
    return new Response(JSON.stringify({ ok: true }), {
      headers: { "Content-Type": "application/json", ...cors(origin) },
    });
  },
};
