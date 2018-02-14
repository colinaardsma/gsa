"""Interface with program here"""
# import operator
import time
import urllib

from leagues.helpers.html_parser import get_league_settings, get_standings, split_league_pos_types, yahoo_teams, yahoo_players, get_single_yahoo_team
from ..models import BatterProjection, BatterValue, PitcherProjection, PitcherValue, save_batter, save_batter_values, save_pitcher, save_pitcher_values
from .data_analysis import rate_fa, rate_team, single_player_rater_db, single_player_rater_html, final_stats_projection, league_volatility, rank_list, evaluate_keepers, trade_analyzer

# https://developer.yahoo.com/fantasysports/guide/players-collection.html
# https://www.mysportsfeeds.com

# static variables
ROS_BATTER_URL = "http://www.fantasypros.com/mlb/projections/ros-hitters.php"
ROS_PITCHER_URL = "https://www.fantasypros.com/mlb/projections/ros-pitchers.php"
# ROS_BATTER_URL = "file://" + urllib.pathname2url(r"/Users/colinaardsma/git/tfbps/testing html/2017 Rest of Season Fantasy Baseball Projections - Hitters.html")
# ROS_PITCHER_URL = "file://" + urllib.pathname2url(r"/Users/colinaardsma/git/tfbps/testing html/2017 Rest of Season Fantasy Baseball Projections - Pitchers.html")

BATTERS_OVER_ZERO_DOLLARS = 176
PITCHERS_OVER_ZERO_DOLLARS = 124
ONE_DOLLAR_BATTERS = 30
ONE_DOLLAR_PITCHERS = 22
B_DOLLAR_PER_FVAAZ = 3.0
P_DOLLAR_PER_FVAAZ = 2.17
B_PLAYER_POOL_MULT = 2.375
P_PLAYER_POOL_MULT = 4.45
LEAGUE_NO = 5091
TEAM_COUNT = 12

SGP_DICT = {'R SGP': 19.16666667, 'HR SGP': 11.5, 'RBI SGP': 20.83333333, 'SB SGP': 7.537037037,
            'OPS SGP': 0.005055555556, 'W SGP': 3.277777778, 'SV SGP': 10.44444444, 'K SGP': 42.5,
            'ERA SGP': -0.08444444444, 'WHIP SGP': -0.01666666667}

# dynamic variables
# BATTER_LIST = player_creator.create_full_batter_html(ROS_BATTER_URL)
# PITCHER_LIST = player_creator.create_full_pitcher_html(ROS_PITCHER_URL)
# BATTER_LIST = player_creator.create_full_batter_csv(CSV)
# PITCHER_LIST = player_creator.create_full_pitcher_csv(CSV)
# ROS_PROJ_B_LIST = player_creator.calc_batter_z_score(BATTER_LIST, BATTERS_OVER_ZERO_DOLLARS,
#                                                      ONE_DOLLAR_BATTERS, B_DOLLAR_PER_FVAAZ,
#                                                      B_PLAYER_POOL_MULT)
# ROS_PROJ_P_LIST = player_creator.calc_pitcher_z_score(PITCHER_LIST, PITCHERS_OVER_ZERO_DOLLARS,
#                                                       ONE_DOLLAR_PITCHERS, P_DOLLAR_PER_FVAAZ,
#                                                       P_PLAYER_POOL_MULT)
# ROS_PROJ_B_LIST = BatterProjection.objects.all()
# ROS_PROJ_P_LIST = PitcherProjection.objects.all()

# variable defined within methods
# BATTER_FA_LIST = yahoo_fa(LEAGUE_NO, "B")
# PITCHER_FA_LIST = yahoo_fa(LEAGUE_NO, "P")
# LEAGUE_SETTINGS = get_league_settings(LEAGUE_NO)
# CURRENT_STANDINGS = get_standings(LEAGUE_NO, int(LEAGUE_SETTINGS['Max Teams:']))
# TEAM_LIST = yahoo_teams(LEAGUE_NO)
# LEAGUE_POS_DICT = split_league_pos_types(LEAGUE_SETTINGS["Roster Positions:"])


