import os
import urllib.request
import urllib.error
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, unquote, parse_qs

ALLOWED_HOSTS = {
    "github.com",
    "www.github.com",
    "raw.githubusercontent.com",
    "gist.githubusercontent.com",
    "gist.github.com",
    "api.github.com",
    "objects.githubusercontent.com",
    "codeload.github.com",
    "github.githubassets.com",
    "avatars.githubusercontent.com",
    "camo.githubusercontent.com",
    "cloud.githubusercontent.com",
    "user-images.githubusercontent.com",
    "private-user-images.githubusercontent.com",
}

class GitHubProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle()

    def do_HEAD(self):
        self.handle()

    def handle(self):
        try:
            raw_path = unquote(self.path)

            # 支持 ?url= 参数 和 直接路径两种方式
            if raw_path.startswith("/?"):
                qs = parse_qs(raw_path[2:])
                target = qs.get("url", [""])[0]
            else:
                target = raw_path.lstrip("/")

            # 首页
            if not target:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <h2>GitHub 加速代理 (Wasmer)</h2>
                <p>使用方法（两种都可以）：</p>
                <pre>https://你的域名/https://github.com/user/repo/releases/download/v1.0/file.zip</pre>
                <pre>https://你的域名/?url=https://github.com/user/repo/releases/download/v1.0/file.zip</pre>
                <p>也支持 raw、archive、gist 等链接</p>
                """
                self.wfile.write(html.encode("utf-8"))
                return

            # 自动补全协议
            if not target.startswith("http"):
                target = "https://" + target

            parsed = urlparse(target)
            if not parsed.hostname or parsed.hostname not in ALLOWED_HOSTS:
                self.send_error(403, f"不允许的域名: {parsed.hostname}")
                return

            # SSL 设置
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            req = urllib.request.Request(target, method=self.command)
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            # 透传 Range（支持断点续传）
            if "Range" in self.headers:
                req.add_header("Range", self.headers["Range"])

            with urllib.request.urlopen(req, timeout=90, context=ctx) as resp:
                self.send_response(resp.status)

                # 转发重要响应头
                skip_headers = {"transfer-encoding", "connection", "content-encoding"}
                for key, value in resp.getheaders():
                    if key.lower() not in skip_headers:
                        self.send_header(key, value)
                self.end_headers()

                # 流式转发
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

        except urllib.error.HTTPError as e:
            self.send_error(e.code, f"GitHub 返回错误: {e.reason}")
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            msg = f"代理错误: {type(e).__name__}: {str(e)}"
            self.wfile.write(msg.encode("utf-8"))
            print(msg)

    def log_message(self, format, *args):
        print(f"{self.command} {self.path}")

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 80))
    print(f"GitHub Proxy 已启动 → {host}:{port}")
    HTTPServer((host, port), GitHubProxy).serve_forever()
