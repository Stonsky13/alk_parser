BOT_NAME = "alkoparse"

SPIDER_MODULES = ["alkoparse.spiders"]
NEWSPIDER_MODULE = "alkoparse.spiders"

ROBOTSTXT_OBEY = False
COOKIES_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"

CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 0.35
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 30

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 20
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = False

RETRY_ENABLED = True
RETRY_TIMES = 5
RETRY_HTTP_CODES = [429, 500, 502, 503, 504, 522, 524]
RETRY_BACKOFF_BASE = 2
RETRY_BACKOFF_MAX = 60


LOG_LEVEL = "INFO"

DEFAULT_REQUEST_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru,en;q=0.9",
    "Connection": "keep-alive",
    "Referer": "https://alkoteka.com/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}

DOWNLOADER_MIDDLEWARES = {
    "alkoparse.middlewares.RandomUserAgentMiddleware": 400,
    "scrapy.downloadermiddlewares.useragent.UserAgentMiddleware": None,
    "alkoparse.middlewares.RotateProxyFromFileMiddleware": 410,
}

ENABLE_UA_ROTATION = True
ENABLE_PROXY_ROTATION = True
