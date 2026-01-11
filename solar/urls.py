from django.urls import path
from . import views

urlpatterns = [
    path('stats', views.get_solar_stats, name='solar_stats'),
]
