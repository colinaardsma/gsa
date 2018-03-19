import time
import cgi
import logging
from io import StringIO
from datetime import datetime
import pytz

from django.shortcuts import render, redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.views import generic

from gsa.settings import TOKEN_REDIRECT_PATH, TEAM_TOOLS_REDIRECT, USER_REDIRECT
from leagues.helpers.api_connector import request_auth, get_token
from leagues.models import League, dummy_league, update_profile, max_year_leagues
from leagues.helpers.yql_queries import get_current_leagues, get_all_team_rosters, get_keeper_query
from leagues.helpers.html_parser import get_single_yahoo_team
from .helpers.team_tools import pull_batters, pull_pitchers, avail_player_finder, final_standing_projection, \
    single_player_rater, get_keeper_costs, get_projected_keepers, roster_change_analyzer_, pull_players_html, \
    get_auction_values_
from .helpers.html_parser import razzball_get_update_datetime, scrape_razzball
from .helpers.keepers import project_keepers
from .models import BatterProjection, PitcherProjection


class IndexView(generic.ListView):
    template_name = 'projections/index.html'
    context_object_name = 'latest_question_list'


def process_players(request):
    start = time.time()
    player_type = request.POST['player_type']
    csv = request.FILES['csv']
    decoded_csv = StringIO(csv.read().decode())
    try:
        league = request.user.profile.leagues.get(league_key=request.user.profile.main_league)
        logging.info("USING MAIN LEAGUE %s" % league.league_key)
        logging.debug("USING MAIN LEAGUE %s" % league.league_key)
        logging.warning("USING MAIN LEAGUE %s" % league.league_key)
    except League.DoesNotExist:
        league = dummy_league()
        logging.warning("USING DUMMY LEAGUE")
    if player_type == 'batter':
        pull_batters(request.user, league, decoded_csv)
    if player_type == 'pitcher':
        pull_pitchers(request.user, league, decoded_csv)
    end = time.time()
    elapsed = end - start
    logging.info('%s seconds elapsed' % elapsed)
    return redirect(USER_REDIRECT)


def scrape_proj(request):
    # if request.method == 'POST':
    main_league = request.user.profile.leagues.get(league_key=request.user.profile.main_league)
    now = datetime.now(pytz.utc)
    if main_league.start_date > now:
        batter_url = 'http://razzball.com/restofseason-hitterprojections/'
        pitcher_url = 'http://razzball.com/restofseason-pitcherprojections/'
    else:
        batter_url = 'http://razzball.com/steamer-hitter-projections/'
        pitcher_url = 'http://razzball.com/steamer-pitcher-projections/'
    pull_players_html(request.user, main_league, batter_url, pitcher_url)
    return redirect(USER_REDIRECT)


