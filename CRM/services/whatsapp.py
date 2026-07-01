"""
WhatsApp Service Layer for EZRun CRM
=====================================

This module is the complete Django-side integration point for WhatsApp via Baileys.

Architecture:
    Customer → WhatsApp → Baileys (Node.js) → POST /crm/api/webhook/whatsapp/ → Django CRM

Sending messages:
    Django CRM → POST http://127.0.0.1:4001/send → Baileys → WhatsApp → Customer
"""

import logging
from datetime import datetime

import requests as http_requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('crm.whatsapp')

# ── Baileys Gateway connection ──────────────────
BAILEYS_URL = getattr(settings, 'WHATSAPP_API_URL', 'http://127.0.0.1:4001')
BAILEYS_KEY = getattr(settings, 'WHATSAPP_API_KEY', 'EZRUN_SECRET_2026')
BAILEYS_HEADERS = {'X-API-KEY': BAILEYS_KEY, 'Content-Type': 'application/json'}
BAILEYS_TIMEOUT = 10  # seconds


# ============================================================
# BOT FLOW MESSAGE TEMPLATES
# ============================================================
MSG_WELCOME = (
    "👋 *Welcome to EZRun!*\n\n"
    "Please select your requirement:\n\n"
    "1️⃣  Solar Structure\n"
    "2️⃣  Roll Forming Machine\n\n"
    "Reply with *1* or *2*."
)

MSG_SOLAR_PROMPT = (
    "Thank you for your interest in *Solar Structure*!\n\n"
    "Please share your project details:\n\n"
    "📐 *Size*\n"
    "🔩 *Material / Coating* (e.g., GI, Aluminium)\n"
    "📏 *Dimension*\n\n"
    "You can send all details in one message."
)

MSG_MACHINE_PROMPT = (
    "Thank you for your interest in *Roll Forming Machine*!\n\n"
    "Please share your requirements:\n\n"
    "⚙️ *Type of profile* (e.g. C purlin,Hat purlin)\n"
    "📍 *Location*\n\n"
    "You can send all details in one message."
)

MSG_COMPLETED = (
    "✅ *Thank you!*\n\n"
    "Your inquiry has been registered. Our sales team will contact you shortly.\n\n"
    "For urgent queries, call us directly."
)

MSG_UNRECOGNIZED = (
    "Sorry, I didn't understand that.\n\n"
    "Please reply with *1* for Solar Structure or *2* for Roll Forming Machine."
)


# ============================================================
# CORE SERVICE FUNCTIONS
# ============================================================

def receive_message(payload: dict) -> dict:
    """
    Process an incoming WhatsApp message from the Baileys webhook.

    Called by: POST /crm/api/webhook/whatsapp/

    Args:
        payload (dict): {
            'phone': '919876543210',
            'name': 'Customer Name',
            'message': 'Hello',
            'message_id': 'BAILEYS_MSG_ID',
            'timestamp': '2026-06-18T12:00:00Z'  (optional)
        }

    Returns:
        dict: {'contact': ..., 'conversation': ..., 'message': ...}
    """
    # Import here to avoid circular imports
    from CRM.models import (
        WhatsAppContact, WhatsAppConversation, WhatsAppMessage,
        AuditLog, ChatState
    )

    phone = payload.get('phone', '').strip()
    name = payload.get('name', '').strip()
    message_text = payload.get('message', '').strip()
    message_id = payload.get('message_id', '')

    # 1. Get or create contact
    contact, created = WhatsAppContact.objects.get_or_create(
        phone=phone,
        defaults={'name': name}
    )
    if name and not contact.name:
        contact.name = name
        contact.save(update_fields=['name'])

    # 2. Get or create conversation
    conversation = WhatsAppConversation.objects.filter(contact=contact).first()
    if not conversation:
        conversation = WhatsAppConversation.objects.create(contact=contact)

    # 3. Save incoming message
    msg = WhatsAppMessage.objects.create(
        conversation=conversation,
        text=message_text,
        direction='incoming',
        message_id=message_id or None,
        delivery_status='delivered',
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=['last_message_at'])

    # 4. Log to audit
    lead = conversation.lead
    if lead:
        AuditLog.objects.create(
            action='Message Received',
            lead=lead,
            details=f"Received from {phone}: {message_text.encode('ascii', 'ignore').decode('ascii')[:100]}",
        )
        log_timeline_event(
            lead=lead,
            event_type='message_received',
            description=f"Customer sent: {message_text.encode('ascii', 'ignore').decode('ascii')[:200]}",
        )
        if lead.last_message_at is None or lead.last_message_at < timezone.now():
            lead.last_message_at = timezone.now()
            lead.save(update_fields=['last_message_at'])

    # 5. Process chatbot state machine
    process_bot_flow(phone=phone, text=message_text, contact=contact, conversation=conversation)

    return {'contact': contact, 'conversation': conversation, 'message': msg}


