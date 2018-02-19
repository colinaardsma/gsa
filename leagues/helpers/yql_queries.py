import json
from operator import itemgetter
import datetime
import pprint
import heapq

from .api_connector import get_json_data, yql_query, check_token_expiration
from ..models import League, calc_three_year_avgs, save_league, update_profile

from projections.helpers.normalizer import team_normalizer, name_normalizer
from projections.helpers.advanced_stat_calc import calc_sgp, get_sgp
from projections.models import BatterProjection, PitcherProjection


def get_guid(access_token):
    url = "https://social.yahooapis.com/v1/me/guid"
    raw_json = get_json_data(url, access_token)
    return raw_json


def get_prev_year_league(current_league_dict):
    fantasy_content = current_league_dict['fantasy_content']
    if 'users' in fantasy_content:
        fantasy_content = fantasy_content['users']['0']['user'][1]['games']['0']['game'][1]
    prev_year_id = fantasy_content['leagues']['0']['league'][0]['renew']
    prev_year_id = prev_year_id.replace("_", ".l.")
    return prev_year_id


def get_league_query(league_key, user, redirect, endpoint):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    query_path = "/leagues;league_keys=" + league_key + endpoint
    league_base_json = yql_query(query_path, user.profile.access_token)
    league_base_dict = json.loads(league_base_json)
    return league_base_dict


def get_player_query(player_keys, user, redirect, endpoint):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    player_key_string = ",".join(player_keys)
    query_path = "/players;player_keys=" + player_key_string + endpoint
    league_base_json = yql_query(query_path, user.profile.access_token)
    league_base_dict = json.loads(league_base_json)
    return league_base_dict


def get_league_settings(league_key, user, redirect):
    query_dict = get_league_query(league_key, user, redirect, "/settings")
    settings_dict = query_dict['fantasy_content']['leagues']['0']['league']
    return format_league_settings_dict(settings_dict)


def get_league_standings(league_key, user, redirect):
    query_dict = get_league_query(league_key, user, redirect, "/standings")
    standings_dict = query_dict['fantasy_content']['leagues']['0']['league']
    return format_league_standings_dict(standings_dict)


def get_league_players(league_key, user, redirect, player_type):
    # player types:
    # A (all available players)
    # FA (free agents only)
    # W (waivers only)
    # T (all taken players)
    # K (keepers only)
    endpoint = "/players;status=" + player_type
    query_dict = get_league_query(league_key, user, redirect, endpoint)
    players_dict = query_dict['fantasy_content']['leagues']['0']['league']
    return players_dict
    # return format_players_dict(players_dict)


def get_user_query(user, redirect, endpoint, game_id = "mlb"):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    query_path = "/users;use_login=1/games;game_keys=" + str(game_id) + endpoint
    user_base_json = yql_query(query_path, user.profile.access_token)
    user_base_dict = json.loads(user_base_json)
    return user_base_dict


