from django.contrib import admin
from .models import ErrorLog, Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ('line_total',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_no', 'customer_name', 'phone', 'total_amount', 'payment_method', 'whatsapp_status', 'created_at')
    list_filter = ('payment_method', 'whatsapp_status', 'created_at')
    search_fields = ('invoice_no', 'customer_name', 'phone')
    readonly_fields = ('invoice_no', 'created_at', 'total_amount')
    inlines = [InvoiceItemInline]
    ordering = ('-created_at',)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product_name', 'quantity', 'price_per_unit', 'line_total')
    list_filter = ('product_name',)
    readonly_fields = ('line_total',)


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