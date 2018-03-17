"""Interface with program here"""
# import operator
import time
import logging
import urllib
import pprint
import operator

from .data_analysis import rate_fa, rate_team, single_player_rater_db, single_player_rater_html, \
    final_stats_projection, league_volatility, rank_list, evaluate_keepers, trade_analyzer
from .player_creator import calc_batter_z_score, calc_pitcher_z_score, create_full_batter_html, \
    create_full_pitcher_html, create_full_batter_csv, create_full_pitcher_csv
from .html_parser import scrape_razzball_batters, scrape_razzball_pitchers
from ..models import BatterProjection, BatterValue, PitcherProjection, PitcherValue, save_batter, save_batter_values, \
    save_pitcher, save_pitcher_values
from leagues.helpers.yql_queries import get_league_settings, get_league_standings, get_all_team_rosters, get_keepers, \
    get_players, get_single_team_roster, get_keeper_query
from .keepers import project_keepers, get_draft_values
from leagues.models import League, update_league, dummy_league

# static variables

# TODO: replace these with db calls
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
    sgp_dict = create_sgp_dict(league)
    return standing_projection(league, user, redirect, rosters, ros_proj_b_list, ros_proj_p_list, sgp_dict)


def keeper_standing_projection(league, user, redirect, projected_keepers, ros_proj_b_list, ros_proj_p_list):
    rosters = keeper_to_roster_converter(projected_keepers['projected_keepers'])
    keeper_sgp_dict = {'R SGP': (league.r_sgp_avg or league.r_sgp) / len(league.batting_pos),
                       'HR SGP': (league.hr_sgp_avg or league.hr_sgp) / len(league.batting_pos),
                       'RBI SGP': (league.rbi_sgp_avg or league.rbi_sgp) / len(league.batting_pos),
                       'SB SGP': (league.sb_sgp_avg or league.sb_sgp) / len(league.batting_pos),
                       'OPS SGP': league.ops_sgp_avg or league.ops_sgp, 'AVG SGP': league.avg_sgp_avg or league.avg_sgp,
                       'W SGP': (league.w_sgp_avg or league.w_sgp) / len(league.pitcher_pos),
                       'SV SGP': (league.sv_sgp_avg or league.sv_sgp) / len(league.pitcher_pos),
                       'K SGP': (league.k_sgp_avg or league.k_sgp) / len(league.pitcher_pos),
                       'ERA SGP': league.era_sgp_avg or league.era_sgp,
                       'WHIP SGP': league.whip_sgp_avg or league.whip_sgp}

    return standing_projection(league, user, redirect, rosters, ros_proj_b_list, ros_proj_p_list, keeper_sgp_dict)


def standing_projection(league, user, redirect, rosters, ros_proj_b_list, ros_proj_p_list, sgp_dict):
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

    final_stats = final_stats_projection(rosters, ros_proj_b_list, ros_proj_p_list, current_standings, league)
    volatility_standings = league_volatility(sgp_dict, final_stats)
    ranked_standings = rank_list(volatility_standings)
    return ranked_standings


def create_sgp_dict(league):
    return {'R SGP': league.r_sgp_avg or league.r_sgp, 'HR SGP': league.hr_sgp_avg or league.hr_sgp,
            'RBI SGP': league.rbi_sgp_avg or league.rbi_sgp, 'SB SGP': league.sb_sgp_avg or league.sb_sgp,
            'OPS SGP': league.ops_sgp_avg or league.ops_sgp, 'AVG SGP': league.avg_sgp_avg or league.avg_sgp,
            'W SGP': league.w_sgp_avg or league.w_sgp, 'SV SGP': league.sv_sgp_avg or league.sv_sgp,
            'K SGP': league.k_sgp_avg or league.k_sgp, 'ERA SGP': league.era_sgp_avg or league.era_sgp,
            'WHIP SGP': league.whip_sgp_avg or league.whip_sgp}


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
    keepers = get_keepers(league, user, redirect)
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