# TODO: handle if current league is pre-season
def get_leagues(user, redirect):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    current_year_dict = get_user_query(user, redirect, "/leagues")
    current_year_league_list = []
    current_year_league_base = (current_year_dict['fantasy_content']['users']['0']
                                                 ['user'][1]['games']['0']['game'][1]['leagues'])
    if not current_year_league_base:
        current_year = datetime.datetime.now().year
        prev_year_game_id = GAME_ID_DICT[current_year]
        current_year_dict = get_user_query(user, redirect, "/leagues", prev_year_game_id)
        current_year_league_base = (current_year_dict['fantasy_content']['users']['0']
        ['user'][1]['games']['0']['game'][1]['leagues'])
    current_year_league_count = current_year_league_base['count']
    for i in range(current_year_league_count):
        league_dict = current_year_league_base['{}'.format(i)]['league'][0]
        current_year_league_list.append(league_dict)
    league_history_list = []
    for current_year_league in current_year_league_list:
        current_year_league_dict = {}
        current_year_league_key = current_year_league['league_key']
        current_year_league_dict['league_key'] = current_year_league_key
        current_year_league_dict['name'] = current_year_league['name']
        current_year_league_dict['season'] = current_year_league['season']
        if current_year_league['renew'] == '':
            current_year_league_dict['prev_year'] = None
            league_history_list.append(current_year_league_dict)
            continue
        current_year_league_dict['prev_year'] = current_year_league['renew'].replace("_", ".l.")
        league_history_list.append(current_year_league_dict)

        one_year_prior_league_dict = {}
        one_year_prior_league_key = current_year_league_dict['prev_year']
        one_year_prior_dict_base = get_league_query(one_year_prior_league_key,
                                                    user, redirect, "")
        one_year_prior_dict = (one_year_prior_dict_base['fantasy_content']['leagues']['0']
        ['league'][0])
        one_year_prior_league_dict['league_key'] = one_year_prior_league_key
        one_year_prior_league_dict['season'] = one_year_prior_dict['season']
        one_year_prior_league_dict['name'] = one_year_prior_dict['name']
        if one_year_prior_dict['renew'] == '':
            one_year_prior_league_dict['prev_year'] = None
            league_history_list.append(one_year_prior_league_dict)
            continue
        one_year_prior_league_dict['prev_year'] = one_year_prior_dict['renew'].replace("_", ".l.")
        league_history_list.append(one_year_prior_league_dict)

        two_years_prior_league_dict = {}
        two_years_prior_league_key = one_year_prior_league_dict['prev_year']
        two_years_prior_dict_base = get_league_query(two_years_prior_league_key, user,
                                                     redirect, "")
        two_years_prior_dict = (two_years_prior_dict_base['fantasy_content']['leagues']['0']
        ['league'][0])
        two_years_prior_league_dict['league_key'] = two_years_prior_league_key
        two_years_prior_league_dict['season'] = two_years_prior_dict['season']
        two_years_prior_league_dict['name'] = two_years_prior_dict['name']
        if two_years_prior_dict['renew'] == '':
            two_years_prior_league_dict['prev_year'] = None
            league_history_list.append(two_years_prior_league_dict)
            continue
        two_years_prior_league_dict['prev_year'] = two_years_prior_dict['renew'].replace("_", ".l.")
        league_history_list.append(two_years_prior_league_dict)
    sorted_league_history_list = sorted(league_history_list, key=itemgetter('season'), reverse=False)
    return sorted_league_history_list


def get_current_leagues(league_list):
    season = datetime.datetime.now().year
    current_leagues = []
    while len(current_leagues) < 1:
        current_leagues = [l for l in league_list if l['season'] == str(season)]
        season -= 1
    return current_leagues


def format_league_standings_dict(league_standings_base_dict):
    team_count = league_standings_base_dict[1]['standings'][0]['teams']['count']
    standings = league_standings_base_dict[1]['standings'][0]['teams']

    formatted_standings = []
    for i in range(team_count):
        team_standing_dict = standings['{}'.format(i)]['team']
        team_info_dict = team_standing_dict[0]

        standing = {}
        standing['PointsTeam'] = [x['name'] for x in team_info_dict if 'name' in x][0]
        standing['StatsTeam'] = standing['PointsTeam']
        standing['Stats'] = {}
        stats = {}

        team_stats_dict = team_standing_dict[1]['team_stats']['stats']
        for stat in team_stats_dict:
            stat_name = STAT_ID_DICT['{}'.format(stat['stat']['stat_id'])]
            stat_value = float(stat['stat']['value']) if stat['stat']['value'] != "" else stat['stat']['value']
            standing['Stats{}'.format(stat_name)] = stat_value
            if stat_name == '':
                continue
            stats['{}'.format(stat_name)] = {}
            stats['{}'.format(stat_name)]['Stat_Value'] = stat_value

        team_points_dict = team_standing_dict[1]['team_points']['stats']
        for point in team_points_dict:
            stat_name = STAT_ID_DICT['{}'.format(point['stat']['stat_id'])]
            point_value = float(point['stat']['value']) if point['stat']['value'] != "" else point['stat']['value']
            standing['Points{}'.format(stat_name)] = point_value
            if stat_name == '':
                continue
            stats['{}'.format(stat_name)]['Point_Value'] = point_value

        standing['Stats'] = stats
        status = league_standings_base_dict[0]['draft_status']

        if status != 'predraft':
            standing['PointsRank'] = int(team_standing_dict[2]['team_standings']['rank'])
        else:
            standing['PointsRank'] = 0
        standing['StatsRank'] = standing['PointsRank']

        formatted_standings.append(standing)
    return status, formatted_standings


