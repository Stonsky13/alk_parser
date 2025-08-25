import random
from pathlib import Path

class RandomUserAgentMiddleware:
    def __init__(self, uas, enabled):
        self.enabled = enabled
        self.uas = uas or []

    @classmethod
    def from_crawler(cls, crawler):
        enabled = crawler.settings.getbool("ENABLE_UA_ROTATION", True)
        p = Path("user_agents.txt")
        if p.exists():
            uas = [
                line.strip() for line in p.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        else:
            uas = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
            ]
        return cls(uas, enabled)

    def process_request(self, request, spider):
        if not self.enabled or not self.uas:
            return
        if "User-Agent" in request.headers:
            return
        request.headers["User-Agent"] = random.choice(self.uas).encode("utf-8")


class RotateProxyFromFileMiddleware:
    def __init__(self, proxies, enabled):
        self.enabled = enabled
        self.proxies = proxies or []

    @classmethod
    def from_crawler(cls, crawler):
        enabled = crawler.settings.getbool("ENABLE_PROXY_ROTATION", False)
        p = Path("proxies.txt")
        proxies = []
        if p.exists():
            proxies = [
                line.strip() for line in p.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        return cls(proxies, enabled)

    def process_request(self, request, spider):
        if not self.enabled or not self.proxies:
            return
        if "proxy" in request.meta:
            return
        request.meta["proxy"] = random.choice(self.proxies)