def process_bot_flow(phone: str, text: str, contact, conversation) -> None:
    """
    State-machine based chatbot flow. Uses ChatState model exclusively.
    Never uses message count logic.

    States:
        start              → Send welcome message, move to waiting_category
        waiting_category   → User picks 1 or 2, create lead, move to waiting_solar_details
                             or waiting_machine_details
        waiting_solar_details  → Collect details, mark completed
        waiting_machine_details → Collect details, mark completed
        completed          → No auto-reply (sales team takes over)

    Args:
        phone (str): Customer phone number
        text (str): The message text
        contact (WhatsAppContact): Contact instance
        conversation (WhatsAppConversation): Conversation instance
    """
    from CRM.models import ChatState

    state_obj, _ = ChatState.objects.get_or_create(
        phone=phone,
        defaults={'current_state': 'start'}
    )
    current_state = state_obj.current_state
    text_clean = text.strip()

    if current_state == 'start':
        # Send welcome, ask for category
        _send_bot_message(phone, MSG_WELCOME, conversation)
        state_obj.current_state = 'waiting_category'
        state_obj.save()

    elif current_state == 'waiting_category':
        if text_clean == '1':
            # Solar Structure chosen
            _send_bot_message(phone, MSG_SOLAR_PROMPT, conversation)
            state_obj.current_state = 'waiting_solar_details'
            state_obj.context_data = {'category': 'solar_structure'}
            state_obj.save()

        elif text_clean == '2':
            # Roll Forming Machine chosen
            _send_bot_message(phone, MSG_MACHINE_PROMPT, conversation)
            state_obj.current_state = 'waiting_machine_details'
            state_obj.context_data = {'category': 'roll_forming_machine'}
            state_obj.save()

        else:
            # Unrecognized input — resend welcome
            _send_bot_message(phone, MSG_UNRECOGNIZED, conversation)

    elif current_state in ('waiting_solar_details', 'waiting_machine_details'):
        # Customer provided their project details → create/update lead
        category = state_obj.context_data.get('category', 'solar_structure')
        lead = create_lead_from_whatsapp(contact=contact, category=category, details=text_clean, conversation=conversation)
        _send_bot_message(phone, MSG_COMPLETED, conversation)
        state_obj.current_state = 'completed'
        state_obj.context_data['details'] = text_clean
        state_obj.save()

        # Link conversation to lead
        if lead and not conversation.lead:
            conversation.lead = lead
            conversation.save(update_fields=['lead'])

    elif current_state == 'completed':
        # Sales team handles from here — no auto-reply
        logger.info(f"[BOT] State completed for {phone}. No auto-reply.")


