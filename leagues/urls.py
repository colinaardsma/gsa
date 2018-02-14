from django.urls import path
from . import views

app_name = 'leagues'
urlpatterns = [
    path('', views.index, name='index'),
    # path('link_yahoo/', views.link_yahoo, name='link_yahoo'),
    path('get_token/', views.get_token_, name='get_token'),
    path('update_main_league/', views.update_main_league, name='update_main_league')
]