def format_league_settings_dict(league_settings_base_dict):
    formatted_settings = {}
    roster_pos_base = league_settings_base_dict[1]['settings'][0]['roster_positions']
    pitching_list = []
    bench_list = []
    dl_list = []
    batting_list = []
    na_list = []
    for pos in roster_pos_base:
        pos_dict = pos['roster_position']
        if pos_dict['position'] == 'BN':
            for i in range(int(pos_dict['count'])):
                bench_list.append('BN')
        elif pos_dict['position'] == 'NA':
            for i in range(int(pos_dict['count'])):
                na_list.append('NA')
        elif pos_dict['position'] == 'DL':
            for i in range(int(pos_dict['count'])):
                dl_list.append('DL')
        elif pos_dict['position_type'] == 'B':
            for i in range(int(pos_dict['count'])):
                batting_list.append(str(pos_dict['position']))
        elif pos_dict['position_type'] == 'P':
            for i in range(int(pos_dict['count'])):
                pitching_list.append(str(pos_dict['position']))
    formatted_settings['Roster Positions'] = {}
    formatted_settings['Roster Positions']['Pitching POS'] = pitching_list
    formatted_settings['Roster Positions']['Bench POS'] = bench_list
    formatted_settings['Roster Positions']['DL POS'] = dl_list
    formatted_settings['Roster Positions']['Batting POS'] = batting_list
    formatted_settings['Roster Positions']['NA POS'] = na_list
    formatted_settings['Pitching POS'] = pitching_list
    formatted_settings['Bench POS'] = bench_list
    formatted_settings['DL POS'] = dl_list
    formatted_settings['Batting POS'] = batting_list
    formatted_settings['NA POS'] = na_list
    formatted_settings['Max Teams'] = league_settings_base_dict[0]['num_teams']
    formatted_settings['Season'] = int(league_settings_base_dict[0]['season'])
    formatted_settings['Name'] = league_settings_base_dict[0]['name']
    formatted_settings['League Key'] = league_settings_base_dict[0]['league_key']
    formatted_settings['Prev Year Key'] = league_settings_base_dict[0]['renew'].replace("_", ".l.")
    formatted_settings['Max Innings Pitched'] = int(league_settings_base_dict[1]['settings'][1]['max_innings_pitched'])
    formatted_settings['start_date'] = league_settings_base_dict[0]['start_date']
    formatted_settings['end_date'] = league_settings_base_dict[0]['end_date']
    return formatted_settings


def get_team_query(league_key, user, redirect, endpoint):
    endpoint = "/teams" + endpoint
    team_base_dict = get_league_query(league_key, user, redirect, endpoint)
    return team_base_dict


def get_all_team_rosters(league_key, user, redirect):
    query_dict = get_team_query(league_key, user, redirect, "/roster")
    rosters_dict = query_dict['fantasy_content']['leagues']['0']['league']
    return format_all_team_rosters_dict(rosters_dict)


def get_single_team_roster(league_key, user, redirect):
    game_id = league_key.split(".l.")[0]
    query_dict = get_user_query(user, redirect, "/teams/roster", game_id)
    rosters_dict = (query_dict['fantasy_content']['users']['0']['user'][1]
    ['games']['0']['game'][1]['teams'])
    user_team_list = format_single_team_rosters_dict(rosters_dict)
    for team in user_team_list:
        if league_key in team['TEAM_KEY']:
            return team


