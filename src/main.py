import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Hello from Wasmer! Proxy is working.")

    def log_message(self, format, *args):
        print(format % args)

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 80))
    print(f"Server starting on {host}:{port}")
    HTTPServer((host, port), Handler).serve_forever()
