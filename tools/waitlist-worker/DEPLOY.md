# Deploying the Stack email list Worker

Nothing here has been deployed. Steps marked **[SIM LOGIN]** need your
Cloudflare or Resend account. Run everything from this folder.

```
cd C:\src\sw_mail\tools\waitlist-worker
```

## 0. Before anything else: the postal address (required)

CAN-SPAM requires a real mailing address in commercial email. The Worker prints
`ADDRESS_LINE` in every email footer. **TODO (Sim): decide the address** (a
street address or a PO box / mailbox service) and set it in `wrangler.toml`:

```toml
[vars]
ADDRESS_LINE = "Cedar Hills Studio LLC, 123 Main St, City, ST 12345"
```

Do not send the launch email until this is set. The confirmation email goes out
without an address line if it is empty.

## 1. Tests (no logins)

```
node --test
```

Expect 22 passing. Needs Node 20 or newer.

## 2. Resend: confirm the sending domain **[SIM LOGIN: Resend]**

The Worker sends as `Stack <hello@trackyourstack.app>`, the same sender the
lifecycle worker uses.

1. Resend dashboard, Domains, `trackyourstack.app`: status must be **Verified**
   (SPF and DKIM records both green). If it is not, add the DNS records Resend
   shows in Cloudflare DNS and click Verify.
2. Optional check from a terminal: `nslookup -type=TXT resend._domainkey.trackyourstack.app`
   should return a DKIM key.
3. Make sure a DMARC record exists: `nslookup -type=TXT _dmarc.trackyourstack.app`.
   If empty, add a TXT record `_dmarc` with `v=DMARC1; p=none; rua=mailto:hello@trackyourstack.app`.
4. API Keys: reuse the existing sending key (same one as the lifecycle worker).

## 3. Cloudflare: log in and set secrets **[SIM LOGIN: Cloudflare]**

```
npx wrangler login
npx wrangler secret put RESEND_API_KEY     # paste the Resend key
npx wrangler secret put HMAC_SECRET        # any long random string, for example the output of:
                                           #   node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
npx wrangler secret put EXPORT_TOKEN       # your own long random string; you use it to export the list
```

The KV namespace in `wrangler.toml` (`WAITLIST`, id `3b65e549...`) already
exists. Setting `HMAC_SECRET` is mandatory: without it links cannot be signed.

## 4. Deploy **[SIM LOGIN: Cloudflare]**

```
npx wrangler deploy
```

It prints the Worker URL, for example `https://stack-waitlist.<account>.workers.dev`.
(The previous version of this Worker used the account `squeeze251`, so expect
`https://stack-waitlist.squeeze251.workers.dev`.) Confirm and unsubscribe links
in emails are built from the URL the request arrives on, so no extra config is
needed. To use a custom domain later, set `PUBLIC_BASE_URL` under `[vars]`.

## 5. Point the site at it

In `C:\src\sw_mail\assets\js\capture.js` replace `TODO_WORKER_URL` with the URL
from step 4 (no trailing slash needed), commit, and merge the branch. Until you
do, the homepage form tells visitors sign-up is not open and shows the email
address.

## 6. Test with curl

Replace `$W` with the Worker URL. Use an inbox you own. `Origin` must be the site
origin, as browsers send it.

```
W=https://stack-waitlist.squeeze251.workers.dev

# should return {"ok":true} and send a confirmation email
curl -i -X POST $W/subscribe -H "Content-Type: application/json" -H "Origin: https://trackyourstack.app" \
  -d '{"email":"you@example.com","source":"launch","consent":true,"website":""}'

# should return 400 consent required
curl -i -X POST $W/subscribe -H "Content-Type: application/json" -H "Origin: https://trackyourstack.app" \
  -d '{"email":"you@example.com","source":"launch","consent":false}'

# open the Confirm link from the email in a browser, then export:
curl -H "Authorization: Bearer YOUR_EXPORT_TOKEN" $W/export
```

Check in the received email: the button works, the footer shows the address,
and Gmail's "Show original" lists `List-Unsubscribe` and
`List-Unsubscribe-Post`. Then click the unsubscribe link and export again: the
address must be gone.

Rate limit: the sixth `/subscribe` from one IP inside 10 minutes returns 429.
A repeat signup for the same pending address inside 10 minutes returns
`{"ok":true}` but sends no second email.

## 7. Export the list

```
curl -H "Authorization: Bearer YOUR_EXPORT_TOKEN" $W/export > list.json
```

Output: `{ "total": n, "counts": { "launch": n, ... }, "subscribers": [ { "email", "source", "confirmedAt", "consentAt", "consentVersion", "unsubscribeUrl" } ] }`.
Confirmed people only. This replaces the old array format. Do not commit
`list.json`.

## 8. Optional: Turnstile (bot check) **[SIM LOGIN: Cloudflare]**

1. Cloudflare dashboard, Turnstile, add a widget for `trackyourstack.app`.
   Copy the site key and the secret key.
2. `npx wrangler secret put TURNSTILE_SECRET` (the secret key), then
   `npx wrangler deploy`. From then on `/subscribe` rejects requests without a
   valid token.
3. In the form markup add, inside the `<form data-capture>`, the widget:
   `<div class="cf-turnstile" data-sitekey="YOUR_SITE_KEY"></div>` and load
   `<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>`.
   Turnstile adds a `cf-turnstile-response` field and `capture.js` sends it.
   Add `https://challenges.cloudflare.com` to any CSP if one is added later.

Do step 2 only after step 3 is live on the site, or sign-ups stop working.

## 9. The 2026-09-07 waitlist entries (decision for Sim)

Older signups sit in KV under `email:<address>` with no consent record. The new
Worker never mails or exports them. Options: delete them, or email each one
once, by hand, asking them to sign up again at the homepage form.

```
npx wrangler kv key list --binding WAITLIST --prefix "email:"
npx wrangler kv key delete --binding WAITLIST "email:someone@example.com"
```

## 10. Not built here

Sending the launch email itself. When it is time, read the export, send through
Resend with `List-Unsubscribe` and `List-Unsubscribe-Post` headers and the
address footer, and use each subscriber's `unsubscribeUrl` from the export as
the unsubscribe link.
