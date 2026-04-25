from mitmproxy import http, options
from mitmproxy.tools.dump import DumpMaster
import json

class RequestHandler:
    def __init__(self):
        self.read_counts = {}

    def request(self, flow: http.HTTPFlow):
        if "mp.weixin.qq.com" in flow.request.pretty_host:
            pass

    def response(self, flow: http.HTTPFlow):
        if "mp.weixin.qq.com" in flow.request.pretty_host:
            try:
                response_data = json.loads(flow.response.text)
                if "read_num" in response_data:
                    article_url = flow.request.url
                    self.read_counts[article_url] = response_data["read_num"]
                    print(f"文章阅读数: {response_data['read_num']}")
            except json.JSONDecodeError:
                pass

    def run_proxy(self):
        import asyncio
        import os
        from mitmproxy import certs

        # 配置 HTTPS 支持
        # 配置 mitmproxy 选项
        conf_dir = os.path.expanduser("~/.mitmproxy")
        opts = options.Options(
            listen_host='0.0.0.0',
            listen_port=8080,
            ssl_insecure=True,  # 允许不安全的 SSL 连接（仅用于开发环境）
        )


        handler = RequestHandler()
        master = DumpMaster(opts,loop=asyncio.new_event_loop())
        master.addons.add(handler)
        print("代理监听已启动，监听地址: 0.0.0.0:8080 (支持 HTTPS)")
        asyncio.run(master.run())

if __name__ == "__main__":
    handler = RequestHandler()
    handler.run_proxy()
