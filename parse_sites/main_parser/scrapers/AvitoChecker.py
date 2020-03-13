from dynamic_scraper.spiders.django_checker import DjangoChecker

from ..models import DataModel


class AvitoChecker(DjangoChecker):
    name = 'avito_checker'

    def __init__(self, *args, **kwargs):
        self._set_ref_object(DataModel, **kwargs)
        self.scraper = self.ref_object.news_website.scraper
        # self.scrape_url = self.ref_object.url (Not used any more in DDS v.0.8.3+)
        self.scheduler_runtime = self.ref_object.checker_runtime
        super(AvitoChecker, self).__init__(self, *args, **kwargs)