# TODO: don't need 2 methods that do effectively the same thing, combine these
def format_single_team_rosters_dict(team_rosters_base_dict):
    team_count = team_rosters_base_dict['count']
    rosters = team_rosters_base_dict

    formatted_rosters = []
    for i in range(team_count):
        team_dict = {}
        team_rosters_dict = rosters['{}'.format(i)]['team']
        team_dict['TEAM_NAME'] = team_rosters_dict[0][2]['name']
        team_dict['TEAM_NUMBER'] = team_rosters_dict[0][1]['team_id']
        team_dict['TEAM_KEY'] = team_rosters_dict[0][0]['team_key']
        roster = []
        roster_count = team_rosters_dict[2]['roster']['0']['players']['count']
        for j in range(roster_count):
            player_dict = {}
            for info in team_rosters_dict[2]['roster']['0']['players']['{}'.format(j)]['player'][0]:
                if 'name' in info:
                    first_name = info['name']['ascii_first']
                    last_name = info['name']['ascii_last']
                    player_name = str(first_name) + " " + str(last_name)
                    norm_name = name_normalizer(player_name)
                    player_dict['NAME'] = player_name
                    player_dict["NORMALIZED_FIRST_NAME"] = norm_name['First']
                    player_dict["LAST_NAME"] = norm_name['Last']
                if 'editorial_team_abbr' in info:
                    team = info['editorial_team_abbr']
                    player_dict['TEAM'] = team_normalizer(team)
            roster.append(player_dict)
        team_dict['ROSTER'] = roster
        formatted_rosters.append(team_dict)
    return formatted_rosters


def format_all_team_rosters_dict(team_rosters_base_dict):
    team_count = team_rosters_base_dict[0]['num_teams']
    rosters = team_rosters_base_dict[1]['teams']

    formatted_rosters = []
    for i in range(team_count):
        team_dict = {}
        team_rosters_dict = rosters['{}'.format(i)]['team']
        team_dict['TEAM_NAME'] = team_rosters_dict[0][2]['name']
        team_dict['TEAM_NUMBER'] = team_rosters_dict[0][1]['team_id']
        roster = []
        roster_count = team_rosters_dict[1]['roster']['0']['players']['count']
        for j in range(roster_count):
            player_dict = {}
            for info in team_rosters_dict[1]['roster']['0']['players']['{}'.format(j)]['player'][0]:
                if 'name' in info:
                    first_name = info['name']['ascii_first']
                    last_name = info['name']['ascii_last']
                    player_name = str(first_name) + " " + str(last_name)
                    norm_name = name_normalizer(player_name)
                    player_dict['NAME'] = player_name
                    player_dict["NORMALIZED_FIRST_NAME"] = norm_name['First']
                    player_dict["LAST_NAME"] = norm_name['Last']
                if 'editorial_team_abbr' in info:
                    team = info['editorial_team_abbr']
                    player_dict['TEAM'] = team_normalizer(team)
            roster.append(player_dict)
        team_dict['ROSTER'] = roster
        formatted_rosters.append(team_dict)
    return formatted_rosters


def get_teams(user, redirect):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    teams_query_path = get_user_query(user, redirect, "/teams")
    teams_query_json = yql_query(teams_query_path, user.profile.access_token)
    teams_dict = json.loads(teams_query_json)
    return teams_dict


def get_players(league_key, user, redirect, total_players, pOrB, player_list_type):
    formatted_fas = []
    count = 25
    total_players = total_players
    for i in range(0, total_players, count):
        player_type = player_list_type + ";sort=AR;position=" + pOrB + ";count=" + str(count) + ";start=" + str(i)
        fa_dict = get_league_players(league_key, user, redirect, player_type)
        for j in range(count):
            player = fa_dict[1]['players']['{}'.format(j)]['player'][0]
            player_name = player[2]['name']['ascii_first'] + " " + player[2]['name']['ascii_last']
            player_dict = {}
            norm_name = name_normalizer(player_name)
            player_dict['NAME'] = player_name
            player_dict["NORMALIZED_FIRST_NAME"] = norm_name['First']
            player_dict["LAST_NAME"] = norm_name['Last']
            if 'status_full' in player[3]:
                player_dict['STATUS'] = player[3]['status_full']
            else:
                player_dict['STATUS'] = ''
            positions = []
            if 'eligible_positions' in player[12]:
                for pos in player[12]['eligible_positions']:
                    positions.append(pos['position'])
            elif 'eligible_positions' in player[13]:
                for pos in player[13]['eligible_positions']:
                    positions.append(pos['position'])
            else:
                positions.append('')
            player_dict["POS"] = positions
            team = ""
            for info in player:
                if 'editorial_team_abbr' in info:
                    team = info['editorial_team_abbr']
                    player_dict['TEAM'] = team_normalizer(team)
            formatted_fas.append(player_dict)
    return formatted_fas


