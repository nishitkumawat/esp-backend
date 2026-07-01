from .models import CRMUser


def crm_context(request):
    """Add CRM user and navigation data to all templates."""
    context = {}
    crm_user_id = request.session.get('crm_user_id')
    if crm_user_id:
        try:
            user = CRMUser.objects.get(id=crm_user_id, is_active=True)
            context['crm_user'] = user
            context['is_crm_admin'] = user.is_admin
        except CRMUser.DoesNotExist:
            pass
            
        # Add WhatsApp connection status
        try:
            from .models import WhatsAppConfiguration
            context['whatsapp_config'] = WhatsAppConfiguration.get_config()
        except Exception:
            pass
            
    return context
