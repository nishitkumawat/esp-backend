from django.contrib import admin
from .models import (
    CRMUser, Lead, Tag, Note, FollowUp, AuditLog,
    WhatsAppContact, WhatsAppConversation, WhatsAppMessage,
)


@admin.register(CRMUser)
class CRMUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'mobile', 'role', 'is_active', 'created_at', 'last_login')
    list_filter = ('role', 'is_active')
    search_fields = ('name', 'mobile')
    readonly_fields = ('pin_hash', 'created_at', 'last_login')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color')
    search_fields = ('name',)


class NoteInline(admin.TabularInline):
    model = Note
    extra = 0
    readonly_fields = ('user', 'created_at')


class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'category', 'status', 'assigned_to', 'source', 'created_at')
    list_filter = ('category', 'status', 'source', 'assigned_to')
    search_fields = ('name', 'phone')
    filter_horizontal = ('tags',)
    inlines = [NoteInline, FollowUpInline]
    readonly_fields = ('created_at', 'updated_at', 'last_message_at')


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('lead', 'user', 'created_at')
    list_filter = ('user',)
    search_fields = ('content',)
    readonly_fields = ('created_at',)


@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('lead', 'assigned_to', 'date', 'time', 'status')
    list_filter = ('status', 'assigned_to', 'date')
    search_fields = ('remarks',)
    readonly_fields = ('created_at',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'lead', 'created_at')
    list_filter = ('user',)
    search_fields = ('action', 'details')
    readonly_fields = ('user', 'action', 'lead', 'details', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(WhatsAppContact)
class WhatsAppContactAdmin(admin.ModelAdmin):
    list_display = ('phone', 'name', 'category', 'created_at')
    search_fields = ('phone', 'name')


@admin.register(WhatsAppConversation)
class WhatsAppConversationAdmin(admin.ModelAdmin):
    list_display = ('contact', 'lead', 'created_at', 'last_message_at')
    list_filter = ('created_at',)


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'direction', 'sent_by', 'timestamp', 'is_read')
    list_filter = ('direction', 'is_read')
    readonly_fields = ('timestamp',)