def get_draft_values_(league, user, redirect):
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()

    actual_keepers = get_keeper_query(league, user, redirect)
    potential_keepers = get_keepers(league, user, redirect)

    draft_values = get_draft_values(league, ros_proj_b_list, ros_proj_p_list, potential_keepers, actual_keepers)

    keeper_team_stats = analyze_keeper_team_stats(league, user, redirect, draft_values, ros_proj_b_list, ros_proj_p_list)
    ranked_stats = rank_list(keeper_team_stats)

    for key, value in draft_values['projected_keepers'].items():
        for stats in ranked_stats:
            if [mg for mg in value['manager_guids'] if mg in stats['manager_guids']]:
                value['keeper_stats_avg'] = stats
                value['dollar_spent_per_point'] = value['total_cost'] / stats['PointsTotal']

    prev_year_league = league.prev_year_league or league
    draft_status, prev_year_standings = get_league_standings(prev_year_league.league_key, user, redirect)

    prev_year_standings.sort(key=operator.itemgetter('PointsRank'))
    batting_pos = len(prev_year_league.batting_pos)
    pitching_pos = len(prev_year_league.pitcher_pos)

    draft_values['top_three_avg'] = {
        # 'PointsTotal': (prev_year_standings[0]['PointsTotal'] + prev_year_standings[1]['PointsTotal'] + prev_year_standings[2]['PointsTotal']) / 3,
        'StatsTotalGP': ((prev_year_standings[0]['StatsTotalGP'] / batting_pos) + (prev_year_standings[1]['StatsTotalGP'] / batting_pos) + (prev_year_standings[2]['StatsTotalGP'] / batting_pos)) / 3,
        'StatsR': ((prev_year_standings[0]['StatsR'] / batting_pos) + (prev_year_standings[1]['StatsR'] / batting_pos) + (prev_year_standings[2]['StatsR'] / batting_pos)) / 3,
        'StatsHR': ((prev_year_standings[0]['StatsHR'] / batting_pos) + (prev_year_standings[1]['StatsHR'] / batting_pos) + (prev_year_standings[2]['StatsHR'] / batting_pos)) / 3,
        'StatsRBI': ((prev_year_standings[0]['StatsRBI'] / batting_pos) + (prev_year_standings[1]['StatsRBI'] / batting_pos) + (prev_year_standings[2]['StatsRBI'] / batting_pos)) / 3,
        'StatsSB': ((prev_year_standings[0]['StatsSB'] / batting_pos) + (prev_year_standings[1]['StatsSB'] / batting_pos) + (prev_year_standings[2]['StatsSB'] / batting_pos)) / 3,
        'StatsOPS': (prev_year_standings[0]['StatsOPS'] + prev_year_standings[1]['StatsOPS'] + prev_year_standings[2]['StatsOPS']) / 3,
        'StatsIP': ((prev_year_standings[0]['StatsIP'] / pitching_pos) + (prev_year_standings[1]['StatsIP'] / pitching_pos) + (prev_year_standings[2]['StatsIP'] / pitching_pos)) / 3,
        'StatsW': ((prev_year_standings[0]['StatsW'] / pitching_pos) + (prev_year_standings[1]['StatsW'] / pitching_pos) + (prev_year_standings[2]['StatsW'] / pitching_pos)) / 3,
        'StatsSV': ((prev_year_standings[0]['StatsSV'] / pitching_pos) + (prev_year_standings[1]['StatsSV'] / pitching_pos) + (prev_year_standings[2]['StatsSV'] / pitching_pos)) / 3,
        'StatsK': ((prev_year_standings[0]['StatsK'] / pitching_pos) + (prev_year_standings[1]['StatsK'] / pitching_pos) + (prev_year_standings[2]['StatsK'] / pitching_pos)) / 3,
        'StatsERA': (prev_year_standings[0]['StatsERA'] + prev_year_standings[1]['StatsERA'] + prev_year_standings[2]['StatsERA']) / 3,
        'StatsWHIP': (prev_year_standings[0]['StatsWHIP'] + prev_year_standings[1]['StatsWHIP'] + prev_year_standings[2]['StatsWHIP']) / 3
    }

    return draft_values


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
    potential_keepers = get_keepers(league, user, redirect)
    projected_keepers = project_keepers(ros_proj_b_list, ros_proj_p_list, potential_keepers, league)
    keeper_team_stats = analyze_keeper_team_stats(league, user, redirect, projected_keepers, ros_proj_b_list, ros_proj_p_list)
    ranked_stats = rank_list(keeper_team_stats)

    for key, value in projected_keepers['projected_keepers'].items():
        for stats in ranked_stats:
            if [mg for mg in value['manager_guids'] if mg in stats['manager_guids']]:
                value['keeper_stats_avg'] = stats
                value['dollar_spent_per_point'] = value['total_cost'] / stats['PointsTotal']

    end = time.time()
    elapsed = end - start
    print("***************************** %s seconds *****************************" % elapsed)
    return projected_keepers


