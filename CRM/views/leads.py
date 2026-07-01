import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator

from CRM.models import Lead, Tag, Note, FollowUp, AuditLog, CRMUser
from CRM.decorators import crm_login_required


def _get_user(request):
    return CRMUser.objects.get(id=request.session['crm_user_id'])


def _log_action(user, action, lead=None, details=''):
    AuditLog.objects.create(user=user, action=action, lead=lead, details=details)


@crm_login_required
def lead_list(request):
    """List leads with filters, search, and pagination."""
    user = _get_user(request)

    leads = Lead.objects.all()

    section = request.GET.get('section', 'active')
    if section == 'closed':
        leads = leads.filter(status__in=['deal_closed', 'not_useful'])
    else:
        leads = leads.exclude(status__in=['deal_closed', 'not_useful'])

    # --- Filters ---
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    assigned_to = request.GET.get('assigned_to', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    tag_filter = request.GET.get('tag', '')

    if category:
        leads = leads.filter(category=category)
    if status:
        leads = leads.filter(status=status)
    if assigned_to:
        leads = leads.filter(assigned_to_id=assigned_to)
    if date_from:
        leads = leads.filter(created_at__date__gte=date_from)
    if date_to:
        leads = leads.filter(created_at__date__lte=date_to)
    if search:
        leads = leads.filter(Q(name__icontains=search) | Q(phone__icontains=search))
    if tag_filter:
        leads = leads.filter(tags__id=tag_filter)

    leads = leads.select_related('assigned_to').prefetch_related('tags')

    # --- Pagination ---
    paginator = Paginator(leads, 20)
    page = request.GET.get('page', 1)
    leads_page = paginator.get_page(page)

    # --- Context ---
    all_users = CRMUser.objects.filter(is_active=True)
    all_tags = Tag.objects.all()

    context = {
        'leads': leads_page,
        'all_users': all_users,
        'all_tags': all_tags,
        'filters': {
            'category': category,
            'status': status,
            'assigned_to': assigned_to,
            'date_from': date_from,
            'date_to': date_to,
            'search': search,
            'tag': tag_filter,
            'section': section,
        },
        'status_choices': Lead.STATUS_CHOICES,
        'category_choices': Lead.CATEGORY_CHOICES,
    }
    return render(request, 'crm/leads/list.html', context)


@crm_login_required
def lead_create(request):
    """Create a new lead."""
    user = _get_user(request)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        category = request.POST.get('category', '')
        status = request.POST.get('status', 'new')
        assigned_to_id = request.POST.get('assigned_to', '')
        source = request.POST.get('source', 'whatsapp')
        remarks = request.POST.get('remarks', '').strip()
        follow_up_date = request.POST.get('follow_up_date', '')
        tag_ids = request.POST.getlist('tags')

        # Validation
        errors = []
        if not name:
            errors.append('Lead name is required.')
        if not phone:
            errors.append('Phone number is required.')
        if not category:
            errors.append('Category is required.')

        if errors:
            for error in errors:
                messages.error(request, error)
            all_users = CRMUser.objects.filter(is_active=True)
            all_tags = Tag.objects.all()
            return render(request, 'crm/leads/form.html', {
                'all_users': all_users,
                'all_tags': all_tags,
                'form_data': request.POST,
                'is_edit': False,
                'status_choices': Lead.STATUS_CHOICES,
                'category_choices': Lead.CATEGORY_CHOICES,
                'source_choices': Lead.SOURCE_CHOICES,
            })

        lead = Lead(
            name=name,
            phone=phone,
            category=category,
            status=status,
            source=source,
            remarks=remarks,
        )
        if assigned_to_id:
            lead.assigned_to_id = int(assigned_to_id)
        elif not user.is_admin:
            lead.assigned_to = user
        if follow_up_date:
            lead.follow_up_date = follow_up_date

        lead.save()

        if tag_ids:
            lead.tags.set(tag_ids)

        _log_action(user, 'Lead Created', lead, f'Created lead: {name}')
        messages.success(request, f'Lead "{name}" created successfully.')
        return redirect('crm:lead_detail', lead_id=lead.id)

    all_users = CRMUser.objects.filter(is_active=True)
    all_tags = Tag.objects.all()

    return render(request, 'crm/leads/form.html', {
        'all_users': all_users,
        'all_tags': all_tags,
        'is_edit': False,
        'status_choices': Lead.STATUS_CHOICES,
        'category_choices': Lead.CATEGORY_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
    })


@crm_login_required
def lead_detail(request, lead_id):
    """Lead detail with tabs: details, notes, follow-ups, activity."""
    user = _get_user(request)
    lead = get_object_or_404(Lead, id=lead_id)



    notes = lead.notes.select_related('user').all()
    followups = lead.followups.select_related('assigned_to').all()
    activity = lead.audit_logs.select_related('user').all()[:20]
    all_tags = Tag.objects.all()
    all_users = CRMUser.objects.filter(is_active=True)

    context = {
        'lead': lead,
        'notes': notes,
        'followups': followups,
        'activity': activity,
        'all_tags': all_tags,
        'all_users': all_users,
        'status_choices': Lead.STATUS_CHOICES,
        'category_choices': Lead.CATEGORY_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
    }
    return render(request, 'crm/leads/detail.html', context)


@crm_login_required
def lead_edit(request, lead_id):
    """Edit a lead."""
    user = _get_user(request)
    lead = get_object_or_404(Lead, id=lead_id)



    if request.method == 'POST':
        old_status = lead.status
        old_assigned = lead.assigned_to

        lead.name = request.POST.get('name', lead.name).strip()
        lead.phone = request.POST.get('phone', lead.phone).strip()
        lead.category = request.POST.get('category', lead.category)
        lead.status = request.POST.get('status', lead.status)
        lead.source = request.POST.get('source', lead.source)
        lead.remarks = request.POST.get('remarks', lead.remarks).strip()

        assigned_to_id = request.POST.get('assigned_to', '')
        if assigned_to_id:
            lead.assigned_to_id = int(assigned_to_id)
        else:
            lead.assigned_to = None

        follow_up_date = request.POST.get('follow_up_date', '')
        lead.follow_up_date = follow_up_date if follow_up_date else None

        tag_ids = request.POST.getlist('tags')
        lead.save()
        lead.tags.set(tag_ids)

        # Audit logs for changes
        if old_status != lead.status:
            old_label = dict(Lead.STATUS_CHOICES).get(old_status, old_status)
            new_label = dict(Lead.STATUS_CHOICES).get(lead.status, lead.status)
            _log_action(user, 'Status Changed', lead, f'{old_label} → {new_label}')

        if old_assigned != lead.assigned_to:
            _log_action(user, 'User Assigned', lead,
                        f'Assigned to {lead.assigned_to.name if lead.assigned_to else "Unassigned"}')

        _log_action(user, 'Lead Updated', lead, f'Updated lead: {lead.name}')
        messages.success(request, f'Lead "{lead.name}" updated successfully.')
        return redirect('crm:lead_detail', lead_id=lead.id)

    all_users = CRMUser.objects.filter(is_active=True)
    all_tags = Tag.objects.all()

    return render(request, 'crm/leads/form.html', {
        'lead': lead,
        'all_users': all_users,
        'all_tags': all_tags,
        'is_edit': True,
        'status_choices': Lead.STATUS_CHOICES,
        'category_choices': Lead.CATEGORY_CHOICES,
        'source_choices': Lead.SOURCE_CHOICES,
    })


@crm_login_required
def lead_delete(request, lead_id):
    """Delete a lead."""
    user = _get_user(request)
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == 'POST':
        lead.delete()
        messages.success(request, f'Lead "{lead.name}" deleted successfully.')
        return redirect('crm:lead_list')

    return redirect('crm:lead_detail', lead_id=lead.id)


@crm_login_required
def lead_add_note(request, lead_id):
    """Add a note to a lead."""
    user = _get_user(request)
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            Note.objects.create(lead=lead, user=user, content=content)
            _log_action(user, 'Note Added', lead, f'Added note to Lead #{lead.id}')
            messages.success(request, 'Note added successfully.')
        else:
            messages.error(request, 'Note content cannot be empty.')

    return redirect('crm:lead_detail', lead_id=lead.id)


@crm_login_required
def lead_add_followup(request, lead_id):
    """Add a follow-up to a lead."""
    user = _get_user(request)
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == 'POST':
        date = request.POST.get('followup_date', '')
        time = request.POST.get('followup_time', '')
        remarks = request.POST.get('followup_remarks', '').strip()

        if date and time:
            FollowUp.objects.create(
                lead=lead,
                assigned_to=user,
                date=date,
                time=time,
                remarks=remarks,
            )
            _log_action(user, 'Follow-Up Added', lead, f'Follow-up scheduled for {date} {time}')
            messages.success(request, 'Follow-up added successfully.')
        else:
            messages.error(request, 'Date and time are required.')

    return redirect('crm:lead_detail', lead_id=lead.id)


@crm_login_required
def lead_add_tag(request, lead_id):
    """Add tags to a lead."""
    user = _get_user(request)
    lead = get_object_or_404(Lead, id=lead_id)

    if request.method == 'POST':
        tag_ids = request.POST.getlist('tags')
        if tag_ids:
            lead.tags.add(*tag_ids)
            _log_action(user, 'Tag Added', lead, f'Tags updated for Lead #{lead.id}')
            messages.success(request, 'Tags updated.')
        else:
            messages.error(request, 'No tags selected.')

    return redirect('crm:lead_detail', lead_id=lead.id)


@crm_login_required
def lead_bulk_action(request):
    """Handle bulk actions: change status, assign user, export."""
    user = _get_user(request)

    if request.method == 'POST':
        lead_ids = request.POST.getlist('lead_ids')
        action = request.POST.get('bulk_action', '')

        if not lead_ids:
            messages.error(request, 'No leads selected.')
            return redirect('crm:lead_list')

        leads = Lead.objects.filter(id__in=lead_ids)

        if action == 'change_status':
            new_status = request.POST.get('bulk_status', '')
            if new_status:
                leads.update(status=new_status)
                for lead in leads:
                    _log_action(user, 'Status Changed (Bulk)', lead, f'Bulk status change to {new_status}')
                messages.success(request, f'{len(lead_ids)} leads updated.')

        elif action == 'assign_user':
            new_user_id = request.POST.get('bulk_user', '')
            if new_user_id:
                leads.update(assigned_to_id=int(new_user_id))
                assign_user = CRMUser.objects.get(id=new_user_id)
                for lead in leads:
                    _log_action(user, 'User Assigned (Bulk)', lead, f'Assigned to {assign_user.name}')
                messages.success(request, f'{len(lead_ids)} leads assigned.')

        elif action == 'export':
            return _export_leads_csv(leads)

    return redirect('crm:lead_list')


def _export_leads_csv(leads):
    """Export leads to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leads_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Phone', 'Category', 'Status', 'Assigned To',
        'Source', 'Remarks', 'Follow-Up Date', 'Created Date'
    ])

    for lead in leads.select_related('assigned_to'):
        writer.writerow([
            lead.id,
            lead.name,
            lead.phone,
            lead.get_category_display(),
            lead.get_status_display(),
            lead.assigned_to.name if lead.assigned_to else '',
            lead.get_source_display(),
            lead.remarks,
            lead.follow_up_date or '',
            lead.created_at.strftime('%Y-%m-%d %H:%M'),
        ])

    return response


@crm_login_required
def solar_leads(request):
    """Solar Structure leads shortcut."""
    request.GET = request.GET.copy()
    request.GET['category'] = 'solar_structure'
    return lead_list(request)


@crm_login_required
def machine_leads(request):
    """Roll Forming Machine leads shortcut."""
    request.GET = request.GET.copy()
    request.GET['category'] = 'roll_forming_machine'
    return lead_list(request)
