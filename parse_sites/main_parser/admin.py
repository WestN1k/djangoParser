from django.contrib import admin
from .models import DataModel, WebSite

# Register your models here.
admin.site.register(DataModel)
admin.site.register(WebSite)