# TODO: not ready, this needs direction and thought, currently getting an average of batter/pitcher stats kept, but what good is that?
def analyze_keeper_team_stats(league, user, redirect, projected_keepers, ros_proj_b_list, ros_proj_p_list):
    try:
        new_league = League.objects.get(prev_year_league=league)
    except League.DoesNotExist:
        new_league = league
    standings = keeper_standing_projection(new_league, user, redirect, projected_keepers, ros_proj_b_list,
                                           ros_proj_p_list)
    league_needs = []
    for std_team in standings:
        for keeper_team_name, keeper_team_values in projected_keepers['projected_keepers'].items():
            if [mg for mg in std_team['manager_guids'] if mg in keeper_team_values['manager_guids']]:
                batters = 0
                pitchers = 0
                for player in keeper_team_values['players']:
                    if player['category'] == 'batter':
                        batters += 1
                    elif player['category'] == 'pitcher':
                        pitchers += 1

                needs = {'team_name': keeper_team_name, 'manager_guids': keeper_team_values['manager_guids'],
                         'StatsERA': std_team['StatsERA'], 'StatsHR': std_team['StatsHR'] / batters,
                         'StatsIP': std_team['StatsIP'], 'StatsK': std_team['StatsK'] / pitchers,
                         'StatsOPS': std_team['StatsOPS'], 'StatsR': std_team['StatsR'] / batters,
                         'StatsRBI': std_team['StatsRBI'] / batters, 'StatsSB': std_team['StatsSB'] / batters,
                         'StatsSV': std_team['StatsSV'] / pitchers, 'StatsTotalGP': std_team['StatsTotalGP'],
                         'StatsW': std_team['StatsW'] / pitchers, 'StatsWHIP': std_team['StatsWHIP']}
                league_needs.append(needs)

    return league_needs


def trade_analyzer_(league_key, user, redirect, team_a, team_a_players, team_b, team_b_players, team_list):
    ros_proj_b_list = BatterProjection.objects.all()
    ros_proj_p_list = PitcherProjection.objects.all()
    # TODO: change to db call
    league_settings = get_league_settings(league_key, user, redirect)
    league_status, current_standings = get_league_standings(league_key, user, redirect)
    league = user.profile.leagues.get(league_key=league_key)
    update_league(league, draft_status=league_status)

    sgp_dict = create_sgp_dict(league)

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
    lg = league
    if league.draft_status == 'predraft':
        if league.prev_year_league:
            lg = league.prev_year_league
        else:
            lg = dummy_league()
    batters_over_zero_dollars = lg.batters_over_zero_dollars_avg or lg.batters_over_zero_dollars
    one_dollar_batters = lg.one_dollar_batters_avg or lg.one_dollar_batters
    b_dollar_per_fvaaz = lg.b_dollar_per_fvaaz_avg or lg.b_dollar_per_fvaaz
    b_player_pool_mult = lg.b_player_pool_mult_avg or lg.b_player_pool_mult

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
    lg = league
    if league.draft_status == 'predraft':
        if league.prev_year_league:
            lg = league.prev_year_league
        else:
            lg = dummy_league()
    pitchers_over_zero_dollars = lg.pitchers_over_zero_dollars_avg or lg.pitchers_over_zero_dollars
    one_dollar_pitchers = lg.one_dollar_pitchers_avg or lg.one_dollar_pitchers
    p_dollar_per_fvaaz = lg.p_dollar_per_fvaaz_avg or lg.p_dollar_per_fvaaz
    p_player_pool_mult = lg.p_player_pool_mult_avg or lg.p_player_pool_mult

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
    pitcher_list = create_full_pitcher_html(pitcher_url)
    batter_list = create_full_batter_html(batter_url)
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
    lg = league
    if league.draft_status == 'predraft':
        if league.prev_year_league:
            lg = league.prev_year_league
        else:
            lg = dummy_league()
    batters_over_zero_dollars = lg.batters_over_zero_dollars_avg or lg.batters_over_zero_dollars
    one_dollar_batters = lg.one_dollar_batters_avg or lg.one_dollar_batters
    b_dollar_per_fvaaz = lg.b_dollar_per_fvaaz_avg or lg.b_dollar_per_fvaaz
    b_player_pool_mult = lg.b_player_pool_mult_avg or lg.b_player_pool_mult
    pitchers_over_zero_dollars = lg.pitchers_over_zero_dollars_avg or lg.pitchers_over_zero_dollars
    one_dollar_pitchers = lg.one_dollar_pitchers_avg or lg.one_dollar_pitchers
    p_dollar_per_fvaaz = lg.p_dollar_per_fvaaz_avg or lg.p_dollar_per_fvaaz
    p_player_pool_mult = lg.p_player_pool_mult_avg or lg.p_player_pool_mult

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
