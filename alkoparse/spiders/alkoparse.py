import json
from urllib.parse import urlencode
from alkoparse.utils.json_parser import JsonParser
import scrapy


class AlkoSpider(scrapy.Spider):
    name = "alkospider"
    allowed_domains = ["alkoteka.com", "www.alkoteka.com"]

    API_CITY = "https://alkoteka.com/web-api/v1/city"
    API_PRODUCTS = "https://alkoteka.com/web-api/v1/product"
    API_PRODUCT_LINK = "https://alkoteka.com/web-api/v1/product/{slug}"
    BASE_PRODUCT_LINK = "https://alkoteka.com/product/{category_slug}/{slug}"


    DEFAULT_CITY_UUID = "4a70f9e0-46ae-11e7-83ff-00155d026416"
    DEFAULT_CITY_NAME = "Краснодар"

    CITIES_FILE = "cities.json"
    CATEGORIES_FILE = "categories.txt"


    def __init__(self, city="", per_page="40", proxy="", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cookiejar_id = 1
        self.proxy = (proxy or "").strip() or None
        self.city_name = (city or "").strip()
        self.per_page = int(per_page) if str(per_page).isdigit() else 40

        self.age_cookie = [{
            "name": "alkoteka_age_confirm",
            "value": "true",
            "domain": "alkoteka.com",
            "path": "/",
        }]

        self.cities = self._load_cities(self.CITIES_FILE)
        self.city_uuid = self._pick_city_uuid_simple(self.city_name, self.cities)
        self.categories = self._load_categories(self.CATEGORIES_FILE)


    async def start(self):
        url = f"{self.API_CITY}?{urlencode({'city_uuid': self.city_uuid})}"
        yield scrapy.Request(
            url,
            cookies=self.age_cookie,
            meta=self._meta(stage="set_city"),
            callback=self.after_set_city,
            dont_filter=True,
        )

    def after_set_city(self, response):
        if response.status != 200:
            self.logger.error(f"[Город] ошибка get города: {response.status}")
            raise scrapy.exceptions.CloseSpider(reason="city_cookies_failed")
        if not self.categories:
            self.logger.error("[Категории] Список категорий пуст")
            raise scrapy.exceptions.CloseSpider("no_categories")
        for cat_url in self.categories:
            slug = self._category_slug(cat_url)
            if not slug:
                self.logger.warning(f"[cat] не смог вытащить category_slug из {cat_url}")
                continue
            yield self._req_product_list(slug, page=1)

    def _meta(self, **extra):
        m = {"cookiejar": self.cookiejar_id}
        if self.proxy:
            m["proxy"] = self.proxy
        m.update(extra)
        return m

    def _load_cities(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"[cities] не удалось прочитать {path}: {e}")
            return []

        try:
            data = json.loads(content)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and isinstance(data.get("results"), list):
                return data["results"]
        except Exception:
            pass

    def _pick_city_uuid_simple(self, city_name, cities):
        if city_name and cities:
            for c in cities:
                name = str(c.get("name") or "").strip().lower()
                if name == city_name:
                    uuid = str(c.get("uuid") or "").strip()
                    if uuid:
                        return uuid
            self.logger.warning(f"[cities] город '{city_name}' не найден в файле, используем Краснодар")
        return self.DEFAULT_CITY_UUID

    def _load_categories(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
        except FileNotFoundError:
            self.logger.warning(f"[Категории] нет файла {path}")
            return []
        except Exception as e:
            self.logger.warning(f"[Категории] ошибка {path}: {e}")
            return []
        if len(lines) > 0:
            return lines
        else:
            self.logger.warning(f"[Категории] Файл категорий пуст {path}")
            return []

    def _category_slug(self, url):
        if not url:
            return ""
        try:
            parts = url.strip("/").split("/")
            if "catalog" in parts:
                i = parts.index("catalog")
                if i + 1 < len(parts):
                    return parts[i + 1]
        except Exception:
            pass
        return ""

    def _req_product_list(self, root_category_slug, page):
        qs = {
            "city_uuid": self.city_uuid,
            "page": page,
            "per_page": self.per_page,
            "root_category_slug": root_category_slug,
        }
        url = f"{self.API_PRODUCTS}?{urlencode(qs)}"
        return scrapy.Request(
            url,
            cookies=self.age_cookie,
            meta=self._meta(stage="list", root_category_slug=root_category_slug, page=page),
            callback=self.parse_product_list,
            dont_filter=True,
        )

    def parse_product_list(self, response):
        if response.status != 200:
            self.logger.warning(f"[product_list] {response.status} : {response.url}")
            return
        try:
            raw = response.json()
        except Exception as e:
            self.logger.warning(f"[product_list] не JSON: {e} : {response.url}")
            return

        items = raw.get("results") or []
        meta = raw.get("meta") or {}
        root_category_slug = response.meta.get("root_category_slug") or ""

        for prod in items:
            slug = str(prod.get("slug") or "").strip()
            category_slug = str(prod.get("category_slug") or "").strip() or root_category_slug
            if not slug:
                continue

            detail_url = self.API_PRODUCT_LINK.format(slug=slug) + "?" + urlencode({"city_uuid": self.city_uuid})
            product_url = self.BASE_PRODUCT_LINK.format(category_slug=category_slug, slug=slug)

            yield scrapy.Request(
                detail_url,
                cookies=self.age_cookie,
                meta=self._meta(stage="detail", product_url=product_url, category_slug=category_slug),
                callback=self.parse_product_detail,
                dont_filter=True,
            )

        if bool(meta.get("has_more_pages")):
            next_page = (response.meta.get("page") or 1) + 1
            yield self._req_product_list(root_category_slug, page=next_page)

    def parse_product_detail(self, response):
        if response.status != 200:
            self.logger.warning(f"[product_detail] {response.status} : {response.url}")
            return

        try:
            raw = response.json()
        except Exception as e:
            self.logger.warning(f"[product_detail] не JSON: {e} → {response.url}")
            return
        product_results = raw.get('results')
        if not isinstance(product_results, dict):
            self.logger.warning(f"[product_detail_result] пусто/не dict : {response.url}")
            return

        product_url = response.meta.get("product_url", "")
        item = JsonParser(product_results, product_url).parse()
        yield item