def get_auction_results(league_key, user, redirect):
    auction_results = {}
    auction_results['results'] = []

    total_money_spent = 0
    money_spent_on_batters = 0
    money_spent_on_pitchers = 0
    batter_budget_pct = 0.0
    pitcher_budget_pct = 0.0
    total_batters_drafted = 0
    total_pitchers_drafted = 0
    one_dollar_batters = 0
    one_dollar_pitchers = 0

    auction_results['results'] = []
    auction_query_results_dict = get_league_query(league_key, user, redirect, '/draftresults')
    auction_results_dict = auction_query_results_dict['fantasy_content']['leagues']['0']['league'][1]['draft_results']
    auction_count = auction_results_dict['count']
    all_player_keys = []
    for i in range(auction_count):
        result = auction_results_dict['{}'.format(i)]['draft_result']
        auction_result = {}
        auction_result['cost'] = int(result['cost'])
        total_money_spent += int(result['cost'])
        auction_result['player_key'] = result['player_key']
        auction_result['team_key'] = result['team_key']
        all_player_keys.append(result['player_key'])
        auction_results['results'].append(auction_result)
    max_list_values = 25
    query_player_keys = []
    player_query_results_dict_list = []
    for i, player_key in enumerate(all_player_keys):
        if i != 0 and i % 25 == 0:
            player_query_results_dict_list.append(get_player_query(query_player_keys,
                                                                   user, redirect, ''))
            max_list_values = i + 25
            query_player_keys[:] = []
        if i < max_list_values:
            query_player_keys.append(player_key)
    player_query_results_dict_list.append(get_player_query(query_player_keys, user,
                                                           redirect, ''))
    player_data = []
    for results_dict in player_query_results_dict_list:
        data_dict = results_dict['fantasy_content']['players']
        player_count = data_dict['count']
        for i in range(player_count):
            player = {}
            result = data_dict['{}'.format(i)]['player'][0]
            player['player_key'] = result[0]['player_key']
            ascii_first_name = result[2]['name']['ascii_first']
            ascii_last_name = result[2]['name']['ascii_last']
            normalized_name = name_normalizer(ascii_first_name + ' ' + ascii_last_name)
            player['full_name'] = normalized_name['Full']
            player['first_name'] = ascii_first_name
            player['last_name'] = ascii_last_name
            player['status'] = result[3]['status_full'] if 'status_full' in result[3] else ''
            if 'editorial_team_abbr' in result[6]:
                player['team'] = result[6]['editorial_team_abbr']
            elif 'editorial_team_abbr' in result[7]:
                player['team'] = result[7]['editorial_team_abbr']
            else:
                player['team'] = 'FA'
            is_pitcher = True
            if 'position_type' in result[11]:
                if result[11]['position_type'] == 'B':
                    player['category'] = 'batter'
                    is_pitcher = False
                    total_batters_drafted += 1
            elif 'position_type' in result[12]:
                if result[12]['position_type'] == 'B':
                    player['category'] = 'batter'
                    is_pitcher = False
                    total_batters_drafted += 1
            if is_pitcher:
                player['category'] = 'pitcher'
                total_pitchers_drafted += 1
            positions = []
            if 'eligible_positions' in result[12]:
                for pos in result[12]['eligible_positions']:
                    positions.append(pos['position'])
            elif 'eligible_positions' in result[13]:
                for pos in result[13]['eligible_positions']:
                    positions.append(pos['position'])
            else:
                positions.append('')
            player['pos'] = positions
            player_data.append(player)
    for i, auction_result in enumerate(auction_results['results']):
        auction_result['first_name'] = player_data[i]['first_name']
        auction_result['last_name'] = player_data[i]['last_name']
        auction_result['status'] = player_data[i]['status']
        auction_result['pos'] = player_data[i]['pos']
        if player_data[i]['category'] == 'batter':
            money_spent_on_batters += auction_result['cost']
            if auction_result['cost'] == 1:
                one_dollar_batters += 1
        if player_data[i]['category'] == 'pitcher':
            money_spent_on_pitchers += auction_result['cost']
            if auction_result['cost'] == 1:
                one_dollar_pitchers += 1
    batter_budget_pct = float(money_spent_on_batters) / float(total_money_spent)
    pitcher_budget_pct = float(money_spent_on_pitchers) / float(total_money_spent)

    auction_results['total_batters_drafted'] = total_batters_drafted
    auction_results['total_pitchers_drafted'] = total_pitchers_drafted
    auction_results['total_money_spent'] = total_money_spent
    auction_results['money_spent_on_batters'] = money_spent_on_batters
    auction_results['money_spent_on_pitchers'] = money_spent_on_pitchers
    auction_results['batter_budget_pct'] = batter_budget_pct
    auction_results['pitcher_budget_pct'] = pitcher_budget_pct
    auction_results['one_dollar_batters'] = one_dollar_batters
    auction_results['one_dollar_pitchers'] = one_dollar_pitchers

    return auction_results


