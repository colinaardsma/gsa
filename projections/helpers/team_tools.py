"""Interface with program here"""
# import operator
import time
import logging
import urllib
import pprint

from .data_analysis import rate_fa, rate_team, single_player_rater_db, single_player_rater_html, final_stats_projection, league_volatility, rank_list, evaluate_keepers, trade_analyzer
from .player_creator import calc_batter_z_score, calc_pitcher_z_score, create_full_batter_html, create_full_pitcher_html, create_full_batter_csv, create_full_pitcher_csv
from .html_parser import scrape_razzball
from ..models import BatterProjection, BatterValue, PitcherProjection, PitcherValue, save_batter, save_batter_values, save_pitcher, save_pitcher_values
from leagues.helpers.yql_queries import get_league_settings, get_league_standings, get_all_team_rosters, get_keepers, get_players, get_single_team_roster
from .keepers import project_keepers
from leagues.models import League, update_league


# static variables

#TODO: replace these with db calls
BATTERS_OVER_ZERO_DOLLARS = 176
PITCHERS_OVER_ZERO_DOLLARS = 124
ONE_DOLLAR_BATTERS = 30
ONE_DOLLAR_PITCHERS = 22
B_DOLLAR_PER_FVAAZ = 3.0
P_DOLLAR_PER_FVAAZ = 2.17
B_PLAYER_POOL_MULT = 2.375
P_PLAYER_POOL_MULT = 4.45


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
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    player = single_player_rater_html(player_name, ros_proj_b_list, ros_proj_p_list)

    return player


def final_standing_projection(league, user, redirect):
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    rosters = get_all_team_rosters(league.league_key, user, redirect)
    return standing_projection(league, user, redirect, rosters, ros_proj_b_list, ros_proj_p_list)


def keeper_standing_projection(league, user, redirect, projected_keepers, ros_proj_b_list, ros_proj_p_list):
    rosters = keeper_to_roster_converter(projected_keepers['projected_keepers'])
    return standing_projection(league, user, redirect, rosters, ros_proj_b_list, ros_proj_p_list)


