from django.urls import path
from . import views

app_name = 'sells'

urlpatterns = [
    # Public invoice routes
    path('create/', views.invoice_create, name='invoice_create'),
    path('list/', views.invoice_list, name='invoice_list'),
    path('view/<str:invoice_no>/', views.invoice_view, name='invoice_view'),
    path('pdf/<str:invoice_no>/', views.invoice_pdf, name='invoice_pdf'),
    path('delete/<int:invoice_id>/', views.invoice_delete, name='invoice_delete'),
]