# http://fantasysports.yahooapis.com/fantasy/v2/leagues;league_keys=370.l.5091/teams/roster;date=2017-11-28
def get_current_rosters(league_key, user, redirect):
    current_rosters = []
    now = datetime.datetime.now()
    date = '{year}-{month}-{day}'.format(year=now.year, month=now.month, day=now.day)
    endpoint = '/teams/roster;date={date}'.format(date=date)
    roster_query_results_dict = get_league_query(league_key, user, redirect, endpoint)
    current_rosters_dict = (roster_query_results_dict['fantasy_content']['leagues']['0']
    ['league'][1]['teams'])
    team_count = current_rosters_dict['count']
    for i in range(team_count):
        team = {}
        team_data = current_rosters_dict['{}'.format(i)]['team']
        team['team_key'] = team_data[0][0]['team_key']
        team['team_name'] = team_data[0][2]['name']
        team['waiver_priority'] = team_data[0][7]['waiver_priority']
        team['faab_balance'] = team_data[0][8]['faab_balance']
        managers = team_data[0][19]['managers']
        manager_guid_list = []
        for manager in managers:
            guid = manager['manager']['guid']
            manager_guid_list.append(guid)
        team['manager_guids'] = manager_guid_list
        roster = []
        roster_dict = team_data[1]['roster']['0']['players']
        roster_count = roster_dict['count']
        for j in range(roster_count):
            player = {}
            player_data = roster_dict['{}'.format(j)]['player'][0]
            player['player_key'] = player_data[0]['player_key']
            ascii_first_name = player_data[2]['name']['ascii_first']
            ascii_last_name = player_data[2]['name']['ascii_last']
            normalized_name = name_normalizer(ascii_first_name + ' ' + ascii_last_name)
            player['full_name'] = normalized_name['Full']
            player['first_name'] = ascii_first_name
            player['last_name'] = ascii_last_name
            if 'status_full' in player_data[3]:
                player['status'] = player_data[3]['status_full']
            else:
                player['status'] = ''
            if 'editorial_team_abbr' in player_data[6]:
                player['team'] = player_data[6]['editorial_team_abbr']
            elif 'editorial_team_abbr' in player_data[7]:
                player['team'] = player_data[7]['editorial_team_abbr']
            else:
                player['team'] = 'FA'
            player['category'] = 'pitcher'
            if 'position_type' in player_data[10]:
                if player_data[10]['position_type'] == 'B':
                    player['category'] = 'batter'
            elif 'position_type' in player_data[11]:
                if player_data[11]['position_type'] == 'B':
                    player['category'] = 'batter'
            elif 'position_type' in player_data[12]:
                if player_data[12]['position_type'] == 'B':
                    player['category'] = 'batter'
            if 'eligible_positions' in player_data[11]:
                positions = player_data[11]['eligible_positions']
            elif 'eligible_positions' in player_data[12]:
                positions = player_data[12]['eligible_positions']
            elif 'eligible_positions' in player_data[13]:
                positions = player_data[13]['eligible_positions']
            position_list = []
            for position in positions:
                pos = position['position']
                position_list.append(pos)
            player['positions'] = position_list
            roster.append(player)
        team['roster'] = roster
        current_rosters.append(team)
    return current_rosters


