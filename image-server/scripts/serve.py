# Image server — development static file server (convenience wrapper)
#
# Usage:
#   python serve.py [port]            # default 8000
#
# This is exactly equivalent to:  python -m http.server 8000
# It just prints a friendly hint about IMAGE_BASE_URL.
import http.server
import os
import socketserver
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "images")

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

if not os.path.isdir(ROOT):
    sys.exit(f"Image root not found: {ROOT}\nPut your images under image-server/images/")

os.chdir(ROOT)

handler = http.server.SimpleHTTPRequestHandler

class QuietHandler(handler):
    def log_message(self, fmt, *args):
        sys.stderr.write("[image-server] %s\n" % (fmt % args))

with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
    print(f"image-server serving {ROOT}")
    print(f"  -> http://localhost:{PORT}/images/nepal/kathmandu/001.webp")
    print(f"Make sure Django's IMAGE_BASE_URL=http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