def create_lead_from_whatsapp(contact, category: str, details: str = '', conversation=None):
    """
    Create a new lead from a WhatsApp contact with duplicate protection.
    If a lead for this phone already exists, reuse it (reopen if closed).

    Args:
        contact (WhatsAppContact): WhatsApp contact instance
        category (str): 'solar_structure' or 'roll_forming_machine'
        details (str): Customer's project details
        conversation: WhatsAppConversation instance

    Returns:
        Lead: The created or reused lead
    """
    from CRM.models import Lead, AuditLog

    # --- Duplicate Protection ---
    existing_lead = Lead.objects.filter(phone=contact.phone).first()

    if existing_lead:
        reopened = False
        if existing_lead.status in ('deal_closed', 'not_useful'):
            existing_lead.status = 'new'
            reopened = True

        if details:
            existing_lead.remarks = (existing_lead.remarks + f"\n\n[New Inquiry]: {details}").strip()
        existing_lead.last_message_at = timezone.now()
        existing_lead.save()

        log_timeline_event(
            lead=existing_lead,
            event_type='message_received',
            description=f"{'Reopened lead.' if reopened else 'New message from existing lead.'} Details: {details[:200]}",
        )
        AuditLog.objects.create(
            action='Lead Reopened' if reopened else 'Existing Lead Updated',
            lead=existing_lead,
            details=f"Phone: {contact.phone}. Details: {details[:100]}",
        )
        logger.info(f"[LEAD] Reused existing lead #{existing_lead.id} for {contact.phone}")
        return existing_lead

    # --- Create New Lead ---
    assigned_user = assign_next_sales_user()
    lead = Lead.objects.create(
        name=contact.name or contact.phone,
        phone=contact.phone,
        category=category,
        status='new',
        source='whatsapp',
        remarks=details,
        assigned_to=assigned_user,
        last_message_at=timezone.now(),
    )

    # Update contact category
    contact.category = category
    contact.save(update_fields=['category'])

    # Audit log
    AuditLog.objects.create(
        action='Lead Created (Auto)',
        lead=lead,
        details=f"Auto-created from WhatsApp. Phone: {contact.phone}. Category: {category}",
    )

    # Timeline events
    log_timeline_event(lead, 'lead_created', f"Lead auto-created from WhatsApp inquiry.")
    log_timeline_event(lead, 'category_selected', f"Customer selected: {lead.get_category_display()}")
    if assigned_user:
        log_timeline_event(lead, 'user_assigned', f"Auto-assigned to {assigned_user.name} (round-robin)")

    logger.info(f"[LEAD] Created new lead #{lead.id} for {contact.phone} -> {category}")
    return lead


def assign_next_sales_user():
    """
    Round-robin auto-assignment to the next available Sales Executive.
    Picks the active sales exec with the fewest currently assigned leads.

    Returns:
        CRMUser or None
    """
    from CRM.models import CRMUser
    from django.db.models import Count

    sales_execs = (
        CRMUser.objects
        .filter(role='sales_executive', is_active=True)
        .annotate(lead_count=Count('assigned_leads'))
        .order_by('lead_count', 'id')
    )

    if not sales_execs.exists():
        logger.warning("[ASSIGN] No active sales executives found for auto-assignment.")
        return None

    return sales_execs.first()


def send_message(phone: str, text: str, sent_by_user=None, lead=None) -> bool:
    """
    Send a WhatsApp message to a customer.
    Saves the message to DB and dispatches to the Baileys gateway.

    Args:
        phone (str): Recipient phone number (with country code)
        text (str): Message text
        sent_by_user (CRMUser, optional): CRM user sending the message
        lead (Lead, optional): Associated lead for timeline logging

    Returns:
        bool: True on success
    """
    from CRM.models import WhatsAppContact, WhatsAppConversation, WhatsAppMessage, AuditLog

    try:
        contact, _ = WhatsAppContact.objects.get_or_create(phone=phone)
        conversation = WhatsAppConversation.objects.filter(contact=contact).first()
        if not conversation:
            conversation = WhatsAppConversation.objects.create(contact=contact)

        msg = WhatsAppMessage.objects.create(
            conversation=conversation,
            text=text,
            direction='outgoing',
            sent_by=sent_by_user,
            delivery_status='pending',
        )
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        # Audit log
        if lead:
            AuditLog.objects.create(
                user=sent_by_user,
                action='Message Sent',
                lead=lead,
                details=f"Sent to {phone}: {text.encode('ascii', 'ignore').decode('ascii')[:100]}",
            )
            log_timeline_event(
                lead=lead,
                event_type='message_sent',
                description=f"Sent: {text.encode('ascii', 'ignore').decode('ascii')[:200]}",
                user=sent_by_user,
            )

        # ── Dispatch to Baileys gateway ─────────────────────
        try:
            resp = http_requests.post(
                f"{BAILEYS_URL}/send",
                json={'phone': phone, 'message': text},
                headers=BAILEYS_HEADERS,
                timeout=BAILEYS_TIMEOUT,
            )
            data = resp.json()
            if resp.status_code == 200 and data.get('success'):
                msg.message_id = data.get('message_id', '')
                msg.delivery_status = 'sent'
                msg.save(update_fields=['delivery_status', 'message_id'])
                logger.info(f"[SEND] Sent to {phone}, msg_id={msg.message_id}")
                return True
            else:
                msg.delivery_status = 'failed'
                msg.save(update_fields=['delivery_status'])
                logger.warning(f"[SEND] Baileys returned error for {phone}: {data}")
                return False
        except http_requests.RequestException as e:
            msg.delivery_status = 'failed'
            msg.save(update_fields=['delivery_status'])
            logger.error(f"[SEND] Baileys unreachable for {phone}: {e}")
            return False

    except Exception as e:
        logger.error(f"[SEND] Error sending message to {phone}: {e}")
        return False


