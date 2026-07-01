from django.shortcuts import render, redirect
from django.contrib import messages

from CRM.models import Tag, CRMUser, AuditLog
from CRM.decorators import crm_login_required, admin_required


@admin_required
def tag_list(request):
    """List and manage tags (Admin only)."""
    tags = Tag.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'create':
            name = request.POST.get('name', '').strip()
            color = request.POST.get('color', '#FFA500').strip()

            if not name:
                messages.error(request, 'Tag name is required.')
            elif Tag.objects.filter(name=name).exists():
                messages.error(request, 'Tag already exists.')
            else:
                Tag.objects.create(name=name, color=color)
                messages.success(request, f'Tag "{name}" created.')

        elif action == 'delete':
            tag_id = request.POST.get('tag_id', '')
            if tag_id:
                Tag.objects.filter(id=tag_id).delete()
                messages.success(request, 'Tag deleted.')

        return redirect('crm:tag_list')

    return render(request, 'crm/tags/list.html', {'tags': tags})


@admin_required
def user_list(request):
    """List and manage CRM users (Admin only)."""
    users = CRMUser.objects.all().order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action', '')
        user_id = request.POST.get('user_id', '')

        if action == 'toggle_active' and user_id:
            try:
                u = CRMUser.objects.get(id=user_id)
                u.is_active = not u.is_active
                u.save()
                status = 'activated' if u.is_active else 'deactivated'
                messages.success(request, f'User {u.name} {status}.')
            except CRMUser.DoesNotExist:
                messages.error(request, 'User not found.')

        elif action == 'change_role' and user_id:
            new_role = request.POST.get('role', '')
            try:
                u = CRMUser.objects.get(id=user_id)
                u.role = new_role
                u.save()
                messages.success(request, f'User {u.name} role changed to {u.get_role_display()}.')
            except CRMUser.DoesNotExist:
                messages.error(request, 'User not found.')

        return redirect('crm:user_list')

    return render(request, 'crm/users/list.html', {'users': users})
