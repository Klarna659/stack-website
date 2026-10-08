"""Dev server WITH HTTP Range support — python -m http.server has none,
and without Range headless Chrome reports an empty seekable range and
silently clamps every video.currentTime write to 0, which kills the
scroll-scrubbed hero in local verification. (Cloudflare Pages serves
Ranges in production; this is dev-parity only.)

    python tools/serve.py [port]     default 4321, serves the repo root
"""
import os
import re
import sys
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        if not m or not os.path.exists(path):
            return super().send_head()
        size = os.path.getsize(path)
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None
        f = open(path, "rb")
        f.seek(start)
        self.send_response(206)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._range_left = end - start + 1
        return f

    def copyfile(self, source, outputfile):
        left = getattr(self, "_range_left", None)
        if left is None:
            return super().copyfile(source, outputfile)
        while left > 0:
            chunk = source.read(min(65536, left))
            if not chunk:
                break
            outputfile.write(chunk)
            left -= len(chunk)
        self._range_left = None


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4321
    os.chdir(ROOT)
    print("serving %s on http://localhost:%d (Range-capable)" % (ROOT, port))
    # Threading matters: a browser holds media connections open, and a
    # single-threaded server would block every other client behind them.
    # 0.0.0.0 so Sim's phone on the same wifi can open the real page —
    # a screen recording of a scroll-driven hero is not the experience.
    ThreadingHTTPServer(("0.0.0.0", port), RangeHandler).serve_forever()


if __name__ == "__main__":
    main()
