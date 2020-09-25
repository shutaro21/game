from django.urls import path

from . import views

app_name = 'linq'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:game_id>/entry/', views.entry, name='entry'),
    path('<int:player_id>/<int:round_no>/main', views.main, name='main'),
    path('<int:player_id>/<int:round_no>/result', views.result, name='result'),
    path('create_game', views.create_game, name='create_game'),
    path('<int:game_id>/entry_player', views.entry_player, name='entry_player'),
    path('<int:player_id>/<int:round_no>/check', views.check, name='check'),
    path('<int:player_id>/<int:round_no>/hint', views.hint, name='hint'),
    path('<int:player_id>/<int:round_no>/poll', views.poll, name='poll'),
]
