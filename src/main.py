import os
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

ALLOWED_HOSTS = {
    "github.com",
    "raw.githubusercontent.com",
    "gist.githubusercontent.com",
    "api.github.com",
    "objects.githubusercontent.com",
    "codeload.github.com",
}

class GitHubProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy()

    def do_HEAD(self):
        self.proxy()

    def proxy(self):
        # 支持两种写法：
        # 1. /https://github.com/user/repo/...
        # 2. /github.com/user/repo/...
        path = unquote(self.path.lstrip("/"))

        if not path:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"""
            <h1>GitHub Proxy on Wasmer</h1>
            <p>Usage:</p>
            <pre>https://你的域名/https://github.com/user/repo/releases/download/v1.0/file.zip</pre>
            <pre>https://你的域名/https://raw.githubusercontent.com/user/repo/main/file.txt</pre>
            """)
            return

        if not path.startswith("http"):
            path = "https://" + path

        parsed = urlparse(path)
        if parsed.hostname not in ALLOWED_HOSTS:
            self.send_error(403, "Host not allowed")
            return

        try:
            req = urllib.request.Request(path, method=self.command)
            # 透传部分请求头
            for header in ["User-Agent", "Accept", "Range"]:
                if header in self.headers:
                    req.add_header(header, self.headers[header])

            with urllib.request.urlopen(req, timeout=30) as resp:
                self.send_response(resp.status)
                # 透传响应头
                for key, value in resp.getheaders():
                    if key.lower() not in ["transfer-encoding", "connection"]:
                        self.send_header(key, value)
                self.end_headers()

                # 流式转发内容
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except urllib.error.HTTPError as e:
            self.send_error(e.code, e.reason)
        except Exception as e:
            self.send_error(502, str(e))

    def log_message(self, format, *args):
        # 减少日志噪音
        pass

if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 80))
    server = HTTPServer((host, port), GitHubProxy)
    print(f"GitHub Proxy running on http://{host}:{port}")
    server.serve_forever()
