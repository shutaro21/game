from django.urls import path

from . import views

app_name = 'zoom'
urlpatterns = [
    path('', views.zoom, name='zoom'),
    path('create_meeting', views.create_meeting_api, name='create_meeting'),
    path('webhook', views.webhook, name='webhook'),
]
