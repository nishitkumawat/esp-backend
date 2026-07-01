import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from CRM.models import (
    Lead, CRMUser, AuditLog, WhatsAppConversation, WhatsAppMessage
)
from CRM.services.whatsapp import receive_message, check_whatsapp_status, send_message


def api_chart_data(request):
    """API endpoint for dashboard chart data."""
    if not request.session.get('crm_user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    user = CRMUser.objects.get(id=request.session['crm_user_id'])

    if user.is_admin:
        leads = Lead.objects.all()
    else:
        leads = Lead.objects.filter(assigned_to=user)

    # Status distribution
    from django.db.models import Count
    status_data = list(
        leads.values('status').annotate(count=Count('id')).order_by('status')
    )

    # Category data
    category_data = list(
        leads.values('category').annotate(count=Count('id'))
    )

    return JsonResponse({
        'status_data': status_data,
        'category_data': category_data,
    })


def api_chat_messages(request, conversation_id):
    """API: Get messages for a conversation."""
    if not request.session.get('crm_user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        conversation = WhatsAppConversation.objects.get(id=conversation_id)
    except WhatsAppConversation.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

    msgs = conversation.messages.select_related('sent_by').order_by('timestamp')
    data = []
    for m in msgs:
        data.append({
            'id': m.id,
            'text': m.text,
            'direction': m.direction,
            'sent_by': f'Mr. {m.sent_by.name}' if m.sent_by else None,
            'timestamp': m.timestamp.strftime('%d-%m-%Y %H:%M'),
            'is_read': m.is_read,
        })

    return JsonResponse({'messages': data})


@csrf_exempt
@require_POST
def whatsapp_webhook(request):
    """
    Webhook endpoint for Baileys integration.

    Expected POST body:
    {
        "phone": "919876543210",
        "message": "Hello",
        "name": "Customer Name",
        "message_id": "BAILEYS_MSG_ID",
        "timestamp": "2026-01-01T00:00:00Z"
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    phone = data.get('phone', '')
    message = data.get('message', '')

    if not phone or not message:
        return JsonResponse({'error': 'phone and message are required'}, status=400)

    # Pass the full payload dict — receive_message() expects it
    result = receive_message(data)

    return JsonResponse({
        'status': 'ok',
        'contact_id': result['contact'].id,
        'conversation_id': result['conversation'].id,
        'message_id': result['message'].id,
    })


@csrf_exempt
@require_POST
def send_message_api(request):
    """
    API for CRM to send a message via Baileys.
    """
    if not request.session.get('crm_user_id'):
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    phone = data.get('phone', '')
    message = data.get('message', '')

    if not phone or not message:
        return JsonResponse({'error': 'phone and message are required'}, status=400)

    user = CRMUser.objects.get(id=request.session['crm_user_id'])
    
    success = send_message(phone=phone, text=message, sent_by_user=user)

    if success:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Failed to send message'}, status=500)


def whatsapp_status_api(request):
    """
    API to check Baileys connection status.
    """
    status_data = check_whatsapp_status()
    return JsonResponse(status_data)
