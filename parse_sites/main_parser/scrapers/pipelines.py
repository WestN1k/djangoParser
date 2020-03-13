import base64
import logging
import os
from pathlib import PureWindowsPath
from urllib.parse import urlparse

from django.db.utils import IntegrityError
from django.utils import timezone
from dynamic_scraper.models import SchedulerRuntime
from scrapy.exceptions import DropItem
from scrapy_splash import SplashRequest

from . import settings


class DjangoWriterPipeline(object):

    def process_item(self, item, spider):
        if spider.conf['DO_ACTION']:  # Necessary since DDS v.0.9+
            if item.get("screenshot"):  # сохранять, только если создался скриншот страницы
                try:
                    item['web_site'] = spider.ref_object

                    checker_rt = SchedulerRuntime(runtime_type='C')
                    checker_rt.save()

                    item['checker_runtime'] = checker_rt

                    item.save()

                    spider.action_successful = True
                    dds_id_str = str(item._dds_item_page) + '-' + str(item._dds_item_id)
                    spider.struct_log("{cs}Item {id} saved to Django DB.{ce}".format(
                        id=dds_id_str,
                        cs=spider.bcolors['OK'],
                        ce=spider.bcolors['ENDC']))

                except IntegrityError as e:
                    spider.log(str(e), logging.ERROR)
                    spider.log(str(item._errors), logging.ERROR)
                    raise DropItem("Missing attribute.")
        else:
            if not item.is_valid():
                spider.log(str(item._errors), logging.ERROR)
                raise DropItem("Missing attribute.")
        return item


class ScreenshotPipeline(object):

    mobile_header = 'Mozilla/5.0 (Linux; Android 6.0.1; CPH1607 Build/MMB29M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/63.0.3239.111 Mobile Safari/537.36'

    def open_spider(self, spider):
        pass

    def process_item(self, item, spider):
        site_name = urlparse(spider.ref_object.url)
        domain_name = '{uri.netloc}'.format(
            uri=site_name)  # составление доменного имени для сравнения со словарем SITES
        self.parce_date = timezone.now().date()
        self.objecttype = spider.ref_object.object_type
        self.site_name = settings.SITES.get(domain_name, None)

        item['web_site'] = spider.ref_object
        item['parse_date'] = self.parce_date
        item['objecttype'] = self.objecttype
        item['parse_site'] = self.site_name

        if domain_name == "www.avito.ru":
            return self.parse_screenshot(spider, item, self.mobile_header)
        else:
            return self.parse_screenshot(spider, item)

    def return_item(self, response, item):
        if response.status != 200 or not self.site_name:
            return item

        filename = self.save_screenshot(response, item['unique_number'])
        if filename:
            item["screenshot"] = PureWindowsPath(filename)
        return item

    def parse_screenshot(self, spider, item, header=None):
        request = SplashRequest(url=item['obj_url'], splash_headers=header, endpoint='render.json', args=settings.DSCRAPER_SPLASH_ARGS)
        dfd = spider.crawler.engine.download(request, spider)
        dfd.addBoth(self.return_item, item)
        return dfd

    def save_screenshot(self, response, unique_number):
        png_bytes = base64.b64decode(response.data['png'])
        type_object = settings.DICT_FOLDER_NAMES.get(self.objecttype)

        if self.site_name:
            folder_to_save = os.path.join(settings.PATH_TO_MAIN_FOLDER_SAVE, self.site_name, type_object)
        else:
            return None

        filename = '{0}_{1}.png'.format(unique_number, str(self.parce_date))
        file_path = os.path.join(folder_to_save, filename)
        if os.path.isfile(file_path):
            return None
        else:
            try:
                os.makedirs(folder_to_save, exist_ok=True)
                with open(file_path, 'wb') as file:
                    file.write(png_bytes)
                    file.close()
                    return file_path

            except Exception as e:
                print('Save file Error: ', e)
                return None
