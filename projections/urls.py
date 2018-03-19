from django.urls import path
from . import views

app_name = 'projections'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('process_players/', views.process_players, name='process_players'),
    path('team_tools/', views.team_tools, name='team_tools'),
    path('top_avail_players/', views.top_avail_players, name='top_avail_players'),
    path('single_player/', views.single_player, name='single_player'),
    path('trade_projection/', views.trade_projection, name='trade_projection'),
    path('projected_standings/', views.projected_standings, name='projected_standings'),
    path('potential_keepers/', views.potential_keepers, name='potential_keepers'),
    path('projected_keepers/', views.projected_keepers, name='projected_keepers'),
    path('batting/', views.batting_projections, name='batting'),
    path('pitching/', views.pitching_projections, name='pitching'),
    path('user/', views.user_, name='user'),
    path('scrape_proj/', views.scrape_proj, name='scrape_proj'),
    path('set_main_league/', views.set_main_league, name='set_main_league'),
    path('auction_values/', views.auction_values, name='auction_values'),

    path('test/', views.test, name='test'),
]
