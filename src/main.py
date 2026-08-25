import os
import urllib.request
import urllib.error
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote

ALLOWED_HOSTS = {
    "github.com",
    "raw.githubusercontent.com",
    "gist.githubusercontent.com",
    "api.github.com",
    "objects.githubusercontent.com",
    "codeload.github.com",
    "github.githubassets.com",
}

class GitHubProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request()

    def do_HEAD(self):
        self.handle_request()

    def handle_request(self):
        try:
            path = unquote(self.path.lstrip("/"))

            # 首页提示
            if not path or path == "":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <h1>GitHub Proxy on Wasmer</h1>
                <p>使用示例：</p>
                <pre>https://你的域名/https://github.com/user/repo/releases/download/v1.0/file.zip</pre>
                <pre>https://你的域名/https://raw.githubusercontent.com/user/repo/main/README.md</pre>
                """
                self.wfile.write(html.encode("utf-8"))
                return

            if not path.startswith("http"):
                path = "https://" + path

            parsed = urlparse(path)
            if not parsed.hostname or parsed.hostname not in ALLOWED_HOSTS:
                self.send_error(403, f"Host not allowed: {parsed.hostname}")
                return

            # 创建不验证证书的上下文（解决某些沙箱 SSL 问题）
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(path, method=self.command)
            req.add_header("User-Agent", "Mozilla/5.0 (Wasmer-GitHub-Proxy)")

            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                self.send_response(resp.status)
                for key, value in resp.getheaders():
                    kl = key.lower()
                    if kl not in ("transfer-encoding", "connection", "content-encoding"):
                        self.send_header(key, value)
                self.end_headers()

                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except urllib.error.HTTPError as e:
            self.send_error(e.code, f"Upstream HTTP Error: {e.reason}")
        except Exception as e:
            # 直接把错误返回给浏览器，方便调试
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(f"Proxy Error: {type(e).__name__}: {str(e)}".encode("utf-8"))

    def log_message(self, format, *args):
        print(f"[{self.command}] {self.path} -> {format % args}")

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 80))
    print(f"Starting GitHub Proxy on {host}:{port}")
    server = HTTPServer((host, port), GitHubProxy)
    server.serve_forever()            <pre>https://你的域名/https://raw.githubusercontent.com/user/repo/main/file.txt</pre>
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