def check_whatsapp_status() -> dict:
    """
    Check if the Baileys server is connected.
    Polls the Node.js gateway and updates the local WhatsAppConfiguration.

    Returns:
        dict: {'connected': bool, 'phone': str, 'name': str, 'last_seen': str, 'api_url': str}
    """
    from CRM.models import WhatsAppConfiguration

    config = WhatsAppConfiguration.get_config()

    try:
        resp = http_requests.get(
            f"{BAILEYS_URL}/status",
            headers=BAILEYS_HEADERS,
            timeout=5,
        )
        data = resp.json()
        config.is_connected = data.get('connected', False)
        config.connected_phone = data.get('phone', '') or ''
        if config.is_connected:
            config.last_connected_at = timezone.now()
        config.save()
    except http_requests.RequestException as e:
        logger.error(f"[STATUS] Baileys unreachable: {e}")
        config.is_connected = False
        config.save()

    return {
        'connected': config.is_connected,
        'phone': config.connected_phone,
        'name': data.get('name', '') if 'data' in dir() else '',
        'last_seen': config.last_connected_at.isoformat() if config.last_connected_at else None,
        'api_url': BAILEYS_URL,
    }


def log_timeline_event(lead, event_type: str, description: str, user=None) -> None:
    """
    Helper: Create a LeadTimeline event.

    Args:
        lead (Lead): The lead to log against
        event_type (str): One of LeadTimeline.EVENT_CHOICES keys
        description (str): Human-readable description
        user (CRMUser, optional): Who triggered the event
    """
    from CRM.models import LeadTimeline
    try:
        LeadTimeline.objects.create(
            lead=lead,
            event_type=event_type,
            description=description,
            created_by=user,
        )
    except Exception as e:
        logger.error(f"[TIMELINE] Failed to log event for lead #{lead.id}: {e}")


# ============================================================
# PRIVATE HELPERS
# ============================================================

def _send_bot_message(phone: str, text: str, conversation) -> None:
    """Internal: Save a bot outgoing message and dispatch via Baileys."""
    from CRM.models import WhatsAppMessage
    msg = WhatsAppMessage.objects.create(
        conversation=conversation,
        text=text,
        direction='outgoing',
        delivery_status='pending',
    )
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=['last_message_at'])

    # Dispatch through Baileys gateway
    try:
        resp = http_requests.post(
            f"{BAILEYS_URL}/send",
            json={'phone': phone, 'message': text},
            headers=BAILEYS_HEADERS,
            timeout=BAILEYS_TIMEOUT,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get('success'):
            msg.message_id = data.get('message_id', '')
            msg.delivery_status = 'sent'
            msg.save(update_fields=['delivery_status', 'message_id'])
            logger.info(f"[BOT -> {phone}] Sent: {text.encode('ascii', 'ignore').decode('ascii')[:80]}")
        else:
            msg.delivery_status = 'failed'
            msg.save(update_fields=['delivery_status'])
            logger.warning(f"[BOT -> {phone}] Baileys error: {data}")
    except http_requests.RequestException as e:
        msg.delivery_status = 'failed'
        msg.save(update_fields=['delivery_status'])
        logger.error(f"[BOT -> {phone}] Baileys unreachable: {e}")
