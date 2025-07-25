from proxy.http.parser import HttpParser
from proxy.http.proxy import HttpProxyBasePlugin

PROXY_USER = 'brd-customer-hl_1b6b5179-zone-datacenter_proxy1-ip-156.252.228.152'
PROXY_PASS = 'qh13e50d5n6f'
PROXY_HOST = 'brd.superproxy.io'
PROXY_PORT = 33335

class UpstreamProxyPlugin(HttpProxyBasePlugin):
    def handle_upstream_connect(self, request: HttpParser) -> None:
        # Forward all traffic to Bright Data proxy
        self.flags.upstream_proxy = (
            f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        )
