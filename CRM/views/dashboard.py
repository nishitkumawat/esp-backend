from django.shortcuts import render
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from CRM.models import Lead, FollowUp, AuditLog, WhatsAppConversation, CRMUser
from CRM.decorators import crm_login_required


@crm_login_required
def dashboard(request):
    """Main CRM dashboard with stats, charts, and recent activity."""
    user = CRMUser.objects.get(id=request.session['crm_user_id'])
    today = timezone.now().date()

    # ---------- Lead Counts ----------
    leads_qs = Lead.objects.all()

    total_leads = leads_qs.count()
    new_leads = leads_qs.filter(status='new').count()
    to_quote = leads_qs.filter(status='to_quote').count()
    quote_sent = leads_qs.filter(status='quote_sent').count()
    future_leads = leads_qs.filter(status='future_lead').count()
    deal_closed = leads_qs.filter(status='deal_closed').count()
    not_useful = leads_qs.filter(status='not_useful').count()

    # ---------- Recent Leads ----------
    recent_leads = leads_qs.select_related('assigned_to')[:10]

    # ---------- Follow-Ups ----------
    followups_qs = FollowUp.objects.all()

    today_followups = followups_qs.filter(date=today, status='pending').select_related('lead', 'assigned_to')[:10]
    overdue_followups = followups_qs.filter(date__lt=today, status='pending').select_related('lead', 'assigned_to')[:10]
    upcoming_followups = followups_qs.filter(date__gt=today, status='pending').select_related('lead', 'assigned_to')[:10]

    # ---------- Recent Conversations ----------
    recent_conversations = WhatsAppConversation.objects.select_related(
        'contact', 'lead'
    ).order_by('-last_message_at')[:10]

    # ---------- Activity Feed (Admin only) ----------
    if user.is_admin:
        activity_feed = AuditLog.objects.select_related('user', 'lead')[:15]
    else:
        activity_feed = AuditLog.objects.filter(user=user).select_related('user', 'lead')[:15]

    # ---------- Chart Data ----------
    # Status distribution
    status_data = list(
        leads_qs.values('status').annotate(count=Count('id')).order_by('status')
    )

    # Monthly leads (last 6 months)
    six_months_ago = today - timedelta(days=180)
    monthly_data = list(
        leads_qs.filter(created_at__date__gte=six_months_ago)
        .extra(select={'month': "DATE_FORMAT(created_at, '%%Y-%%m')"})
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Category data
    category_data = list(
        leads_qs.values('category').annotate(count=Count('id'))
    )

    context = {
        'total_leads': total_leads,
        'new_leads': new_leads,
        'to_quote': to_quote,
        'quote_sent': quote_sent,
        'future_leads': future_leads,
        'deal_closed': deal_closed,
        'not_useful': not_useful,
        'recent_leads': recent_leads,
        'today_followups': today_followups,
        'overdue_followups': overdue_followups,
        'upcoming_followups': upcoming_followups,
        'recent_conversations': recent_conversations,
        'activity_feed': activity_feed,
        'status_data': status_data,
        'monthly_data': monthly_data,
        'category_data': category_data,
    }
    return render(request, 'crm/dashboard/index.html', context)
