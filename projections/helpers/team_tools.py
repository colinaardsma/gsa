"""Interface with program here"""
# import operator
import time
import logging
import urllib
import pprint

from .data_analysis import rate_fa, rate_team, single_player_rater_db, single_player_rater_html, final_stats_projection, league_volatility, rank_list, evaluate_keepers, trade_analyzer
from .player_creator import calc_batter_z_score, calc_pitcher_z_score, create_full_batter_html, create_full_pitcher_html, create_full_batter_csv, create_full_pitcher_csv
from ..models import BatterProjection, BatterValue, PitcherProjection, PitcherValue, save_batter, save_batter_values, save_pitcher, save_pitcher_values
from leagues.helpers.yql_queries import get_league_settings, get_league_standings, get_all_team_rosters, get_keepers, get_players, get_single_team_roster
from .keepers import project_keepers
from leagues.models import League, update_league

RUN_ASYNC = True

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
# BATTER_LIST = create_full_batter_html(ROS_BATTER_URL)
# PITCHER_LIST = create_full_pitcher_html(ROS_PITCHER_URL)
# BATTER_LIST = create_full_batter_csv(CSV)
# PITCHER_LIST = create_full_pitcher_csv(CSV)

SGP_DICT = {'R SGP': 19.16666667, 'HR SGP': 11.5, 'RBI SGP': 20.83333333, 'SB SGP': 7.537037037,
            'OPS SGP': 0.005055555556, 'W SGP': 3.277777778, 'SV SGP': 10.44444444, 'K SGP': 42.5,
            'ERA SGP': -0.08444444444, 'WHIP SGP': -0.01666666667}


# # dynamic variables
# ROS_PROJ_B_LIST = queries.get_batters()
# ROS_PROJ_P_LIST = queries.get_pitchers()
# ROS_PROJ_B_LIST = calc_batter_z_score(BATTER_LIST, BATTERS_OVER_ZERO_DOLLARS,
#                                                      ONE_DOLLAR_BATTERS, B_DOLLAR_PER_FVAAZ,
#                                                      B_PLAYER_POOL_MULT)
# ROS_PROJ_P_LIST = calc_pitcher_z_score(PITCHER_LIST, PITCHERS_OVER_ZERO_DOLLARS,
#                                                       ONE_DOLLAR_PITCHERS, P_DOLLAR_PER_FVAAZ,
#                                                       P_PLAYER_POOL_MULT)

# variable defined within methods
# BATTER_FA_LIST = yahoo_fa(LEAGUE_NO, "B")
# PITCHER_FA_LIST = yahoo_fa(LEAGUE_NO, "P")
# LEAGUE_SETTINGS = get_league_settings(LEAGUE_NO)
# CURRENT_STANDINGS = get_standings(LEAGUE_NO, int(LEAGUE_SETTINGS['Max Teams:']))
# TEAM_LIST = yahoo_teams(LEAGUE_NO)
# LEAGUE_POS_DICT = split_league_pos_types(LEAGUE_SETTINGS["Roster Positions:"])

def fa_finder(league_key, user, redirect):
    """Compare team player values with available FA player values\n
    Args:\n
        league_key: Yahoo! fantasy baseball league number.\n
        team_name: name of the team to retreive.\n
    Returns:\n
        string comparing team values against fa values.\n
    Raises:\n
        None.
    """
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()

    player_comp = {}
    pitching_fa_list = get_players(league_key, user, redirect, 300, "P", "FA")
    batting_fa_list = get_players(league_key, user, redirect, 300, "B", "FA")
    avail_pitching_fas = rate_fa(pitching_fa_list, ros_proj_p_list)
    yahoo_team = get_single_team_roster(league_key, user, redirect)
    # yahoo_team = get_single_yahoo_team(league_no, team_name)
    team_pitching_values = rate_team(yahoo_team, ros_proj_p_list)
    avail_batting_fas = rate_fa(batting_fa_list, ros_proj_b_list)
    team_batting_values = rate_team(yahoo_team, ros_proj_b_list)

    player_comp['TeamName'] = yahoo_team['TEAM_NAME']
    player_comp['PitchingFAs'] = avail_pitching_fas
    player_comp['PitchingTeam'] = team_pitching_values
    player_comp['BattingFAs'] = avail_batting_fas
    player_comp['BattingTeam'] = team_batting_values

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
    # player_list = single_player_rater_db(player_name)
    # player = player_list[0]
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    player = single_player_rater_html(player_name, ros_proj_b_list, ros_proj_p_list)
    # player_stats = ""
    # if any("P" in pos for pos in player.pos):
    #     player_stats = ("${player.dollarValue:^5.2f} - {player.name:^25} - {player.pos:^25}" +
    #                     " - {player.w:^3} - {player.sv:^2} - {player.k:^3}" +
    #                     "- {player.era:^4} - {player.whip:^4}\n").format(player=player)
    # else:
    #     player_stats = ("${player.dollarValue:^5.2f} - {player.name:^25} - {player.pos:^25}" +
    #                     " - {player.r:^3} - {player.hr:^2} - {player.rbi:^3}" +
    #                     " - {player.sb:^2} - {player.ops:^5} - {player.avg:^5}\n").format(player=player)

    return player


