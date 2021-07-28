from django.urls import path
from django.conf import settings

from . import views

app_name = 'kabu'
urlpatterns = [
    path(settings.KABU_URL, views.graph, name='graph'),
]
