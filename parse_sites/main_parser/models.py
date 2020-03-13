from django.db import models
from django.utils import timezone
from dynamic_scraper.models import Scraper, SchedulerRuntime
from scrapy_djangoitem import DjangoItem


class WebSite(models.Model):
    code = models.AutoField(primary_key=True, default=0)
    name = models.CharField(max_length=200)
    url = models.URLField()
    object_type = models.IntegerField(default=None)
    scraper = models.ForeignKey(Scraper, blank=True, null=True, on_delete=models.SET_NULL)
    scraper_runtime = models.ForeignKey(SchedulerRuntime, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name


class DataModel(models.Model):
    code = models.AutoField(primary_key=True)
    web_site = models.ForeignKey(WebSite)

    # общее
    name_object = models.CharField(max_length=100, null=True, blank=True)
    seller = models.CharField(max_length=100, null=True, blank=True)
    cost_object = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    obj_url = models.URLField()
    date_announcement = models.DateField(null=True, blank=True)
    unique_number = models.IntegerField()
    total_area = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    region = models.CharField(max_length=50, null=True, blank=True)
    locality = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=50, null=True, blank=True)
    house = models.CharField(max_length=20, null=True, blank=True)
    cad_num = models.CharField(max_length=50, null=True, blank=True)
    cad_status = models.IntegerField(null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)
    parse_date = models.DateField(default=timezone.now)
    parse_site = models.CharField(max_length=50, null=True, blank=True)
    analog_1price = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    objecttype = models.IntegerField(default=0)
    screenshot = models.TextField(null=False, blank=False, default='None')
    updated_date_announcement = models.DateField(null=True, blank=True)

    # квартиры, помещения, дома
    # rooms_in_apartments = models.IntegerField(null=True, blank=True)
    floor = models.IntegerField(null=True, blank=True)
    floors = models.IntegerField(null=True, blank=True)
    type_building = models.CharField(max_length=50, null=True, blank=True)
    rent_cost_type = models.CharField(max_length=50, null=True, blank=True)
    wall_material = models.CharField(max_length=50, null=True, blank=True)
    distance_to_city = models.CharField(max_length=50, null=True, blank=True)
    house_area = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    type_partipication = models.CharField(max_length=50, null=True, blank=True)
    official_developer = models.TextField(null=True, blank=True)
    quantity_rooms = models.CharField(max_length=50, null=True, blank=True)
    kitchen_area = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)
    residential_area = models.DecimalField(max_digits=30, decimal_places=2, null=True, blank=True)

    # гаражи
    type_garage = models.CharField(max_length=50, null=True, blank=True)
    type_carplace = models.CharField(max_length=50, null=True, blank=True)
    secure = models.CharField(max_length=50, null=True, blank=True)

    # координаты
    # coord_point = PointField(default=None)
    coord_point = models.TextField(null=True, blank=True)
    checker_runtime = models.ForeignKey(SchedulerRuntime, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name_object


class DataModelItem(DjangoItem):
    django_model = DataModel
