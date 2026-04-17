from django.contrib import admin
from .models import ErrorLog


@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_message",
        "timestamp",
    )

    list_filter = (
        "timestamp",
    )

    search_fields = (
        "message",
        "traceback",
    )

    readonly_fields = (
        "timestamp",
        "message",
        "traceback",
    )

    ordering = ("-timestamp",)

    list_per_page = 50

    fieldsets = (
        ("Error Info", {
            "fields": (
                "timestamp",
                "message",
            )
        }),
        ("Traceback", {
            "fields": (
                "traceback",
            )
        }),
    )

    def short_message(self, obj):
        return obj.message[:100]

    short_message.short_description = "Message"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False