def get_league_transactions(league_key, user, redirect):
    query_dict = get_league_query(league_key, user, redirect, "/transactions")
    transactions_dict = query_dict['fantasy_content']['leagues']['0']['league'][1]['transactions']
    transaction_count = transactions_dict['count']
    transactions = []
    for i in range(transaction_count):
        transaction = {}
        players = []
        transaction_list = transactions_dict['{}'.format(i)]['transaction']
        transaction_data = transaction_list[0]
        transaction['transaction_type'] = transaction_data['type']
        transaction['transaction_datetime'] = datetime.datetime.fromtimestamp(int(transaction_data['timestamp'])).strftime('%Y-%m-%d %H:%M:%S')
        if 'faab_bid' in transaction_data:
            transaction['faab_bid'] = transaction_data['faab_bid']
        if 'players' in transaction_list[1]:
            player_dict = transaction_list[1]['players']
            player_count = player_dict['count']
            for j in range(player_count):
                player = {}
                player_list = player_dict['{}'.format(j)]['player']
                player['player_key'] = player_list[0][0]['player_key']
                ascii_first_name = player_list[0][2]['name']['ascii_first']
                ascii_last_name = player_list[0][2]['name']['ascii_last']
                normalized_name = name_normalizer(ascii_first_name + ' ' + ascii_last_name)
                player['full_name'] = normalized_name['Full']
                player['first_name'] = ascii_first_name
                player['last_name'] = ascii_last_name
                player['team'] = player_list[0][3]['editorial_team_abbr']
                player['pos'] = player_list[0][4]['display_position'].split(',')
                if player_list[0][5]['position_type'] == 'B':
                    player['category'] = 'batter'
                else:
                    player['category'] = 'pitcher'
                player_trans_data = player_list[1]['transaction_data']
                player_transaction_data = {}
                if isinstance(player_trans_data, list):
                    player_transaction_data = player_trans_data[0]
                else:
                    player_transaction_data = player_trans_data
                player['transaction_type'] = player_transaction_data['type']
                player['source_type'] = player_transaction_data['source_type']
                if player_transaction_data['type'] == "add":
                    player['destination_type'] = player_transaction_data['destination_type']
                    player['destination_team'] = player_transaction_data['destination_team_name']
                    player['destination_team_key'] = player_transaction_data['destination_team_key']
                if (player_transaction_data['type'] == "trade"
                        or player_transaction_data['type'] == "drop"):
                    player['source_team'] = player_transaction_data['source_team_name']
                    player['source_team_key'] = player_transaction_data['source_team_key']
                players.append(player)
        transaction['players'] = players
        transactions.append(transaction)
    return transactions


def get_keepers(league_key, user, redirect):
    current_rosters = get_current_rosters(league_key, user, redirect)
    auction_results = get_auction_results(league_key, user, redirect)
    league_transactions = get_league_transactions(league_key, user, redirect)

    for team in current_rosters:
        for player in team['roster']:
            player['keeper_cost'] = 5
            player['keeper_found'] = False
            transaction_found = False
            for transaction in league_transactions:
                for plyr in transaction['players']:
                    if plyr['player_key'] == player['player_key']:
                        # FA pickup
                        if plyr['source_type'] == 'freeagents':
                            transaction_found = True
                            player['keeper_found'] = True
                            continue
                        # Waiver Claim
                        if plyr['source_type'] == 'waivers':
                            if 'faab_bid' in transaction:
                                player['keeper_cost'] += int(transaction['faab_bid'])
                            transaction_found = True
                            player['keeper_found'] = True
                            continue
                if transaction_found:
                    continue
            if not transaction_found:
                player['keeper_cost'] += [int(result['cost']) for result in auction_results['results']
                                          if result['player_key'] == player['player_key']][0]
                player['keeper_found'] = True
    return current_rosters


