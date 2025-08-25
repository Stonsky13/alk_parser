Точка запуска: из папки alkoparse

cities.json — справочник городов
categories.txt — ссылки на категории

user_agents.txt — список User-Agent’ов, по одному в строке.
proxies.txt — список прокси, по одному в строке.

Базовый запуск (без прокси, с дефолтным городом Краснодар):
scrapy crawl alkospider -O result.json -s LOG_LEVEL=INFO

Как передать город для парсинга:
По slug (ищется в cities.json):
scrapy crawl alkospider -O result.json -a city="moskva"

Запуск с ротацией прокси:
scrapy crawl alkospider -O result.json -s LOG_LEVEL=INFO -s ENABLE_PROXY_ROTATION=True




