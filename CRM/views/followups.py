from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from CRM.models import FollowUp, Lead, CRMUser, AuditLog
from CRM.decorators import crm_login_required


@crm_login_required
def followup_list(request):
    """List all follow-ups with filters."""
    user = CRMUser.objects.get(id=request.session['crm_user_id'])
    today = timezone.now().date()

    followups = FollowUp.objects.all()

    # Auto-mark overdue
    followups.filter(date__lt=today, status='pending').update(status='overdue')

    # Filters
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    if status_filter:
        followups = followups.filter(status=status_filter)
    if date_filter:
        followups = followups.filter(date=date_filter)

    followups = followups.select_related('lead', 'assigned_to').order_by('date', 'time')

    # Grouped
    today_followups = followups.filter(date=today, status__in=['pending', 'overdue'])
    overdue_followups = followups.filter(date__lt=today, status='overdue')
    upcoming_followups = followups.filter(date__gt=today, status='pending')
    completed_followups = followups.filter(status='completed').order_by('-date')[:20]

    context = {
        'today_followups': today_followups,
        'overdue_followups': overdue_followups,
        'upcoming_followups': upcoming_followups,
        'completed_followups': completed_followups,
        'status_filter': status_filter,
        'date_filter': date_filter,
    }
    return render(request, 'crm/followups/list.html', context)


@crm_login_required
def followup_complete(request, followup_id):
    """Mark a follow-up as completed."""
    user = CRMUser.objects.get(id=request.session['crm_user_id'])
    followup = get_object_or_404(FollowUp, id=followup_id)

    followup.status = 'completed'
    followup.save()

    AuditLog.objects.create(
        user=user,
        action='Follow-Up Completed',
        lead=followup.lead,
        details=f'Follow-up marked as completed',
    )
    messages.success(request, 'Follow-up marked as completed.')
    return redirect('crm:followup_list')
