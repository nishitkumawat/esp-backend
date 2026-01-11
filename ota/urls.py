from django.urls import path
from . import views

urlpatterns = [
    path("ota/<str:device_id>/", views.ota_check),
    path("ota/<str:device_id>/status/", views.ota_status),
]
