from celery import shared_task
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


class CrawlerScript(object):
    def __init__(self, spider, scrapy_settings):
        self.crawler = CrawlerProcess(scrapy_settings)
        self.spider = spider  # just a string

    def run(self, **kwargs):
        # Pass the kwargs (usually command line args) to the crawler
        self.crawler.crawl(self.spider, **kwargs)
        self.crawler.start(stop_after_crawl=False)


@shared_task
def run_spider(spider, **kwargs):
    scrapy_settings = get_project_settings()
    cs = CrawlerScript(spider, scrapy_settings)
    cs.run(**kwargs)
