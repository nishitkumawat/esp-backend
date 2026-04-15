from django.contrib import admin
from .models import IotUser, IotDevice, IotUserDevice,ErrorLog


@admin.register(IotUser)
class IotUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone', 'name', 'is_active', 'created_at')
    search_fields = ('phone', 'name')


@admin.register(IotDevice)
class IotDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'device_code', 'name', 'created_at')
    search_fields = ('device_code', 'name')


@admin.register(IotUserDevice)
class IotUserDeviceAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'device', 'role', 'created_at')
    list_filter = ('role',)


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'short_message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('message', 'traceback')
    readonly_fields = ('message', 'traceback', 'created_at')

    ordering = ('-created_at',)

    def short_message(self, obj):
        return obj.message[:80]
    short_message.short_description = "Message"