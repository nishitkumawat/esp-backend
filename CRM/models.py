from django.db import models
from django.contrib.auth.hashers import make_password, check_password


# ============================================================
# CRM USER MODEL
# ============================================================
class CRMUser(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('sales_executive', 'Sales Executive'),
    ]

    name = models.CharField(max_length=100)
    mobile = models.CharField(max_length=15, unique=True)
    pin_hash = models.CharField(max_length=128)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='sales_executive')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'crm_user'
        verbose_name = 'CRM User'
        verbose_name_plural = 'CRM Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.mobile})"

    def set_pin(self, raw_pin):
        self.pin_hash = make_password(raw_pin)

    def check_pin(self, raw_pin):
        return check_password(raw_pin, self.pin_hash)

    @property
    def is_admin(self):
        return self.role == 'admin'


# ============================================================
# TAG MODEL
# ============================================================
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#FFA500')

    class Meta:
        db_table = 'crm_tag'
        ordering = ['name']

    def __str__(self):
        return self.name


# ============================================================
# LEAD MODEL
# ============================================================
class Lead(models.Model):
    CATEGORY_CHOICES = [
        ('solar_structure', 'Solar Structure'),
        ('roll_forming_machine', 'Roll Forming Machine'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('to_quote', 'To Quote'),
        ('quote_sent', 'Quote Sent'),
        ('future_lead', 'Future Lead'),
        ('deal_closed', 'Deal Closed'),
        ('not_useful', 'Not Useful'),
    ]

    SOURCE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('advertisement', 'Advertisement'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        CRMUser, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads'
    )
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='whatsapp')
    remarks = models.TextField(blank=True, default='')
    follow_up_date = models.DateField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='leads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'crm_lead'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.phone}"

    def get_status_display_class(self):
        """Return Bootstrap badge class for status."""
        mapping = {
            'new': 'primary',
            'to_quote': 'info',
            'quote_sent': 'warning',
            'future_lead': 'secondary',
            'deal_closed': 'success',
            'not_useful': 'danger',
        }
        return mapping.get(self.status, 'secondary')


