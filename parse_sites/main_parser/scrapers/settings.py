import os
import sys
import django
from django.conf import settings

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

sys.path.append("C:/django_example/ParserOnDjango/parse_sites")
os.environ['DJANGO_SETTINGS_MODULE'] = 'parse_sites.settings'

django.setup()
if not settings.configured:
    settings.configure()

BOT_NAME = 'sites_scraper'

SPIDER_MODULES = ['dynamic_scraper.spiders', 'main_parser.scrapers', ]
USER_AGENT = '%s/%s' % (BOT_NAME, '1.0')

ITEM_PIPELINES = {
    'dynamic_scraper.pipelines.ValidationPipeline': 100,
    'main_parser.scrapers.pipelines.ScreenshotPipeline': 150,
    'main_parser.scrapers.pipelines.DjangoWriterPipeline': 200,
}

DOWNLOADER_MIDDLEWARES = {
    'scrapy_splash.SplashCookiesMiddleware': 723,
    'scrapy_splash.SplashMiddleware': 725,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
    # 'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    # 'scrapy_proxies.RandomProxy': 100,
    # 'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
}

SPIDER_MIDDLEWARES = {
    'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
}

LOG_STDOUT = False

IMAGES_STORE = os.path.join(PROJECT_ROOT, '../images')

DSCRAPER_CUSTOM_PROCESSORS = [
    'main_parser.scrapers.processors.MainProcessors',
]

# время ожидания между запросами страницы
DOWNLOAD_DELAY = 3

# ======================== SPLASH SETTINGS ===================================

DSCRAPER_SPLASH_ARGS = {
            'png': 1,
            'width': 1200,
            'render_all': 1,
            'wait': 2,
}

SPLASH_URL = 'http://192.168.99.100:8050/'  # splash (если django настроен через docker-compose) или 192.168.99.100
DUPEFILTER_CLASS = 'scrapy_splash.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapy_splash.SplashAwareFSCacheStorage'

# =============================== SAVE SCREENSHOTS ================================

PATH_TO_MAIN_FOLDER_SAVE = os.path.join('данные_с_сайтов', 'screenshots')

DICT_FOLDER_NAMES = {
    1: 'земельные участки',
    2: 'дома',
    6: 'коммерческая недвижимость',
    8: 'гаражи и машиноместа',
    101: 'квартиры',
    102: 'комнаты',
}

SITES = {
    'www.avito.ru': 'авито',
    'n30.ru': 'n30',
    'www.cyan.ru': 'циан',
    'www.domofond.ru': 'домофонд',
    'www.consulting-abv.ru': 'консалтинг АБВ',
}

# ======================================= PROXIES ================================
# Retry many times since proxies often fail
RETRY_TIMES = 10

# Retry on most error codes since proxies fail for different reasons
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408]

# Proxy list containing entries like
# http://host1:port
# http://username:password@host2:port
# http://host3:port
# ...
PROXY_LIST = os.path.join(PROJECT_ROOT, 'proxy_list.txt')

# Proxy mode
# 0 = Every requests have different proxy
# 1 = Take only one proxy from the list and assign it to every requests
# 2 = Put a custom proxy to use in the settings
PROXY_MODE = 0

# If proxy mode is 2 uncomment this sentence :
#CUSTOM_PROXY = "http://host1:port"