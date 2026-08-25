import os
import urllib.request
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler

class TestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            url = "https://raw.githubusercontent.com/octocat/Hello-World/master/README"
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"GitHub Raw OK!\n\n")
                self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"GitHub test failed: {type(e).__name__}: {e}".encode("utf-8"))

    def log_message(self, format, *args):
        print(format % args)

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 80))), TestHandler).serve_forever()
