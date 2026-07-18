"""One-off: mesh the hand-authored pages with the new "ledger + gold thread"
paper-default chrome (the generated pages are handled by build_library.py).

Patches: theme-color meta (light default + dark media), favicon, asset cache
version, the pre-paint theme script, brand-mark disc fills -> CSS vars, and a
nav theme toggle. Idempotent. Run from repo root: python tools/brand_mesh_fix.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PAGES = [
    "creators.html", "data-deletion.html", "privacy.html", "referral.html",
    "terms.html", "stacks/index.html", "tools/reconstitution/index.html",
]

PREPAINT = ('<script>(function(){try{var t=localStorage.getItem("stack-theme");'
            'if(t==="dark"||t==="light")document.documentElement.setAttribute'
            '("data-theme",t);}catch(e){}})();</script>')

TOGGLE = ('<button class="theme-toggle" id="themeToggle" type="button" '
          'aria-label="Switch theme" title="Switch theme">'
          '<svg class="sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="2" stroke-linecap="round" aria-hidden="true">'
          '<circle cx="12" cy="12" r="4.2"/><path d="M12 2v2.5M12 19.5V22M4.2 4.2l1.8 1.8'
          'M18 18l1.8 1.8M2 12h2.5M19.5 12H22M4.2 19.8 6 18M18 6l1.8-1.8"/></svg>'
          '<svg class="moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
          'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
          '<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg></button>')


def patch(html: str) -> str:
    # theme-color: single dark meta -> light default + dark media
    html = re.sub(
        r'<meta name="theme-color" content="#0b0b0f" ?/>',
        '<meta name="theme-color" content="#FBFBFA" media="(prefers-color-scheme: light)" />\n'
        '  <meta name="theme-color" content="#0B0B0F" media="(prefers-color-scheme: dark)" />',
        html, flags=re.I)
    # favicon + asset versions
    html = html.replace("img/icon-dark.svg", "img/icon.svg")
    html = html.replace("mono.css?v=2", "mono.css?v=3").replace("site.js?v=2", "site.js?v=3")
    # pre-paint theme script, once, right after the stylesheet link
    if "stack-theme" not in html:
        html = re.sub(r'(<link rel="stylesheet" href="[^"]*mono\.css\?v=3" />)',
                      r'\1\n  ' + PREPAINT, html, count=1)
    # brand-mark disc fills -> theme-aware vars
    html = (html.replace('fill="#c9ccd2"', 'fill="var(--brand-1)"')
                .replace('fill="#6b6e76"', 'fill="var(--brand-2)"')
                .replace('fill="#f4f4f5"', 'fill="var(--brand-3)"'))
    # nav theme toggle, once, right after the first nav-links </nav>
    if 'id="themeToggle"' not in html:
        html = re.sub(r'(</nav>)', r'\1\n      ' + TOGGLE, html, count=1)
    return html


def main() -> None:
    for rel in PAGES:
        path = os.path.join(ROOT, rel.replace("/", os.sep))
        with open(path, encoding="utf-8") as f:
            src = f.read()
        out = patch(src)
        with open(path, "w", encoding="utf-8") as f:
            f.write(out)
        print(("patched " if out != src else "unchanged ") + rel)


if __name__ == "__main__":
    main()
