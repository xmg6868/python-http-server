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

            with urllib.request.urlopen("https://httpbin.org/get", timeout=20, context=ctx) as resp:
                data = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Outbound OK!\n\n")
                self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Outbound failed: {type(e).__name__}: {e}".encode())

    def log_message(self, format, *args):
        print(format % args)

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", int(os.environ.get("PORT", 80))), TestHandler).serve_forever()
