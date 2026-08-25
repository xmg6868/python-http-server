import os
import urllib.request
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse

class GitHubProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy()

    def do_HEAD(self):
        self.proxy()

    def proxy(self):
        try:
            # 取出路径并解码
            path = unquote(self.path)

            # 去掉开头的 /
            if path.startswith("/"):
                path = path[1:]

            # 首页
            if not path:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <h2>GitHub 加速代理</h2>
                <p>使用方法：</p>
                <pre>https://你的域名/https://github.com/user/repo/releases/download/xxx/file.zip</pre>
                <pre>https://你的域名/https://raw.githubusercontent.com/user/repo/main/file.txt</pre>
                """
                self.wfile.write(html.encode("utf-8"))
                return

            # 自动补全 https://
            if not path.startswith("http"):
                path = "https://" + path

            # 简单白名单检查
            host = urlparse(path).hostname or ""
            if "github" not in host and "githubusercontent" not in host:
                self.send_error(403, "只允许 GitHub 相关域名")
                return

            # SSL
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(path)
            req.add_header(
                "User-Agent",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 支持断点续传
            if "Range" in self.headers:
                req.add_header("Range", self.headers["Range"])

            with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
                self.send_response(resp.status)

                for key, value in resp.headers.items():
                    if key.lower() not in ("transfer-encoding", "connection", "content-encoding"):
                        self.send_header(key, value)
                self.end_headers()

                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            error = f"错误: {type(e).__name__}: {e}"
            self.wfile.write(error.encode("utf-8"))
            print(error)

    def log_message(self, format, *args):
        print(f"{self.command} {self.path}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    print(f"Proxy running on port {port}")
    HTTPServer(("0.0.0.0", port), GitHubProxy).serve_forever()
