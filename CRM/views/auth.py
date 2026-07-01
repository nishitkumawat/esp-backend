from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from CRM.models import CRMUser


def login_view(request):
    """CRM Login — Mobile + 4-digit PIN."""
    if request.session.get('crm_user_id'):
        return redirect('crm:dashboard')

    if request.method == 'POST':
        mobile = request.POST.get('mobile', '').strip()
        pin = request.POST.get('pin', '').strip()

        if not mobile or not pin:
            messages.error(request, 'Please enter mobile number and PIN.')
            return render(request, 'crm/auth/login.html')

        try:
            user = CRMUser.objects.get(mobile=mobile, is_active=True)
        except CRMUser.DoesNotExist:
            messages.error(request, 'Invalid mobile number or PIN.')
            return render(request, 'crm/auth/login.html')

        if user.check_pin(pin):
            # Set session
            request.session['crm_user_id'] = user.id
            request.session.set_expiry(86400 * 30)  # 30 days
            # Update last login
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            return redirect('crm:dashboard')
        else:
            messages.error(request, 'Invalid mobile number or PIN.')

    return render(request, 'crm/auth/login.html')


def signup_view(request):
    """CRM Signup — Name, Mobile, PIN."""
    if request.session.get('crm_user_id'):
        return redirect('crm:dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        pin = request.POST.get('pin', '').strip()
        confirm_pin = request.POST.get('confirm_pin', '').strip()

        # Validation
        errors = []
        if not name:
            errors.append('Full name is required.')
        if not mobile:
            errors.append('Mobile number is required.')
        if not pin or len(pin) != 4 or not pin.isdigit():
            errors.append('PIN must be exactly 4 digits.')
        if pin != confirm_pin:
            errors.append('PINs do not match.')
        if CRMUser.objects.filter(mobile=mobile).exists():
            errors.append('This mobile number is already registered.')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'crm/auth/signup.html', {
                'form_data': {'name': name, 'mobile': mobile}
            })

        # Create user
        user = CRMUser(name=name, mobile=mobile, role='sales_executive')
        user.set_pin(pin)
        user.save()

        messages.success(request, 'Account created successfully! Please login.')
        return redirect('crm:login')

    return render(request, 'crm/auth/signup.html')


def logout_view(request):
    """CRM Logout — Clear session."""
    request.session.pop('crm_user_id', None)
    request.session.flush()
    messages.success(request, 'You have been logged out.')
    return redirect('crm:login')
