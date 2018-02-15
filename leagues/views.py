import time
import cgi
import json
import datetime
import heapq

from django.shortcuts import render, redirect
from django.views import generic
from django.http import HttpResponse
from django.db.models import Max
from django.contrib.auth.models import User

from .helpers.api_connector import request_auth, get_token
from .models import League, update_profile, save_league, calc_three_year_avgs
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
    redirect = "/user"

    update_leagues(request.user, redirect)
    return render(request, 'index.html', {})


def get_leagues_(request):
    get_leagues_from_yahoo(request.user)
    return redirect('/user')


def get_leagues_from_yahoo(user):
    leagues = get_leagues(user, USER_REDIRECT)
    db_leagues = League.objects.all()
    batters = BatterProjection.objects.all()
    batter_fvaaz_list = []
    for batter in batters:
        batter_fvaaz_list.append(batter.fvaaz)
    pitchers = PitcherProjection.objects.all()
    pitcher_fvaaz_list = []
    for pitcher in pitchers:
        pitcher_fvaaz_list.append(pitcher.fvaaz)
    main_league = None
    for league in leagues:
        db_league = [db_lg for db_lg in db_leagues if db_lg.league_key == league['league_key']]
        if not db_league:
            settings = get_league_settings(league['league_key'], user, USER_REDIRECT)
            standings = get_league_standings(league['league_key'], user, USER_REDIRECT)
            results = get_auction_results(league['league_key'], user, USER_REDIRECT)
            sgp = get_sgp(standings)
            avg_sgp = 0.00
            ops_sgp = 0.00
            drafted_batters_over_one_dollar = (results['total_batters_drafted']
                                               - results['one_dollar_batters'])
            drafted_pitchers_over_one_dollar = (results['total_pitchers_drafted']
                                                - results['one_dollar_pitchers'])

            batter_fvaaz_over_one_dollar = heapq.nlargest(drafted_batters_over_one_dollar,
                                                          batter_fvaaz_list)
            pitcher_fvaaz_over_one_dollar = heapq.nlargest(drafted_pitchers_over_one_dollar,
                                                           pitcher_fvaaz_list)
            total_batter_fvaaz_over_one_dollar = sum(batter_fvaaz_over_one_dollar)
            total_pitcher_fvaaz_over_one_dollar = sum(pitcher_fvaaz_over_one_dollar)

            batter_budget_over_one_dollar = (results['money_spent_on_batters']
                                             - results['one_dollar_batters'])
            pitcher_budget_over_one_dollar = (results['money_spent_on_pitchers']
                                              - results['one_dollar_pitchers'])

            batter_dollar_per_fvaaz = (batter_budget_over_one_dollar
                                       / total_batter_fvaaz_over_one_dollar)
            pitcher_dollar_per_fvaaz = (pitcher_budget_over_one_dollar
                                        / total_pitcher_fvaaz_over_one_dollar)

            b_player_pool_mult = 2.375
            p_player_pool_mult = 4.45

            if 'AVG' in sgp:
                avg_sgp = sgp['AVG']
            if 'OPS' in sgp:
                ops_sgp = sgp['OPS']
            save_league(user, settings['Name'], settings['League Key'],
                        settings['Max Teams'], settings['Max Innings Pitched'],
                        settings['Batting POS'], settings['Pitching POS'],
                        settings['Bench POS'], settings['DL POS'],
                        settings['NA POS'], settings['Prev Year Key'],
                        settings['Season'], sgp['R'], sgp['HR'], sgp['RBI'],
                        sgp['SB'], ops_sgp, avg_sgp, sgp['W'], sgp['SV'],
                        sgp['K'], sgp['ERA'], sgp['WHIP'],
                        results['total_batters_drafted'],
                        results['total_pitchers_drafted'],
                        results['one_dollar_batters'],
                        results['one_dollar_pitchers'], results['total_money_spent'],
                        results['money_spent_on_batters'],
                        results['money_spent_on_pitchers'], results['batter_budget_pct'],
                        results['pitcher_budget_pct'],
                        batter_dollar_per_fvaaz, pitcher_dollar_per_fvaaz,
                        b_player_pool_mult, p_player_pool_mult)
            calc_three_year_avgs(settings['League Key'])
        main_league = league
    update_profile(user, main_league=main_league['league_key'])


def max_year_leagues(user):
    try:
        user_leagues = user.profile.leagues.all()
    except User.DoesNotExist:
        user_leagues = None
    if not user_leagues:
        return None

    max_year = user_leagues.aggregate(Max('season'))['season__max']
    return user_leagues.filter(season=max_year)


def update_main_league(request):
    if request.method == 'POST':
        league_key = request.POST["league_key"]
        update_profile(request.user, main_league=league_key)
    elapsed = None
    yahoo_link = request_auth(TOKEN_REDIRECT_PATH)
    max_year_leagues_ = max_year_leagues(request.user)
    # return render(request, 'user.html', {'yahoo_link': yahoo_link, 'elapsed': elapsed, 'max_year_leagues': max_year_leagues_})
    return redirect("/user/")


def main_page(request):
    return render(request, "main_page.html", {})