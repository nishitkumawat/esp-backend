from django.urls import path
from . import views

urlpatterns = [
    path('stats', views.get_solar_stats, name='solar_stats'),
    path('latest', views.get_latest_solar_data, name='solar_latest'),
    # path('ping', views.ping_location, name='solar_ping'),
    # path('device/complete-setup', views.complete_setup, name='complete_setup'),
    path('location-ping/', views.save_device_location, name='save_device_location'),
]
