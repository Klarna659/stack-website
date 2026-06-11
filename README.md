# Stack — landing site

Clean, minimal landing + redirect page for the Stack app. Plain HTML/CSS/JS —
no build step, no dependencies.

## Run it locally
Just open `index.html` in a browser. (For forms/preview to behave exactly like
production, serve it: `npx serve` in this folder, then visit the printed URL.)

## The 4 things to set when you're ready
Open **`assets/js/main.js`** and edit the `CONFIG` block at the very top.
Everything works before you touch it — these just upgrade it.

| Setting | What it does | Until you set it |
|---|---|---|
| `CONTACT_EMAIL` | where form emails go | already set to `hello@trackyourstack.app` |
| `FORM_ENDPOINT` | paste a Formspree / Web3Forms / Getform URL to collect submissions in a dashboard | forms open the visitor's email app pre-filled (works today) |
| `PLAY_URL` | your Google Play listing URL | store buttons say "coming soon" → bounce to the email-notify box |
| `APP_STORE_URL` | your App Store listing URL | same |

### Easiest form backend (5 min, free)
1. Go to **web3forms.com**, enter your email, copy the **access key**.
2. In `main.js`, you can either keep the mailto fallback, or wire Web3Forms:
   set `FORM_ENDPOINT: "https://api.web3forms.com/submit"` and add your key by
   putting `<input type="hidden" name="access_key" value="YOUR_KEY">` inside each
   `<form>` in `index.html`. (Formspree works too — paste its form URL as
   `FORM_ENDPOINT`.)

## Add a screenshot
Drop a `1080×2400` PNG into `assets/img/screens/`, then add one line to the
`SCREENS` array in `main.js`:
```js
{ img: "assets/img/screens/yourfile.png", title: "Title", sub: "One-line caption" },
```

## Deploy (free, ~2 min)
- **Netlify / Cloudflare Pages / Vercel:** drag this whole folder onto their
  dashboard, or connect a Git repo. No settings needed (it's static).
- Point your domain **trackyourstack.app** at it.
- Your hosted legal URLs become:
  - `https://trackyourstack.app/privacy.html`  ← use this for the Play Store data-safety / privacy-policy URL
  - `https://trackyourstack.app/terms.html`

## Structure
```
index.html        landing page (hero, features, screenshots, referral, feedback, notify)
privacy.html      hosted Privacy Policy
terms.html        hosted Terms of Service
assets/css/styles.css
assets/js/main.js   ← CONFIG + screenshot list live here
assets/img/         icon + screenshots
assets/fonts/       Inter (self-hosted)
```

Brand mirrors the app's `DESIGN_SYSTEM.md`: blue `#2563EB`, Inter, light theme.
