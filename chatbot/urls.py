"""
URLs para el chatbot
"""
from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.index, name='index'),
    path('webhook/', views.webhook, name='webhook'),
    path('status/', views.status, name='status'),
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:conversation_id>/messages/', views.conversation_messages, name='conversation_messages'),
    path('send-alert/', views.send_alert, name='send_alert'),
]
