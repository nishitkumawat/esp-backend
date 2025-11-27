from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup, name="iot-signup"),
    path("verify_signup_otp/", views.verify_signup_otp, name="iot-verify-signup-otp"),
    path("login/", views.login, name="iot-login"),
    path("forgot_password_send_otp/", views.forgot_password_send_otp, name="iot-forgot-password-send-otp"),
    path("verify_forgot_otp/", views.verify_forgot_otp, name="iot-verify-forgot-otp"),
    path("logout/", views.logout, name="iot-logout"),
    path("add_device/", views.add_device, name="iot-add-device"),
    path("my_devices/", views.my_devices, name="iot-my-devices"),
    path("rename_device/", views.rename_device, name="iot-rename-device"),
    path("change_admin/", views.change_admin, name="iot-change-admin"),
    path("control_device/", views.control_device, name="iot-control-device"),
    path("tester/", views.tester, name="iot-tester"),
    path("device_members/", views.device_members, name="iot-device-members"),
    path("pending_access_requests/", views.pending_access_requests, name="iot-pending-access-requests"),
    path("approve_access/", views.approve_access, name="iot-approve-access"),
    path("reject_access/", views.reject_access, name="iot-reject-access"),
    path("remove_access/", views.remove_access, name="iot-remove-access"),
    path("delete_device/", views.delete_device, name="iot-delete-device"),
    path("popup/", views.get_popup, name="iot-popup"),
    path("resend_signup_otp/", views.resend_signup_otp, name="resend-signup-otp"),
    path("resend_forgot_otp/", views.resend_forgot_otp, name="resend-forgot-otp"),
    
]