def final_standing_projection(league_key, user, redirect):
    """Returns projection of final standings for league based on\n
    current standings and team projections\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    # ros_proj_b_list = calc_batter_z_score(BATTER_LIST, BATTERS_OVER_ZERO_DOLLARS,
    #                                                      ONE_DOLLAR_BATTERS, B_DOLLAR_PER_FVAAZ,
    #                                                      B_PLAYER_POOL_MULT)
    # ros_proj_p_list = calc_pitcher_z_score(PITCHER_LIST, PITCHERS_OVER_ZERO_DOLLARS,
    #                                                      ONE_DOLLAR_PITCHERS, P_DOLLAR_PER_FVAAZ,
    #                                                      P_PLAYER_POOL_MULT)
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    # TODO: change to db call
    league_settings = get_league_settings(league_key, user, redirect)
    league_status, current_standings = get_league_standings(league_key, user, redirect)
    league = user.profile.leagues.get(league_key=league_key)
    update_league(league, status=league_status)

    team_list = get_all_team_rosters(league_key, user, redirect)
    final_stats = final_stats_projection(team_list, ros_proj_b_list, ros_proj_p_list, current_standings, league_settings)
    volatility_standings = league_volatility(SGP_DICT, final_stats)
    ranked_standings = rank_list(volatility_standings)
    return ranked_standings


def get_keeper_costs(league_key, user, redirect):
    """Returns current keepers\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    keepers = get_keepers(league_key, user, redirect)
    return keepers


# def get_projected_keepers(league_key, user, redirect):
#     """Returns current keepers\n
#     Args:\n
#         league_no: Yahoo! fantasy baseball league number.\n
#     Returns:\n
#         Final point standings.\n
#     Raises:\n
#         None.
#     """
#     ros_proj_b_list = BatterProjection.objects.all()
#     ros_proj_p_list = PitcherProjection.objects.all()
#     keepers = get_keepers(league_key, user, redirect)
#     eval_keepers = evaluate_keepers(keepers, ros_proj_b_list, ros_proj_p_list)
#     # import pprint
#     # pprint.pprint(eval_keepers)
#     return eval_keepers


