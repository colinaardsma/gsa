import time
import cgi
import json
import datetime
import heapq

from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse
from django.contrib.auth.models import User

from .helpers.api_connector import request_auth, get_token
from .models import League, update_profile, save_league, calc_three_year_avgs, max_year_leagues
from .helpers.yql_queries import update_leagues, get_leagues, get_league_settings, get_league_standings, get_auction_results
from projections.helpers.advanced_stat_calc import get_sgp
from projections.models import BatterProjection, BatterValue, PitcherProjection, PitcherValue
from gsa.settings import TOKEN_REDIRECT_PATH, TEAM_TOOLS_REDIRECT, USER_REDIRECT

# class IndexView(generic.DetailView):
#     template_name = 'index.html'
#     context_object_name = 'latest_question_list'


# def get_user(request):
#     user = None
#     if request.user.is_authenticated():
#         user = request.user
#     return user


def index(request):
    # TODO: this POST/GET logic is correct syntax, but currently does nothing
    if request.method == 'POST':
        elapsed = request.POST['elapsed']
        yahoo_link = request.POST['yahoo_link']
    else:
        # question = get_object_or_404(Question, pk=question_id)
        # return render(request, 'index.html', {'question': question})
        yahoo_link = request_auth(TOKEN_REDIRECT_PATH)
        elapsed = None
    return render(request, 'index.html', {'yahoo_link': yahoo_link, 'elapsed': elapsed})


# def link_yahoo(request):
#     yahoo_link = request_auth(TOKEN_REDIRECT_PATH)
#     self.render_user(link_yahoo=link_yahoo)


def get_token_(request):
    code = request.GET['code']

    token_json = get_token(code, TOKEN_REDIRECT_PATH)
    token_dict = json.loads(token_json)
    yahoo_guid = token_dict['xoauth_yahoo_guid']
    access_token = token_dict['access_token']
    refresh_token = token_dict['refresh_token']
    token_expiration = (datetime.datetime.now() +
                        datetime.timedelta(seconds=token_dict['expires_in']))
    update_profile(request.user, yahoo_guid=yahoo_guid,
                   access_token=access_token, refresh_token=refresh_token,
                   token_expiration=token_expiration)

    update_leagues(request.user, USER_REDIRECT)
    return redirect(USER_REDIRECT)


def get_leagues_(request):
    update_leagues(request.user, USER_REDIRECT)
    return redirect(USER_REDIRECT)


def update_main_league(request):
    if request.method == 'POST':
        league_key = request.POST["league_key"]
        update_profile(request.user, main_league=league_key)
    elapsed = None
    yahoo_link = request_auth(TOKEN_REDIRECT_PATH)
    max_year_leagues_ = max_year_leagues(request.user)
    # return render(request, 'user.html', {'yahoo_link': yahoo_link, 'elapsed': elapsed, 'max_year_leagues': max_year_leagues_})
    return redirect(USER_REDIRECT)


def main_page(request):
    return render(request, "main_page.html", {})
