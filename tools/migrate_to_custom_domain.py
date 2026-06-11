"""One-shot migration: klarna659.github.io/stack-website  ->  trackyourstack.app

Run this ONLY AFTER the Cloudflare DNS for trackyourstack.app is live and
resolving (see DOMAIN_SETUP_HANDOFF.md). It:
  1. flips BASE_URL in build_library.py to the apex domain (root, no subpath)
  2. rewrites every absolute URL in the static HTML + robots.txt
     (canonicals, OG tags, JSON-LD) from the github.io/stack-website path
     to https://trackyourstack.app
  3. regenerates the compound library + comparisons + guides + sitemap
  4. writes the Pages CNAME file (trackyourstack.app)

Then the operator (or the session) runs:
  git add -A && git commit -m "Point site at trackyourstack.app" && git push
  gh api -X PUT repos/Klarna659/stack-website/pages -f cname=trackyourstack.app -F https_enforced=true

  python tools/migrate_to_custom_domain.py
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OLD = "https://klarna659.github.io/stack-website"
NEW = "https://trackyourstack.app"
APEX = "trackyourstack.app"


def rewrite_static():
    exts = (".html", ".xml", ".txt")
    n = 0
    for dirpath, dirnames, files in os.walk(ROOT):
        # skip git, mockups (deleted), node-ish, hidden
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "mockups"]
        for fn in files:
            if not fn.endswith(exts):
                continue
            p = os.path.join(dirpath, fn)
            with open(p, encoding="utf-8") as f:
                t = f.read()
            if OLD in t:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(t.replace(OLD, NEW))
                n += 1
    return n


def rewrite_base_url():
    p = os.path.join(ROOT, "tools", "build_library.py")
    with open(p, encoding="utf-8") as f:
        t = f.read()
    t = re.sub(r'BASE_URL = "[^"]*"', f'BASE_URL = "{NEW}"', t, count=1)
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)


def write_cname():
    with open(os.path.join(ROOT, "CNAME"), "w", encoding="utf-8", newline="") as f:
        f.write(APEX + "\n")


def main():
    rewrite_base_url()
    n = rewrite_static()
    write_cname()
    # regenerate generated pages with the new BASE_URL
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_library.py")], check=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build_pages.py")], check=True)
    # sanity: nothing should still point at the old host
    leftovers = subprocess.run(
        ["git", "grep", "-l", "klarna659.github.io"], cwd=ROOT,
        capture_output=True, text=True).stdout.strip()
    print(f"rewrote BASE_URL + {n} static files + CNAME, regenerated pages")
    print("leftover github.io refs:", leftovers or "NONE")


if __name__ == "__main__":
    main()
