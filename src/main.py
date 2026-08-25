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
        self.handle()

    def do_HEAD(self):
        self.handle()

    def handle(self):
        try:
            path = unquote(self.path.lstrip("/"))

            # 首页
            if not path:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <h2>GitHub 加速代理 (Wasmer)</h2>
                <p>使用方法：在 GitHub 链接前面加上本站地址</p>
                <pre>https://你的域名/https://github.com/user/repo/releases/download/v1.0/file.zip</pre>
                <pre>https://你的域名/https://raw.githubusercontent.com/user/repo/main/README.md</pre>
                """
                self.wfile.write(html.encode("utf-8"))
                return

            # 自动补全 https://
            if not path.startswith("http"):
                path = "https://" + path

            parsed = urlparse(path)
            if not parsed.hostname or parsed.hostname not in ALLOWED_HOSTS:
                self.send_error(403, f"不允许的域名: {parsed.hostname}")
                return

            # 关闭 SSL 证书验证（Wasmer 沙箱里经常需要）
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(path, method=self.command)
            req.add_header("User-Agent", "Mozilla/5.0 (Wasmer-GitHub-Proxy)")

            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                self.send_response(resp.status)

                # 转发响应头
                for key, value in resp.getheaders():
                    if key.lower() not in ("transfer-encoding", "connection", "content-encoding"):
                        self.send_header(key, value)
                self.end_headers()

                # 流式传输内容
                while True:
                    chunk = resp.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except urllib.error.HTTPError as e:
            self.send_error(e.code, f"上游错误: {e.reason}")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            error_msg = f"代理错误: {type(e).__name__}: {str(e)}"
            self.wfile.write(error_msg.encode("utf-8"))
            print(error_msg)

    def log_message(self, format, *args):
        print(f"{self.command} {self.path}")

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 80))
    print(f"GitHub Proxy 启动在 {host}:{port}")
    HTTPServer((host, port), GitHubProxy).serve_forever()
