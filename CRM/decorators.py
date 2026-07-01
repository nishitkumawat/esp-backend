from functools import wraps
from django.shortcuts import redirect


def crm_login_required(view_func):
    """Decorator: Requires CRM user to be logged in."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('crm_user_id'):
            return redirect('crm:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_required(view_func):
    """Decorator: Requires CRM user to be an admin."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('crm_user_id'):
            return redirect('crm:login')
        from .models import CRMUser
        try:
            user = CRMUser.objects.get(id=request.session['crm_user_id'], is_active=True)
        except CRMUser.DoesNotExist:
            request.session.flush()
            return redirect('crm:login')
        if not user.is_admin:
            return redirect('crm:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