def update_leagues(user, redirect):
    leagues = get_leagues(user, redirect)
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
            settings = get_league_settings(league['league_key'], user, redirect)
            league_status, standings = get_league_standings(league['league_key'], user, redirect)
            results = get_auction_results(league['league_key'], user, redirect)
            sgp = get_sgp(standings)
            avg_sgp = 0.00
            ops_sgp = 0.00
            drafted_batters_over_one_dollar = (results['total_batters_drafted'] - results['one_dollar_batters'])
            drafted_pitchers_over_one_dollar = (results['total_pitchers_drafted'] - results['one_dollar_pitchers'])

            batter_fvaaz_over_one_dollar = heapq.nlargest(drafted_batters_over_one_dollar, batter_fvaaz_list)
            pitcher_fvaaz_over_one_dollar = heapq.nlargest(drafted_pitchers_over_one_dollar, pitcher_fvaaz_list)
            total_batter_fvaaz_over_one_dollar = sum(batter_fvaaz_over_one_dollar)
            total_pitcher_fvaaz_over_one_dollar = sum(pitcher_fvaaz_over_one_dollar)

            batter_budget_over_one_dollar = (results['money_spent_on_batters'] - results['one_dollar_batters'])
            pitcher_budget_over_one_dollar = (results['money_spent_on_pitchers'] - results['one_dollar_pitchers'])

            batter_dollar_per_fvaaz = (batter_budget_over_one_dollar / total_batter_fvaaz_over_one_dollar)
            pitcher_dollar_per_fvaaz = (pitcher_budget_over_one_dollar / total_pitcher_fvaaz_over_one_dollar)

            b_player_pool_mult = 2.375
            p_player_pool_mult = 4.45

            if 'AVG' in sgp:
                avg_sgp = sgp['AVG']
            if 'OPS' in sgp:
                ops_sgp = sgp['OPS']

            save_league(user, settings['Name'], settings['League Key'], settings['Max Teams'],
                        settings['Max Innings Pitched'], settings['Batting POS'], settings['Pitching POS'],
                        settings['Bench POS'], settings['DL POS'], settings['NA POS'], league_status,
                        settings['start_date'], settings['end_date'], settings['Prev Year Key'], settings['Season'],
                        sgp['R'], sgp['HR'], sgp['RBI'], sgp['SB'], ops_sgp, avg_sgp, sgp['W'], sgp['SV'], sgp['K'],
                        sgp['ERA'], sgp['WHIP'], results['total_batters_drafted'], results['total_pitchers_drafted'],
                        results['one_dollar_batters'], results['one_dollar_pitchers'],
                        results['total_money_spent'], results['money_spent_on_batters'],
                        results['money_spent_on_pitchers'], results['batter_budget_pct'], results['pitcher_budget_pct'],
                        batter_dollar_per_fvaaz, pitcher_dollar_per_fvaaz, b_player_pool_mult, p_player_pool_mult)

            calc_three_year_avgs(settings['League Key'])
        else:
            db_league.users.add(user)
        main_league = league
    update_profile(user, main_league=main_league['league_key'])


STAT_ID_DICT = {'1': 'TotalGP',
                '60': '',
                '7': 'R',
                '12': 'HR',
                '13': 'RBI',
                '16': 'SB',
                '55': 'OPS',
                '50': 'IP',
                '28': 'W',
                '32': 'SV',
                '42': 'K',
                '26': 'ERA',
                '27': 'WHIP'}

GAME_ID_DICT = {2018: 'mlb',
                2017: 370,
                2016: 357,
                2015: 346,
                2014: 328,
                2013: 308,
                2012: 268,
                2011: 253,
                2010: 238,
                2009: 215,
                2008: 195,
                2007: 171,
                2006: 147,
                2005: 113}
