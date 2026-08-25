import os
import urllib.request
import ssl
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote, urlparse

class OpenProxy(BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy()

    def do_HEAD(self):
        self.proxy()

    def proxy(self):
        try:
            path = unquote(self.path)
            if path.startswith("/"):
                path = path[1:]

            # 首页
            if not path:
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1">
                    <title>通用下载加速代理</title>
                    <style>
                        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }
                        h1 { color: #2563eb; }
                        pre { background: #f1f5f9; padding: 12px 16px; border-radius: 8px; overflow-x: auto; }
                        .warn { background: #fef2f2; color: #991b1b; padding: 12px; border-radius: 8px; margin: 16px 0; }
                    </style>
                </head>
                <body>
                    <h1>🌐 通用下载加速代理</h1>
                    <div class="warn">
                        <b>警告：</b>本代理支持任意网站，请仅限个人使用，切勿公开分享。
                    </div>
                    <p><b>使用方法：</b>在原链接前面加上本站地址</p>
                    <pre>https://你的域名/https://example.com/file.zip
https://你的域名/https://github.com/user/repo/releases/download/v1.0/file.zip
https://你的域名/https://huggingface.co/xxx/resolve/main/model.bin</pre>
                </body>
                </html>
                """
                self.wfile.write(html.encode("utf-8"))
                return

            # 自动补全协议
            if not path.startswith("http://") and not path.startswith("https://"):
                path = "https://" + path

            # 简单防止自己代理自己造成死循环
            host = urlparse(path).hostname or ""
            if "wasmer.app" in host:
                self.send_error(403, "不能代理本站自己")
                return

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

            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
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
            error = f"代理错误: {type(e).__name__}: {e}"
            self.wfile.write(error.encode("utf-8"))
            print(error)

    def log_message(self, format, *args):
        print(f"{self.command} {self.path}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    print(f"通用代理已启动 → 端口 {port}")
    HTTPServer(("0.0.0.0", port), OpenProxy).serve_forever()