def fa_finder(league_no, team_name):
    """Compare team player values with available FA player values\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
        team_name: name of the team to retreive.\n
    Returns:\n
        string comparing team values against fa values.\n
    Raises:\n
        None.
    """
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    player_comp = {}
    pitching_fa_list = yahoo_players(league_no, "P")
    batting_fa_list = yahoo_players(LEAGUE_NO, "B")
    avail_pitching_fas = rate_fa(pitching_fa_list, ros_proj_p_list)
    yahoo_team = get_single_yahoo_team(league_no, team_name)
    team_pitching_values = rate_team(yahoo_team, ros_proj_p_list)
    avail_batting_fas = rate_fa(batting_fa_list, ros_proj_b_list)
    team_batting_values = rate_team(yahoo_team, ros_proj_b_list)

    player_comp['Team Name'] = yahoo_team['TEAM_NAME']
    player_comp['Pitching FAs'] = avail_pitching_fas
    player_comp['Pitching Team'] = team_pitching_values
    player_comp['Batting FAs'] = avail_batting_fas
    player_comp['Batting Team'] = team_batting_values

    return player_comp


def single_player_rater(player_name):
    """Searches for and returns rating of and individual player\n
    Args:\n
        player_name: name of the player to search for.\n
    Returns:\n
        rated player object.\n
    Raises:\n
        None.
    """
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    player = single_player_rater_html(player_name, ros_proj_b_list, ros_proj_p_list)
    player_stats = ""
    if any("P" in pos for pos in player.pos):
        player_stats = ("${player.dollarValue:^5.2f} - {player.name:^25} - {player.pos:^25}" +
                        " - {player.wins:^3} - {player.svs:^2} - {player.sos:^3}" +
                        "- {player.era:^4} - {player.whip:^4}\n").format(player=player)
    else:
        player_stats = ("${player.dollarValue:^5.2f} - {player.name:^25} - {player.pos:^25}" +
                        " - {player.runs:^3} - {player.hrs:^2} - {player.rbis:^3}" +
                        " - {player.sbs:^2} - {player.ops:^5}\n").format(player=player)

    return player_stats


def final_standing_projection(league_no):
    """Returns projection of final standings for league based on\n
    current standings and team projections\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    league_settings = get_league_settings(league_no)
    current_standings = get_standings(league_no, int(league_settings['Max Teams:']))
    team_list = yahoo_teams(league_no)
    league_pos_dict = split_league_pos_types(league_settings["Roster Positions:"])
    final_stats = final_stats_projection(team_list, ros_proj_b_list,
                                         ros_proj_p_list, league_pos_dict,
                                         current_standings, league_settings)
    volatility_standings = league_volatility(SGP_DICT, final_stats)
    ranked_standings = rank_list(volatility_standings)
    return ranked_standings


def batter_projections():
    # projections = player_creator.calc_batter_z_score(BATTER_LIST, BATTERS_OVER_ZERO_DOLLARS,
    #                                                  ONE_DOLLAR_BATTERS, B_DOLLAR_PER_FVAAZ,
    #                                                  B_PLAYER_POOL_MULT)
    projections = BatterProjection.objects.all()
    sorted_proj = sorted(projections, key=lambda x: x.dollarValue, reverse=True)
    return sorted_proj


def pitcher_projections():
    # projections = player_creator.calc_pitcher_z_score(PITCHER_LIST, PITCHERS_OVER_ZERO_DOLLARS,
    #                                                   ONE_DOLLAR_PITCHERS, P_DOLLAR_PER_FVAAZ,
    #                                                   P_PLAYER_POOL_MULT)
    projections = PitcherProjection.objects.all()
    sorted_proj = sorted(projections, key=lambda x: x.dollarValue, reverse=True)
    return sorted_proj


def trade_analyzer_(league_no, team_a, team_a_players, team_b, team_b_players):
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    league_settings = get_league_settings(league_no)
    current_standings = get_standings(league_no, int(league_settings['Max Teams:']))
    team_list = yahoo_teams(league_no)
    league_pos_dict = split_league_pos_types(league_settings["Roster Positions:"])
    new_standings = trade_analyzer(team_a, team_a_players, team_b, team_b_players,
                                   team_list, league_pos_dict, ros_proj_b_list,
                                   ros_proj_p_list, current_standings,
                                   league_settings, SGP_DICT)
    return new_standings


def get_keepers(league_key, user, user_id, redirect):
    """Returns current keepers\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    # not yql queries, need to create and call html parser
    keepers = ""
    return keepers

# start = time.time()
# print fa_finder(5091, "MachadoAboutNothing") #42sec #29sec
# # print final_standing_projection(5091) #21sec #5sec
# end = time.time()
# elapsed = end - start
# print "{elapsed:.2f} seconds".format(elapsed=elapsed)
