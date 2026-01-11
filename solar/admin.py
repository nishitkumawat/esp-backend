from django.contrib import admin
from .models import SolarHourlyData, WashRecord
# Register your models here.

admin.site.register(SolarHourlyData)
admin.site.register(WashRecord)

