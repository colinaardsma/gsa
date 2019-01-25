"""gsa URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.static import serve

from leagues.views import get_token_, get_leagues_, main_page, registration
from projections.views import team_tools, user_

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView,  {'template_name': 'login.html'}, name='login'),
    path('logout/', auth_views.LogoutView, {'template_name': 'main_page.html'}, name='logout'),
    path('registration/', registration, name='registration'),

    path('leagues/', include('leagues.urls')),
    path('projections/', include('projections.urls')),
    path('get_token/', get_token_, name='get_token'),
    path('team_tools/', team_tools, name='team_tools'),
    path('user/', user_, name='user'),
    path('get_leagues/', get_leagues_, name='get_token'),
    path('', main_page, name='main_page'),
]