def team_tools(request):
    if request.user and not request.user.is_anonymous:
        if request.method == 'POST':
            league_key = request.POST['league_key']
            league = request.user.profile.leagues.get(league_key=league_key)
        else:
            league = request.user.profile.leagues.get(league_key=request.user.profile.main_league)
        return render(request, 'team_tools.html', {'league': league, 'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return render(request, 'team_tools.html', {'redirect': TEAM_TOOLS_REDIRECT})
        # return redirect(TEAM_TOOLS_REDIRECT)


def top_avail_players(request):
    if request.method == 'POST':
        avail_player_league_key = request.POST["avail_player_league_key"]
        top_avail_players_ = avail_player_finder(avail_player_league_key, request.user, TEAM_TOOLS_REDIRECT)
        team_name = top_avail_players_['TeamName']
        return render(request, 'top_avail_players.html', {'top_avail_players': top_avail_players_,
                                                          'team_name': team_name, 'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def single_player(request):
    if request.method == 'POST':
        player_name = request.POST["player_name"]
        player = single_player_rater(player_name)
        return render(request, 'single_player.html', {'player': player, 'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def trade_projection(request):
    if request.method == 'POST':
        try:
            league_key = request.POST["trade_league_key"]
            league_no = None
        except MultiValueDictKeyError:
            league_no = request.POST["trade_league_no"]
            league_key = None
        try:
            team_a_name = request.POST['team_a_name']
            team_b_name = request.POST['team_b_name']
        except MultiValueDictKeyError:
            team_a_name = ""
            team_b_name = ""
        try:
            team_a = request.POST['team_a']
            team_b = request.POST['team_b']
            team_a_players = request.POST.getlist('team_a_players')
            team_b_players = request.POST.getlist('team_b_players')
            team_list = request.POST['team_list']
            league_key = request.POST['league_key']
            league_no = request.POST['league_no']
        except MultiValueDictKeyError:
            pass

        if league_key != "" and team_a_name != "" and team_b_name != "":
            team_list = get_all_team_rosters(league_key, request.user, TEAM_TOOLS_REDIRECT)
            team_a = [team for team in team_list if team['TEAM_NAME'].lower() == team_a_name.lower()][0]
            team_b = [team for team in team_list if team['TEAM_NAME'].lower() == team_b_name.lower()][0]
            import pprint
            return render(request, 'trade_projection.html', {'team_a': team_a, 'team_b': team_b,
                                                             'league_key': league_key, 'team_list': team_list,
                                                             'league_no': league_no, 'redirect': TEAM_TOOLS_REDIRECT})
        else:
            trade_result = roster_change_analyzer_(league_key, request.user, TEAM_TOOLS_REDIRECT, team_a, team_a_players,
                                                   team_b, team_b_players, team_list)
            return render(request, 'trade_projection.html',
                          {'team_a': team_a, 'team_b': team_b, 'league_key': league_key, 'league_no': league_no,
                           'trade_result': trade_result, 'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def projected_standings(request):
    if request.method == 'POST':
        proj_league_key = request.POST["proj_league_key"]
        league = request.user.profile.leagues.get(league_key=proj_league_key)
        projected_standings_ = final_standing_projection(league, request.user, TEAM_TOOLS_REDIRECT)
        return render(request, 'projected_standings.html', {'projected_standings': projected_standings_,
                                                            'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def potential_keepers(request):
    if request.method == 'POST':
        user = request.user
        potential_keepers_key = request.POST["potential_keepers_key"]
        potential_keepers_ = get_keeper_costs(potential_keepers_key, user, TEAM_TOOLS_REDIRECT)
        import pprint
        return render(request, 'potential_keepers.html', {'potential_keepers': potential_keepers_,
                                                          'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def projected_keepers(request):
    if request.method == 'POST':
        proj_keepers_key = request.POST["proj_keepers_key"]
        league = request.user.profile.leagues.get(league_key=proj_keepers_key)
        proj_keepers = get_projected_keepers(league, request.user, TEAM_TOOLS_REDIRECT)
        return render(request, 'projected_keepers.html', {'all_players': proj_keepers, 'league_settings': league,
                                                          'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def auction_values(request):
    if request.method == 'POST':
        auction_values_key = request.POST["auction_values_key"]
        main_league = request.user.profile.leagues.get(league_key=request.user.profile.main_league)
        league_settings = request.user.profile.leagues.get(league_key=auction_values_key)
        auction_values_ = get_auction_values_(main_league, request.user, TEAM_TOOLS_REDIRECT)
        return render(request, 'auction_values.html', {'all_players': auction_values_, 'league_settings': league_settings,
                                                       'redirect': TEAM_TOOLS_REDIRECT})
    else:
        return redirect(TEAM_TOOLS_REDIRECT)


def batting_projections(request):
    players = BatterProjection.objects.all().order_by('-fvaaz')
    return render(request, 'spreadsheet.html', {'players': players, 'cat': "batter"})


def pitching_projections(request):
    players = PitcherProjection.objects.all().order_by('-fvaaz')
    return render(request, 'spreadsheet.html', {'players': players, 'cat': "pitcher"})


def set_main_league(request):
    if request.method == 'POST':
        main_league_key = request.POST["main_league_key"]
        # main_league = request.user.profile.leagues.get(league_key=main_league_key)

        update_profile(request.user, main_league=main_league_key)

        # profile = request.user.profile
        # main_league = League.objects.get(league_key=main_league_key)
        # profile.main_league_key = main_league_key
        # profile.main_league = main_league
        # profile.save()
    return redirect(USER_REDIRECT)


# TODO: change to update pitching and batting at same time
def user_(request):
    # TODO: this POST/GET logic is correct syntax, but currently does nothing
    if request.method == 'POST':
        elapsed = request.POST['elapsed']
        yahoo_link = request.POST['yahoo_link']
    else:
        # question = get_object_or_404(Question, pk=question_id)
        # return render(request, 'index.html', {'question': question})
        yahoo_link = request_auth(TOKEN_REDIRECT_PATH)
        elapsed = None

    max_year_leagues_ = max_year_leagues(request.user)

    try:
        main_league = request.user.profile.leagues.get(league_key=request.user.profile.main_league)
    except League.DoesNotExist:
        main_league = None

    try:
        batter_projection_date = BatterProjection.objects.all().first().last_modified
        pitcher_projection_date = PitcherProjection.objects.all().first().last_modified
        oldest_last_mod_date = min(batter_projection_date, pitcher_projection_date)
    except AttributeError or BatterProjection.DoesNotExist or PitcherProjection.DoesNotExist:
        oldest_last_mod_date = datetime(2000, 1, 1, tzinfo=pytz.utc)

    now = datetime.now(pytz.utc)
    razzball_proj_update_datetime = None
    if main_league and main_league.end_date > now:
        batter_url = 'http://razzball.com/restofseason-hitterprojections/'
        pitcher_url = 'http://razzball.com/restofseason-pitcherprojections/'
    else:
        batter_url = 'http://razzball.com/steamer-hitter-projections/'
        pitcher_url = 'http://razzball.com/steamer-pitcher-projections/'
        # TODO: old way of checking for updated razzball, can delete
        # if oldest_last_mod_date.date() < now.date():
        #     razzball_proj_update_datetime = razzball_get_update_datetime(batter_url)
        #     if razzball_proj_update_datetime < oldest_last_mod_date:
        #         razzball_proj_update_datetime = None

    return render(request, 'user.html', {'yahoo_link': yahoo_link, 'elapsed': elapsed,
                                         'leagues': max_year_leagues_,
                                         # 'razzball_proj_update_datetime': razzball_proj_update_datetime,
                                         'proj_update_datetime': oldest_last_mod_date,
                                         'main_league': main_league, 'batter_url': batter_url,
                                         'pitcher_url': pitcher_url})


def test(request):
    main_league = request.user.profile.leagues.get(league_key=request.user.profile.main_league)
    auction_values_ = get_keeper_query(main_league, request.user, USER_REDIRECT)
    import pprint
    pprint.pprint(auction_values_)
