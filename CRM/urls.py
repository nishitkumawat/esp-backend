from django.urls import path

from CRM.views.auth import login_view, signup_view, logout_view
from CRM.views.dashboard import dashboard
from CRM.views.leads import (
    lead_list, lead_create, lead_detail, lead_edit, lead_delete,
    lead_add_note, lead_add_followup, lead_add_tag,
    lead_bulk_action, solar_leads, machine_leads,
)
from CRM.views.chat import chat_index, send_chat_message
from CRM.views.followups import followup_list, followup_complete
from CRM.views.reports import reports_index, export_report
from CRM.views.tags import tag_list, user_list
from CRM.views.api import (
    api_chart_data, api_chat_messages, whatsapp_webhook,
    send_message_api, whatsapp_status_api
)

app_name = 'crm'

urlpatterns = [
    # --- Auth ---
    path('auth/login/', login_view, name='login'),
    path('auth/signup/', signup_view, name='signup'),
    path('auth/logout/', logout_view, name='logout'),

    # --- Dashboard ---
    path('', dashboard, name='dashboard'),
    path('dashboard/', dashboard, name='dashboard_alt'),

    # --- Leads ---
    path('leads/', lead_list, name='lead_list'),
    path('leads/create/', lead_create, name='lead_create'),
    path('leads/<int:lead_id>/', lead_detail, name='lead_detail'),
    path('leads/<int:lead_id>/edit/', lead_edit, name='lead_edit'),
    path('leads/<int:lead_id>/delete/', lead_delete, name='lead_delete'),
    path('leads/<int:lead_id>/note/', lead_add_note, name='lead_add_note'),
    path('leads/<int:lead_id>/followup/', lead_add_followup, name='lead_add_followup'),
    path('leads/<int:lead_id>/tag/', lead_add_tag, name='lead_add_tag'),
    path('leads/bulk/', lead_bulk_action, name='lead_bulk_action'),

    # --- Category Shortcuts ---
    path('solar/', solar_leads, name='solar_leads'),
    path('machines/', machine_leads, name='machine_leads'),

    # --- Chat ---
    path('chat/', chat_index, name='chat_index'),
    path('chat/send/', send_chat_message, name='send_chat_message'),

    # --- Follow-Ups ---
    path('followups/', followup_list, name='followup_list'),
    path('followups/<int:followup_id>/complete/', followup_complete, name='followup_complete'),

    # --- Reports ---
    path('reports/', reports_index, name='reports_index'),
    path('reports/export/', export_report, name='export_report'),

    # --- Tags & Users (Admin) ---
    path('tags/', tag_list, name='tag_list'),
    path('users/', user_list, name='user_list'),

    # --- API ---
    path('api/chart-data/', api_chart_data, name='api_chart_data'),
    path('api/chat/<int:conversation_id>/messages/', api_chat_messages, name='api_chat_messages'),
    path('api/webhook/whatsapp/', whatsapp_webhook, name='whatsapp_webhook'),
    path('api/send-message/', send_message_api, name='send_message_api'),
    path('api/whatsapp-status/', whatsapp_status_api, name='whatsapp_status_api'),
]
