from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from . import views

urlpatterns = [
    path('stats', views.get_solar_stats, name='solar_stats'),
    path('ping', views.ping_location, name='solar_ping'),
    path('device/complete-setup', views.complete_setup, name='complete_setup'),
    path('api/device/location', csrf_exempt(views.save_device_location), name='save_device_location'),
]
