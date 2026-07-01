from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from CRM.models import (
    CRMUser, WhatsAppContact, WhatsAppConversation, WhatsAppMessage, Lead, AuditLog
)
from CRM.decorators import crm_login_required


@crm_login_required
def chat_index(request):
    """WhatsApp-style chat interface."""
    user = CRMUser.objects.get(id=request.session['crm_user_id'])

    # Get all conversations with latest message
    conversations = WhatsAppConversation.objects.select_related(
        'contact', 'lead'
    ).order_by('-last_message_at')

    # Filter for sales exec — only show conversations linked conversation
    active_conversation_id = request.GET.get('conversation')
    active_conversation = None
    messages_list = []
    contact = None
    lead = None

    if active_conversation_id:
        active_conversation = get_object_or_404(
            WhatsAppConversation, id=active_conversation_id
        )
        messages_list = active_conversation.messages.select_related('sent_by').all()
        contact = active_conversation.contact
        lead = active_conversation.lead

        # Mark messages as read
        active_conversation.messages.filter(
            direction='incoming', is_read=False
        ).update(is_read=True)

    # Search
    search = request.GET.get('search', '')
    if search:
        conversations = conversations.filter(
            contact__name__icontains=search
        ) | conversations.filter(
            contact__phone__icontains=search
        )

    # Unread counts
    for conv in conversations:
        conv.unread_count = conv.messages.filter(
            direction='incoming', is_read=False
        ).count()
        conv.last_message = conv.messages.order_by('-timestamp').first()

    context = {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages_list': messages_list,
        'contact': contact,
        'lead': lead,
        'search': search,
    }
    return render(request, 'crm/chat/index.html', context)


@crm_login_required
@require_POST
def send_chat_message(request):
    """Send a message in chat (stored in DB, future Baileys dispatch)."""
    user = CRMUser.objects.get(id=request.session['crm_user_id'])
    conversation_id = request.POST.get('conversation_id')
    text = request.POST.get('message', '').strip()

    if not conversation_id or not text:
        return JsonResponse({'error': 'Missing data'}, status=400)

    conversation = get_object_or_404(WhatsAppConversation, id=conversation_id)

    msg = WhatsAppMessage.objects.create(
        conversation=conversation,
        text=text,
        direction='outgoing',
        sent_by=user,
    )
    conversation.last_message_at = timezone.now()
    conversation.save()

    # Update lead's last message date
    if conversation.lead:
        conversation.lead.last_message_at = timezone.now()
        conversation.lead.save(update_fields=['last_message_at'])

    AuditLog.objects.create(
        user=user,
        action='Message Sent',
        lead=conversation.lead,
        details=f'Sent message to {conversation.contact.phone}',
    )

    return JsonResponse({
        'status': 'ok',
        'message': {
            'id': msg.id,
            'text': msg.text,
            'direction': msg.direction,
            'sent_by': f'Mr. {user.name}',
            'timestamp': msg.timestamp.strftime('%d-%m-%Y %H:%M'),
        }
    })
