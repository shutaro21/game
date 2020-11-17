from django.urls import path

from . import views

app_name = 'wg'
urlpatterns = [
    path('cons', views.cons, name='cons'),
    path('save_template', views.save_template, name='save_template'),
    path('get_template', views.get_template, name='get_template'),
    path('del_template', views.del_template, name='del_template'),
]