# ============================================================
# NOTE MODEL
# ============================================================
class Note(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='notes')
    user = models.ForeignKey(CRMUser, on_delete=models.SET_NULL, null=True, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_note'
        ordering = ['-created_at']

    def __str__(self):
        return f"Note by {self.user} on Lead #{self.lead_id}"


# ============================================================
# FOLLOW-UP MODEL
# ============================================================
class FollowUp(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    assigned_to = models.ForeignKey(
        CRMUser, on_delete=models.SET_NULL, null=True, related_name='followups'
    )
    date = models.DateField()
    time = models.TimeField()
    remarks = models.TextField(blank=True, default='')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_followup'
        ordering = ['date', 'time']

    def __str__(self):
        return f"Follow-up for Lead #{self.lead_id} on {self.date}"


# ============================================================
# AUDIT LOG MODEL
# ============================================================
class AuditLog(models.Model):
    user = models.ForeignKey(
        CRMUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=255)
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    details = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_audit_log'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.action}"


# ============================================================
# WHATSAPP MODELS (For Future Baileys Integration)
# ============================================================
class WhatsAppContact(models.Model):
    phone = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=200, blank=True, default='')
    category = models.CharField(max_length=30, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_whatsapp_contact'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name or self.phone}"


class WhatsAppConversation(models.Model):
    contact = models.ForeignKey(
        WhatsAppContact, on_delete=models.CASCADE, related_name='conversations'
    )
    lead = models.ForeignKey(
        Lead, on_delete=models.SET_NULL, null=True, blank=True, related_name='conversations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'crm_whatsapp_conversation'
        ordering = ['-last_message_at']

    def __str__(self):
        return f"Conversation with {self.contact}"


class WhatsAppMessage(models.Model):
    DIRECTION_CHOICES = [
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ]
    DELIVERY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    conversation = models.ForeignKey(
        WhatsAppConversation, on_delete=models.CASCADE, related_name='messages'
    )
    text = models.TextField()
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    sent_by = models.ForeignKey(
        CRMUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_messages'
    )
    message_id = models.CharField(max_length=255, null=True, blank=True, help_text="Baileys message ID for delivery tracking")
    delivery_status = models.CharField(max_length=15, choices=DELIVERY_STATUS_CHOICES, default='pending')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'crm_whatsapp_message'
        ordering = ['timestamp']

    def __str__(self):
        return f"{'->' if self.direction == 'outgoing' else '<-'} {self.text[:50]}"


# ============================================================
# CHAT STATE MODEL (State-based Chatbot Flow)
# ============================================================
class ChatState(models.Model):
    """
    Tracks the chatbot conversation state for each WhatsApp phone number.
    Uses state-machine approach (never message count logic).
    """
    STATE_CHOICES = [
        ('start', 'Start'),
        ('waiting_category', 'Waiting Category Selection'),
        ('waiting_solar_details', 'Waiting Solar Details'),
        ('waiting_machine_details', 'Waiting Machine Details'),
        ('completed', 'Completed'),
    ]

    phone = models.CharField(max_length=20, unique=True)
    current_state = models.CharField(max_length=30, choices=STATE_CHOICES, default='start')
    context_data = models.JSONField(default=dict, blank=True, help_text="Temporary data collected during flow")
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_chat_state'
        verbose_name = 'Chat State'
        verbose_name_plural = 'Chat States'

    def __str__(self):
        return f"{self.phone} → {self.current_state}"


# ============================================================
# LEAD TIMELINE MODEL
# ============================================================
class LeadTimeline(models.Model):
    """
    Chronological event log for a lead. Richer than AuditLog — shows customer-facing events.
    """
    EVENT_CHOICES = [
        ('lead_created', 'Lead Created'),
        ('status_changed', 'Status Changed'),
        ('note_added', 'Note Added'),
        ('followup_added', 'Follow-Up Added'),
        ('message_received', 'Message Received'),
        ('message_sent', 'Message Sent'),
        ('user_assigned', 'User Assigned'),
        ('category_selected', 'Category Selected'),
        ('quote_sent', 'Quote Sent'),
        ('deal_closed', 'Deal Closed'),
        ('other', 'Other'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='timeline')
    event_type = models.CharField(max_length=30, choices=EVENT_CHOICES, default='other')
    description = models.TextField()
    created_by = models.ForeignKey(
        CRMUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='timeline_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crm_lead_timeline'
        ordering = ['-created_at']
        verbose_name = 'Lead Timeline'
        verbose_name_plural = 'Lead Timeline Events'

    def __str__(self):
        return f"[{self.event_type}] {self.lead.name} - {self.description[:50]}"


# ============================================================
# WHATSAPP CONFIGURATION MODEL
# ============================================================
class WhatsAppConfiguration(models.Model):
    """
    Stores Baileys server connection settings.
    Only one record should exist (singleton pattern).
    """
    api_url = models.URLField(default='http://127.0.0.1:4001', help_text="Baileys Node.js server URL")
    webhook_secret = models.CharField(max_length=255, blank=True, default='', help_text="Shared secret for webhook verification")
    connected_phone = models.CharField(max_length=20, blank=True, default='', help_text="WhatsApp number connected via Baileys")
    is_connected = models.BooleanField(default=False)
    last_connected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'crm_whatsapp_config'
        verbose_name = 'WhatsApp Configuration'
        verbose_name_plural = 'WhatsApp Configuration'

    def __str__(self):
        status = "🟢 Connected" if self.is_connected else "🔴 Disconnected"
        return f"WhatsApp Config — {status}"

    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration."""
        config, _ = cls.objects.get_or_create(id=1, defaults={'api_url': 'http://127.0.0.1:4001'})
        return config
