from django.urls import path

from . import views

app_name = 'zoom'
urlpatterns = [
    path('', views.zoom, name='zoom'),
    path('create_meeting', views.create_meeting, name='create_meeting'),
]