def standing_projection(league, user, redirect, rosters, ros_proj_b_list, ros_proj_p_list):
    """Returns projection of final standings for league based on\n
    current standings and team projections\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    draft_status, current_standings = get_league_standings(league.league_key, user, redirect)
    league = update_league(league, draft_status=draft_status)

    # TODO: move to method for reuse
    sgp_dict = {'R SGP': league.r_sgp_avg or league.r_sgp, 'HR SGP': league.hr_sgp_avg or league.hr_sgp,
                'RBI SGP': league.rbi_sgp_avg or league.rbi_sgp, 'SB SGP': league.sb_sgp_avg or league.sb_sgp,
                'OPS SGP': league.ops_sgp_avg or league.ops_sgp, 'AVG SGP': league.avg_sgp_avg or league.avg_sgp,
                'W SGP': league.w_sgp_avg or league.w_sgp, 'SV SGP': league.sv_sgp_avg or league.sv_sgp,
                'K SGP': league.k_sgp_avg or league.k_sgp, 'ERA SGP': league.era_sgp_avg or league.era_sgp,
                'WHIP SGP': league.whip_sgp_avg or league.whip_sgp}

    final_stats = final_stats_projection(rosters, ros_proj_b_list, ros_proj_p_list, current_standings, league)
    volatility_standings = league_volatility(sgp_dict, final_stats)
    ranked_standings = rank_list(volatility_standings)
    return ranked_standings


def keeper_to_roster_converter(keeper_dict):
    roster_list = []
    for key, val in keeper_dict.items():
        roster_dict = {'TEAM_NAME': key, 'manager_guids': val['manager_guids'], 'ROSTER': []}
        for roster_player in val['players']:
            player = dict(LAST_NAME=roster_player['last_name'].lower(), NAME=roster_player['full_name'],
                          NORMALIZED_FIRST_NAME=roster_player['first_name'].lower(), TEAM=roster_player['team'])
            roster_dict['ROSTER'].append(player)
        roster_list.append(roster_dict)
    return roster_list


def get_keeper_costs(league_key, user, redirect):
    """Returns current keepers\n
    Args:\n
        league_no: Yahoo! fantasy baseball league number.\n
    Returns:\n
        Final point standings.\n
    Raises:\n
        None.
    """
    league = League.objects.get(league_key=league_key)
    keepers = get_keepers(league_key, league, user, redirect)
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
    potential_keepers = get_keepers(league_key, league, user, redirect)
    projected_keepers = project_keepers(ros_proj_b_list, ros_proj_p_list, potential_keepers, league)

    # auction_needs = analyze_auction_needs(league, user, redirect, projected_keepers, ros_proj_b_list,ros_proj_p_list)

    end = time.time()
    elapsed = end - start
    print("***************************** %s seconds *****************************" % elapsed)
    return projected_keepers


# TODO: not ready, this needs direction and thought, currently getting an average of batter/pitcher stats kept, but what good is that?
def analyze_auction_needs(league, user, redirect, projected_keepers, ros_proj_b_list, ros_proj_p_list):
    try:
        new_league = League.objects.get(prev_year_league=league)
    except League.DoesNotExist:
        new_league = league
    standings = keeper_standing_projection(new_league, user, redirect, projected_keepers, ros_proj_b_list,
                                           ros_proj_p_list)
    for std_team in standings:
        for keeper_team_name, keeper_team_values in projected_keepers['projected_keepers'].items():
            if [mg for mg in std_team['manager_guids'] if mg in keeper_team_values['manager_guids']]:
                batters = 0
                pitchers = 0
                for player in keeper_team_values['players']:
                    if player['category'] == 'batter':
                        batters += 1
                    else:
                        pitchers += 1

                needs = {'team_name': keeper_team_name, 'manager_guids': keeper_team_values['manager_guids'],
                         'era': std_team['StatsERA'], 'hr_avg': std_team['StatsHR'] / batters,
                         'ip': std_team['StatsIP'], 'k_avg': std_team['StatsK'] / pitchers,
                         'ops_avg': std_team['StatsOPS'] / batters, 'r_avg': std_team['StatsR'] / batters,
                         'rbi_avg': std_team['StatsRBI'] / batters, 'sb_avg': std_team['StatsSB'] / batters,
                         'sv_avg': std_team['StatsSV'] / pitchers, 'total_gp': std_team['StatsTotalGP'],
                         'w_avg': std_team['StatsW'] / pitchers, 'whip': std_team['StatsWHIP']}

    # pprint.pprint(standings)


def trade_analyzer_(league_key, user, redirect, team_a, team_a_players, team_b, team_b_players, team_list):
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    # TODO: change to db call
    league_settings = get_league_settings(league_key, user, redirect)
    league_status, current_standings = get_league_standings(league_key, user, redirect)
    league = user.profile.leagues.get(league_key=league_key)
    update_league(league, status=league_status)

    sgp_dict = {'R SGP': league.r_sgp_avg or league.r_sgp, 'HR SGP': league.hr_sgp_avg or league.hr_sgp,
                'RBI SGP': league.rbi_sgp_avg or league.rbi_sgp, 'SB SGP': league.sb_sgp_avg or league.sb_sgp,
                'OPS SGP': league.ops_sgp_avg or league.ops_sgp, 'AVG SGP': league.avg_sgp_avg or league.avg_sgp,
                'W SGP': league.w_sgp_avg or league.w_sgp, 'SV SGP': league.sv_sgp_avg or league.sv_sgp,
                'K SGP': league.k_sgp_avg or league.k_sgp, 'ERA SGP': league.era_sgp_avg or league.era_sgp,
                'WHIP SGP': league.whip_sgp_avg or league.whip_sgp}

    new_standings = trade_analyzer(team_a, team_a_players, team_b, team_b_players, team_list, ros_proj_b_list,
                                   ros_proj_p_list, current_standings, league_settings, sgp_dict)
    return new_standings


def pull_batters(user, league, csv):
    start = time.time()
    # batter_list = create_full_batter_html(ROS_BATTER_URL)
    batter_list = create_full_batter_csv(user, league, csv)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nBatter Creation in %f seconds", elapsed)

    # delete all records from database before rebuidling
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
    batters_over_zero_dollars = league.batters_over_zero_dollars_avg or league.batters_over_zero_dollars
    one_dollar_batters = league.one_dollar_batters_avg or league.one_dollar_batters
    b_dollar_per_fvaaz = league.b_dollar_per_fvaaz_avg or league.b_dollar_per_fvaaz
    b_player_pool_mult = league.b_player_pool_mult_avg or league.b_player_pool_mult

    batters = calc_batter_z_score(batter_list, batters_over_zero_dollars, one_dollar_batters, b_dollar_per_fvaaz,
                                  b_player_pool_mult)
    for batter in batters:
        save_batter(batter)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nBatter Generic Valuation in %f seconds", elapsed)

    # TODO: this is very slow, not sure this is the right solution for custom valuation
    # start = time.time()
    # store_batter_values(user.yahooGuid, league, batter_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nBatter Custom Valuation  in %f seconds", elapsed)


def pull_pitchers(user, league, csv):
    start = time.time()
    # pitcher_list = create_full_pitcher_html(ROS_PITCHER_URL)
    pitcher_list = create_full_pitcher_csv(user, league, csv)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPitcher Creation in %f seconds", elapsed)

    # delete all records from database before rebuidling
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
    pitchers_over_zero_dollars = league.pitchers_over_zero_dollars_avg or league.pitchers_over_zero_dollars
    one_dollar_pitchers = league.one_dollar_pitchers_avg or league.one_dollar_pitchers
    p_dollar_per_fvaaz = league.p_dollar_per_fvaaz_avg or league.p_dollar_per_fvaaz
    p_player_pool_mult = league.p_player_pool_mult_avg or league.p_player_pool_mult

    pitchers = calc_pitcher_z_score(pitcher_list, pitchers_over_zero_dollars, one_dollar_pitchers, p_dollar_per_fvaaz,
                                    p_player_pool_mult)
    for pitcher in pitchers:
        save_pitcher(pitcher)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPitcher Generic Valuation in %f seconds", elapsed)

    # TODO: this is very slow, not sure this is the right solution for custom valuation
    # start = time.time()
    # store_pitcher_values(user.yahooGuid, league, pitcher_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nPitcher Custom Valuation in %f seconds", elapsed)


def pull_players_csv(user, league, pitcher_csv, batter_csv):
    start = time.time()
    pitcher_list = create_full_pitcher_csv(user, league, pitcher_csv)
    batter_list = create_full_batter_csv(user, league, batter_csv)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPlayer Creation in %f seconds", elapsed)
    pull_players_(user, league, pitcher_list, batter_list)


def pull_players_html(user, league, batter_url, pitcher_url):
    start = time.time()
    batter_list = scrape_razzball(batter_url)
    pitcher_list = scrape_razzball(pitcher_url)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPlayer Creation in %f seconds", elapsed)
    pull_players_(user, league, pitcher_list, batter_list)


def pull_players_(user, league, pitcher_list, batter_list):
    # delete all records from database before rebuidling
    start = time.time()
    pitchers_to_delete = PitcherProjection.objects.all()
    batters_to_delete = BatterProjection.objects.all()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPlayer Get for Deletion in %f seconds", elapsed)

    start = time.time()
    for pitcher in pitchers_to_delete:
        pitcher.delete()
    for batter in batters_to_delete:
        batter.delete()
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPlayer Deletion in %f seconds", elapsed)

    start = time.time()
    batters_over_zero_dollars = league.batters_over_zero_dollars_avg or league.batters_over_zero_dollars
    one_dollar_batters = league.one_dollar_batters_avg or league.one_dollar_batters
    b_dollar_per_fvaaz = league.b_dollar_per_fvaaz_avg or league.b_dollar_per_fvaaz
    b_player_pool_mult = league.b_player_pool_mult_avg or league.b_player_pool_mult
    pitchers_over_zero_dollars = league.pitchers_over_zero_dollars_avg or league.pitchers_over_zero_dollars
    one_dollar_pitchers = league.one_dollar_pitchers_avg or league.one_dollar_pitchers
    p_dollar_per_fvaaz = league.p_dollar_per_fvaaz_avg or league.p_dollar_per_fvaaz
    p_player_pool_mult = league.p_player_pool_mult_avg or league.p_player_pool_mult

    pitchers = calc_pitcher_z_score(pitcher_list, pitchers_over_zero_dollars, one_dollar_pitchers, p_dollar_per_fvaaz,
                                    p_player_pool_mult)
    batters = calc_batter_z_score(batter_list, batters_over_zero_dollars, one_dollar_batters, b_dollar_per_fvaaz,
                                  b_player_pool_mult)
    for pitcher in pitchers:
        save_pitcher(pitcher)
    for batter in batters:
        save_batter(batter)
    end = time.time()
    elapsed = end - start
    logging.info("\r\n***************\r\nPlayer Generic Valuation in %f seconds", elapsed)

    # TODO: this is very slow, not sure this is the right solution for custom valuation
    # start = time.time()
    # store_batter_values(user.yahooGuid, league, batter_models)
    # store_pitcher_values(user.yahooGuid, league, pitcher_models)
    # end = time.time()
    # elapsed = end - start
    # logging.info("\r\n***************\r\nPitcher Custom Valuation in %f seconds", elapsed)
