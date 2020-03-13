from dynamic_scraper.spiders.django_spider import DjangoSpider

from ..models import WebSite, DataModel, DataModelItem


class AvitoSpider(DjangoSpider):
    name = 'avito_spider'

    def __init__(self, *args, **kwargs):
        self._set_ref_object(WebSite, **kwargs)
        self.scraper = self.ref_object.scraper
        self.scrape_url = self.ref_object.url
        self.scheduler_runtime = self.ref_object.scraper_runtime
        self.scraped_obj_class = DataModel
        self.scraped_obj_item_class = DataModelItem
        super(AvitoSpider, self).__init__(self, *args, **kwargs)


class DomofondSpider(DjangoSpider):
    name = 'domofond_spider'

    def __init__(self, *args, **kwargs):
        self._set_ref_object(WebSite, **kwargs)
        self.scraper = self.ref_object.scraper
        self.scrape_url = self.ref_object.url
        self.scheduler_runtime = self.ref_object.scraper_runtime
        self.scraped_obj_class = DataModel
        self.scraped_obj_item_class = DataModelItem
        super(DomofondSpider, self).__init__(self, *args, **kwargs)


class N30Spider(DjangoSpider):
    name = 'n30_spider'

    def __init__(self, *args, **kwargs):
        self._set_ref_object(WebSite, **kwargs)
        self.scraper = self.ref_object.scraper
        self.scrape_url = self.ref_object.url
        self.scheduler_runtime = self.ref_object.scraper_runtime
        self.scraped_obj_class = DataModel
        self.scraped_obj_item_class = DataModelItem
        super(N30Spider, self).__init__(self, *args, **kwargs)


class ConsaltingABCSpider(DjangoSpider):
    name = 'consalting_spider'

    def __init__(self, *args, **kwargs):
        self._set_ref_object(WebSite, **kwargs)
        self.scraper = self.ref_object.scraper
        self.scrape_url = self.ref_object.url
        self.scheduler_runtime = self.ref_object.scraper_runtime
        self.scraped_obj_class = DataModel
        self.scraped_obj_item_class = DataModelItem
        super(ConsaltingABCSpider, self).__init__(self, *args, **kwargs)