def get_projected_keepers(league_key, user, redirect):
    """Returns current keepers\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    start = time.time()
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    league = League.objects.get(league_key=league_key)
    potential_keepers = get_keepers(league_key, user, redirect)
    projected_keepers = project_keepers(ros_proj_b_list, ros_proj_p_list, potential_keepers, league)
    end = time.time()
    elapsed = end - start
    print("***************************** %s seconds *****************************" % elapsed)
    return projected_keepers


def trade_analyzer_(league_key, user, redirect, team_a, team_a_players, team_b, team_b_players, team_list):
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    # TODO: change to db call
    league_settings = get_league_settings(league_key, user, redirect)
    league_status, current_standings = get_league_standings(league_key, user, redirect)
    league = user.profile.leagues.get(league_key=league_key)
    update_league(league, status=league_status)

    new_standings = trade_analyzer(team_a, team_a_players, team_b, team_b_players, team_list, ros_proj_b_list,
                                   ros_proj_p_list, current_standings, league_settings, SGP_DICT)
    return new_standings


def batter_projections():
    start = time.time()
    projections = BatterProjection.objects.all()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nGet Batter in %f seconds", elapsed)

    # sorted_proj = sorted(projections, key=lambda x: x.dollarValue, reverse=True)
    return projections


def pitcher_projections():
    start = time.time()
    projections = PitcherProjection.objects.all()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nGet Pitcher in %f seconds", elapsed)

    # sorted_proj = sorted(projections, key=lambda x: x.dollarValue, reverse=True)
    return projections


def pull_batters(user, league, csv):
    start = time.time()
    # batter_list = create_full_batter_html(ROS_BATTER_URL)
    batter_list = create_full_batter_csv(user, league, csv)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nBatter Creation in %f seconds", elapsed)

    # delete all records from database before rebuidling
    # if BatterDB:
    start = time.time()
    batters_to_delete = BatterProjection.objects.all()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nBatter Get for Deletion in %f seconds", elapsed)

    start = time.time()
    for batter in batters_to_delete:
        batter.delete()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nBatter Deletion in %f seconds", elapsed)

    start = time.time()
    batters = calc_batter_z_score(batter_list, BATTERS_OVER_ZERO_DOLLARS,
                                  ONE_DOLLAR_BATTERS, B_DOLLAR_PER_FVAAZ,
                                  B_PLAYER_POOL_MULT)
    # batter_models = []
    for batter in batters:
        batter_model = save_batter(batter)
        # batter_models.append(batter_model)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nBatter Valuation in %f seconds", elapsed)

    # start = time.time()
    # for batter in batter_models:
    #     batter.save()
    # # put_batters(batter_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nGeneric Batter DB Storage in %f seconds", elapsed)

    # TODO: this is very slow, not sure this is the right solution for custom valuation
    # start = time.time()
    # store_batter_values(user.yahooGuid, league, batter_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nBatter Value DB Storage in %f seconds", elapsed)


def pull_pitchers(user, league, csv):
    start = time.time()
    # pitcher_list = create_full_pitcher_html(ROS_PITCHER_URL)
    pitcher_list = create_full_pitcher_csv(user, league, csv)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPitcher Creation in %f seconds", elapsed)

    # delete all records from database before rebuidling
    # if PitcherDB:
    start = time.time()
    pitchers_to_delete = PitcherProjection.objects.all()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPitcher Get for Deletion in %f seconds", elapsed)

    start = time.time()
    for pitcher in pitchers_to_delete:
        pitcher.delete()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPitcher Deletion in %f seconds", elapsed)

    start = time.time()
    pitchers = calc_pitcher_z_score(pitcher_list, PITCHERS_OVER_ZERO_DOLLARS,
                                    ONE_DOLLAR_PITCHERS, P_DOLLAR_PER_FVAAZ,
                                    P_PLAYER_POOL_MULT)
    # pitcher_models = []
    for pitcher in pitchers:
        pitcher_model = save_pitcher(pitcher)
        # pitcher_models.append(pitcher_model)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPitcher Valuation in %f seconds", elapsed)

    # start = time.time()
    # for pitcher in pitcher_models:
    #     pitcher.save()
    # # put_pitchers(pitcher_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nGeneric Pitcher DB Storage in %f seconds", elapsed)

    # TODO: this is very slow, not sure this is the right solution for custom valuation
    # start = time.time()
    # store_pitcher_values(user.yahooGuid, league, pitcher_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nPitcher Value DB Storage in %f seconds", elapsed)


def pull_players(user, league, pitcher_csv, batter_csv):
    # pitcher_list = create_full_pitcher_html(ROS_PITCHER_URL)
    # batter_list = create_full_batter_html(ROS_BATTER_URL)
    pitcher_list = create_full_pitcher_csv(user, league, pitcher_csv)
    batter_list = create_full_batter_csv(user, league, batter_csv)
    # delete all records from database before rebuidling
    # if PitcherDB:
    pitchers_to_delete = PitcherProjection.objects.all()
    # if BatterDB:
    batters_to_delete = BatterProjection.objects.all()
    pitchers = calc_pitcher_z_score(pitcher_list, PITCHERS_OVER_ZERO_DOLLARS,
                                    ONE_DOLLAR_PITCHERS, P_DOLLAR_PER_FVAAZ,
                                    P_PLAYER_POOL_MULT)
    batters = calc_batter_z_score(batter_list, BATTERS_OVER_ZERO_DOLLARS,
                                  ONE_DOLLAR_BATTERS, B_DOLLAR_PER_FVAAZ,
                                  B_PLAYER_POOL_MULT)
    for pitcher in pitchers_to_delete:
        pitcher.delete()
    # pitcher_models = []
    for pitcher in pitchers:
        pitcher_model = save_pitcher(pitcher)
        # pitcher_models.append(pitcher_model)
    for batter in batters_to_delete:
        batter.delete()
    # batter_models = []
    for batter in batters:
        batter_model = save_batter(batter)
        # batter_models.append(batter_model)

    # put_batters(batter_models)
    # store_batter_values(user.yahooGuid, league, batter_models)
    # put_pitchers(pitcher_models)
    # store_pitcher_values(user.yahooGuid, league, pitcher_models)

# print pull_batters()
# start = time.time()
# print single_player_rater("mike trout")
# # print fa_finder(5091, "MachadoAboutNothing") #42sec #29sec
# # print final_standing_projection(5091) #21sec #5sec
# end = time.time()
# elapsed = end - start
# print "{elapsed:.2f} seconds".format(elapsed=elapsed)