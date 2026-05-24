from django.contrib import admin
# pyrefly: ignore [missing-import]
from .models import SolarHourlyData, WashRecord, DeviceLocation, WeatherLog, SolarErrorLog

@admin.register(SolarHourlyData)
class SolarHourlyDataAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'timestamp', 'voltage', 'current', 'power', 'energy')
    list_filter = ('device_id', 'timestamp')
    search_fields = ('device_id',)

@admin.register(WashRecord)
class WashRecordAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'timestamp', 'wash_type', 'voltage', 'current', 'power')
    list_filter = ('device_id', 'wash_type', 'timestamp')
    search_fields = ('device_id',)

@admin.register(DeviceLocation)
class DeviceLocationAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'city', 'state', 'lat', 'lon', 'last_updated')
    list_filter = ('city', 'state')
    search_fields = ('device_id', 'city', 'state')

@admin.register(WeatherLog)
class WeatherLogAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'timestamp', 'lat', 'lon', 'temperature', 'weather_code', 'max_rain', 'skip_wash')
    list_filter = ('device_id', 'skip_wash')
    search_fields = ('device_id',)
    readonly_fields = ('raw_response',)

@admin.register(SolarErrorLog)
class SolarErrorLogAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'error_type', 'timestamp', 'short_message')
    list_filter = ('error_type', 'device_id', 'timestamp')
    search_fields = ('device_id', 'error_type', 'message', 'traceback')
    readonly_fields = ('message', 'traceback', 'timestamp')

    def short_message(self, obj):
        return obj.message[:80]
    short_message.short_description = "Message"
