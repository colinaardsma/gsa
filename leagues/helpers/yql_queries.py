import json
from operator import itemgetter
from datetime import datetime
import pprint
import heapq
import pytz
import math

from .api_connector import get_json_data, yql_query, check_token_expiration
from ..models import League, calc_three_year_avgs, save_league, update_profile, update_league

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


def get_leagues(user, redirect):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    current_year_dict = get_user_query(user, redirect, "/leagues")
    current_year_league_list = []
    current_year_league_base = (
        current_year_dict['fantasy_content']['users']['0']['user'][1]['games']['0']['game'][1]['leagues'])
    if not current_year_league_base:
        current_year = datetime.now().year
        prev_year_game_id = GAME_ID_DICT[current_year]
        current_year_dict = get_user_query(user, redirect, "/leagues", prev_year_game_id)
        current_year_league_base = (
            current_year_dict['fantasy_content']['users']['0']['user'][1]['games']['0']['game'][1]['leagues'])
    current_year_league_count = current_year_league_base['count']
    for i in range(current_year_league_count):
        league_dict = current_year_league_base['{}'.format(i)]['league'][0]
        current_year_league_list.append(league_dict)
    league_history_list = []
    for current_year_league in current_year_league_list:
        current_year_league_dict = get_league_dict(current_year_league)
        league_history_list.append(current_year_league_dict)

        one_year_prior_league_dict = get_league_dict(current_year_league_dict, True, user, redirect)
        league_history_list.append(one_year_prior_league_dict)

        two_years_prior_league_dict = get_league_dict(one_year_prior_league_dict, True, user, redirect)
        league_history_list.append(two_years_prior_league_dict)

        # TODO: i dont think this is working?
        current_league_start_datetime = datetime.strptime(current_year_league['start_date'], '%Y-%m-%d')
        now = datetime.now()
        if current_league_start_datetime > now:
            three_years_prior_league_dict = get_league_dict(two_years_prior_league_dict, True, user, redirect)
            league_history_list.append(three_years_prior_league_dict)

    sorted_league_history_list = sorted(league_history_list, key=itemgetter('season'), reverse=False)
    return sorted_league_history_list


def get_league_dict(league, get_prev_league=False, user=None, redirect=None):
    league_dict = {}
    if get_prev_league:
        year_prior_league_key = league['prev_year']
        year_prior_dict_base = get_league_query(year_prior_league_key, user, redirect, "")
        league = (year_prior_dict_base['fantasy_content']['leagues']['0']['league'][0])
    league_key = league['league_key']
    league_dict['league_key'] = league_key
    league_dict['name'] = league['name']
    league_dict['season'] = league['season']
    if league['renew'] == '':
        league_dict['prev_year'] = None
        return league_dict
    league_dict['prev_year'] = league['renew'].replace("_", ".l.")
    return league_dict


def get_current_leagues(league_list):
    season = datetime.now().year
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
        team_info_dict = dict([(key, dct[key]) for dct in team_standing_dict[0] for key in dct])

        standing = {}

        managers = team_info_dict['managers']
        manager_guid_list = []
        for manager in managers:
            guid = manager['manager']['guid']
            manager_guid_list.append(guid)
        standing['manager_guids'] = manager_guid_list

        standing['PointsTeam'] = team_info_dict['name']
        standing['StatsTeam'] = standing['PointsTeam']
        standing['Stats'] = {}
        stats = {}

        team_stats_dict = team_standing_dict[1]['team_stats']['stats']
        for stat in team_stats_dict:
            stat_name = STAT_ID_DICT['{}'.format(stat['stat']['stat_id'])]
            stat_value = float(stat['stat']['value'] or 0)
            standing['Stats{}'.format(stat_name)] = stat_value
            if stat_name == '':
                continue
            stats['{}'.format(stat_name)] = {}
            stats['{}'.format(stat_name)]['Stat_Value'] = stat_value

        team_points_dict = team_standing_dict[1]['team_points']['stats']
        for point in team_points_dict:
            stat_name = STAT_ID_DICT['{}'.format(point['stat']['stat_id'])]
            point_value = float(point['stat']['value'] or 0)
            standing['Points{}'.format(stat_name)] = point_value
            if stat_name == '':
                continue
            stats['{}'.format(stat_name)]['Point_Value'] = point_value

        standing['Stats'] = stats
        status = league_standings_base_dict[0]['draft_status']

        if status == 'predraft':
            for key, val in standing.items():
                if key == 'Stats':
                    for k, v in val.items():
                        v['Point_Value'] = 0
                        v['Stat_Value'] = 0
                elif key == 'PointsTeam' or key == 'StatsTeam':
                    continue
                elif 'Points' in key or 'Stats' in key:
                    standing[key] = 0
        else:
            standing['PointsRank'] = float(team_standing_dict[2]['team_standings']['rank'] or 0)
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
    formatted_settings['draft_status'] = league_settings_base_dict[0]['draft_status']
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
    rosters_dict = (query_dict['fantasy_content']['users']['0']['user'][1]['games']['0']['game'][1]['teams'])
    user_team_list = format_single_team_rosters_dict(rosters_dict)
    for team in user_team_list:
        if league_key in team['TEAM_KEY']:
            return team


def format_single_team_rosters_dict(team_rosters_base_dict):
    team_count = team_rosters_base_dict['count']
    rosters = team_rosters_base_dict
    return format_team_rosters_dict(team_count, rosters)


def format_all_team_rosters_dict(team_rosters_base_dict):
    team_count = team_rosters_base_dict[0]['num_teams']
    rosters = team_rosters_base_dict[1]['teams']
    return format_team_rosters_dict(team_count, rosters)


def format_team_rosters_dict(team_count, rosters):
    formatted_rosters = []
    for i in range(team_count):
        team_dict = {}
        team_rosters_dict = rosters['{}'.format(i)]['team']
        team_dict_info = dict([(key, dct[key]) for dct in team_rosters_dict[0] for key in dct])
        team_dict['TEAM_KEY'] = team_dict_info['team_key']
        team_dict['TEAM_NAME'] = team_dict_info['name']
        team_dict['TEAM_NUMBER'] = team_dict_info['team_id']

        managers = team_dict_info['managers']
        manager_guid_list = []
        for manager in managers:
            guid = manager['manager']['guid']
            manager_guid_list.append(guid)
        team_dict['manager_guids'] = manager_guid_list

        roster = []
        if team_rosters_dict[1]:
            roster_dict = team_rosters_dict[1]['roster']['0']['players']
        else:
            roster_dict = team_rosters_dict[2]['roster']['0']['players']
        roster_count = roster_dict['count']
        for j in range(roster_count):
            player_dict = {}
            info = roster_dict['{}'.format(j)]['player'][0]
            player_data_dict = dict([(key, dct[key]) for dct in info for key in dct])

            first_name = player_data_dict['name']['ascii_first']
            last_name = player_data_dict['name']['ascii_last']
            player_name = str(first_name) + " " + str(last_name)
            norm_name = name_normalizer(player_name)
            player_dict['NAME'] = player_name
            player_dict["NORMALIZED_FIRST_NAME"] = norm_name['First']
            player_dict["LAST_NAME"] = norm_name['Last']
            team = player_data_dict['editorial_team_abbr']
            player_dict['POS'] = player_data_dict['display_position'].split(',')
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
            player_data_dict = dict([(key, dct[key]) for dct in player for key in dct])

            player_name = player_data_dict['name']['ascii_first'] + " " + player_data_dict['name']['ascii_last']
            player_dict = {}
            norm_name = name_normalizer(player_name)
            player_dict['NAME'] = player_name
            player_dict["NORMALIZED_FIRST_NAME"] = norm_name['First']
            player_dict["LAST_NAME"] = norm_name['Last']
            if 'status_full' in player_data_dict:
                player_dict['STATUS'] = player_data_dict['status_full']
            else:
                player_dict['STATUS'] = ''
            positions = []
            for pos in player_data_dict['eligible_positions']:
                positions.append(pos['position'])
            player_dict["POS"] = positions
            team = player_data_dict['editorial_team_abbr']
            player_dict['TEAM'] = team_normalizer(team)
            formatted_fas.append(player_dict)
    return formatted_fas


def get_auction_results(league, user, redirect):
    auction_results = {'results': []}

    total_money_spent = 0
    money_spent_on_batters = 0
    money_spent_on_pitchers = 0
    batter_budget_pct = 0.0
    pitcher_budget_pct = 0.0
    total_batters_drafted = 0
    total_pitchers_drafted = 0
    one_dollar_batters = 0
    one_dollar_pitchers = 0

    if isinstance(league, dict):
        if league['draft_status'] == 'predraft':
            league_key = league['prev_year_key']
        else:
            league_key = league['league_key']
    else:
        if league.draft_status == 'predraft':
            league_key = league.prev_year_league.league_key
        else:
            league_key = league.league_key

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
            player_query_results_dict_list.append(get_player_query(query_player_keys, user, redirect, ''))
            max_list_values = i + 25
            query_player_keys[:] = []
        if i < max_list_values:
            query_player_keys.append(player_key)
    player_query_results_dict_list.append(get_player_query(query_player_keys, user, redirect, ''))
    player_data = []
    for results_dict in player_query_results_dict_list:
        data_dict = results_dict['fantasy_content']['players']
        player_count = data_dict['count']
        for i in range(player_count):
            player = {}
            result = data_dict['{}'.format(i)]['player'][0]
            player_dict = dict([(key, dct[key]) for dct in result for key in dct])

            player['player_key'] = player_dict['player_key']
            ascii_first_name = player_dict['name']['ascii_first']
            ascii_last_name = player_dict['name']['ascii_last']
            normalized_name = name_normalizer(ascii_first_name + ' ' + ascii_last_name)
            player['full_name'] = normalized_name['Full']
            player['first_name'] = ascii_first_name
            player['last_name'] = ascii_last_name
            player['status'] = player_dict['status_full'] if 'status_full' in result[3] else ''
            if 'editorial_team_abbr' in player_dict:
                player['team'] = player_dict['editorial_team_abbr']
            else:
                player['team'] = 'FA'
            is_pitcher = True
            if player_dict['position_type'] == 'B':
                player['category'] = 'batter'
                is_pitcher = False
                total_batters_drafted += 1
            if is_pitcher:
                player['category'] = 'pitcher'
                total_pitchers_drafted += 1
            positions = []
            if 'eligible_positions' in player_dict:
                for pos in player_dict['eligible_positions']:
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
    now = datetime.now()
    date = '{year}-{month}-{day}'.format(year=now.year, month=now.month, day=now.day)
    endpoint = '/teams/roster;date={date}'.format(date=date)
    roster_query_results_dict = get_league_query(league_key, user, redirect, endpoint)
    current_rosters_dict = (
        roster_query_results_dict['fantasy_content']['leagues']['0']['league'][1]['teams'])
    team_count = current_rosters_dict['count']
    for i in range(team_count):
        team = {}
        team_data = current_rosters_dict['{}'.format(i)]['team']
        team_dict = dict([(key, dct[key]) for dct in team_data[0] for key in dct])

        team['team_key'] = team_dict['team_key']
        team['team_name'] = team_dict['name']
        team['waiver_priority'] = team_dict['waiver_priority']
        team['faab_balance'] = team_dict['faab_balance']
        if 'auction_budget_total' in team_dict:
            team['auction_budget'] = team_dict['auction_budget_total']
        managers = team_dict['managers']
        manager_guid_list = []
        for manager in managers:
            guid = manager['manager']['guid']
            manager_guid_list.append(guid)
        team['manager_guids'] = manager_guid_list

        roster = []
        roster_dict = team_data[1]['roster']['0']['players']
        if 'count' in roster_dict:
            roster_count = roster_dict['count']
            for j in range(roster_count):
                player = {}
                player_data = roster_dict['{}'.format(j)]['player'][0]
                player_dict = dict([(key, dct[key]) for dct in player_data for key in dct])

                player['player_key'] = player_dict['player_key']
                ascii_first_name = player_dict['name']['ascii_first']
                ascii_last_name = player_dict['name']['ascii_last']
                normalized_name = name_normalizer(ascii_first_name + ' ' + ascii_last_name)
                player['full_name'] = normalized_name['Full']
                player['first_name'] = normalized_name['First']
                player['last_name'] = normalized_name['Last']
                if 'status_full' in player_dict:
                    player['status'] = player_dict['status_full']
                else:
                    player['status'] = ''
                player_team = player_dict['editorial_team_abbr']
                player['team'] = team_normalizer(player_team)
                player['category'] = 'pitcher'
                if 'position_type' in player_dict:
                    if player_dict['position_type'] == 'B':
                        player['category'] = 'batter'
                if 'eligible_positions' in player_dict:
                    positions = player_dict['eligible_positions']
                position_list = []
                for position in positions:
                    pos = position['position']
                    position_list.append(pos)
                player['positions'] = position_list
                roster.append(player)
            team['roster'] = roster
        current_rosters.append(team)
    return current_rosters


def get_league_transactions(league, user, redirect):
    query_dict = get_league_query(league.league_key, user, redirect, "/transactions")
    transactions_dict = query_dict['fantasy_content']['leagues']['0']['league'][1]['transactions']
    transaction_count = transactions_dict['count']
    transactions = []
    for i in range(transaction_count):
        transaction = {}
        players = []
        transaction_list = transactions_dict['{}'.format(i)]['transaction']
        transaction_data = transaction_list[0]
        transaction['transaction_type'] = transaction_data['type']
        transaction['transaction_datetime'] = datetime.fromtimestamp(int(transaction_data['timestamp']))
        if 'faab_bid' in transaction_data:
            transaction['faab_bid'] = transaction_data['faab_bid']
        if 'players' in transaction_list[1]:
            player_dict = transaction_list[1]['players']
            player_count = player_dict['count']
            for j in range(player_count):
                player = {}
                player_list = player_dict['{}'.format(j)]['player']
                # team_dict = dict([(key, dct[key]) for dct in team_data[0] for key in dct])

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


def get_keepers(league, user, redirect):
    if league.draft_status == 'predraft':
        new_league = league
        prev_league = league.prev_year_league
    else:
        prev_league = league
        new_league = ''
    current_rosters = get_current_rosters(prev_league.league_key, user, redirect)
    auction_results = get_auction_results(prev_league, user, redirect)
    league_transactions = get_league_transactions(prev_league, user, redirect)
    list_of_managers = []
    try:
        if not new_league:
            new_league = user.profile.leagues.get(prev_year_key=league.league_key)
        new_current_rosters = get_current_rosters(new_league.league_key, user, redirect)
        for team in new_current_rosters:
            list_of_managers.extend(team['manager_guids'])
    except ModuleNotFoundError:
        for team in current_rosters:
            list_of_managers.extend(team['manager_guids'])
    teams_to_remove = []
    for team in current_rosters:
        if not [mg for mg in team['manager_guids'] if mg in list_of_managers]:
            teams_to_remove.append(team)
        for player in team['roster']:
            # TODO: this is super custom
            player['keeper_cost'] = 5
            player['keeper_found'] = False
            player['preseason_trade'] = False
            player['postseason_trade'] = False
            pickup_found = False
            for transaction in league_transactions:
                if transaction['transaction_datetime'] > prev_league.start_date.replace(tzinfo=None):
                    for plyr in transaction['players']:
                        if plyr['player_key'] == player['player_key'] and not pickup_found:
                            # FA pickup
                            if plyr['source_type'] == 'freeagents':
                                pickup_found = True
                                player['keeper_found'] = True
                                continue
                            # Waiver Claim
                            if plyr['source_type'] == 'waivers':
                                if 'faab_bid' in transaction:
                                    player['keeper_cost'] += int(transaction['faab_bid'])
                                pickup_found = True
                                player['keeper_found'] = True
                                continue
                # Off-season trade
                # else:
                # # TODO: this is super custom, and also could be refactored, not sure this is even possible with how yahoo handles offseason trades, below doesnt work
                # if (not player['preseason_trade'] and transaction['transaction_type'] == 'trade' and
                #         transaction['transaction_datetime'] < league.start_date.replace(tzinfo=None)):
                #     player['preseason_trade'] = True
                #     print(transaction['transaction_datetime'])
                #     print(league.start_date.replace(tzinfo=None))
                #     print("PRESEASON TRADE:")
                #     current_cost = [int(result['cost']) for result in auction_results['results']
                #                     if result['player_key'] == player['player_key']][0]
                #     print(current_cost)
                #     if current_cost <= 10:
                #         continue
                #     else:
                #         player['keeper_found'] = True
                #         reduction = int(math.floor(int(current_cost) / 10.0))
                #         keeper_cost = int(current_cost) - reduction
                #     player['keeper_cost'] = keeper_cost
                #
                # if (not player['postseason_trade'] and transaction['transaction_type'] == 'trade' and
                #         transaction['transaction_datetime'] > league.end_date.replace(tzinfo=None)):
                #     player['postseason_trade'] = True
                #     print(transaction['transaction_datetime'])
                #     print(league.end_date.replace(tzinfo=None))
                #     print("POSTSEASON TRADE:")
                #     current_cost = [int(result['cost']) for result in auction_results['results']
                #                     if result['player_key'] == player['player_key']][0]
                #     print(current_cost)
                #     if current_cost <= 10:
                #         continue
                #     else:
                #         player['keeper_found'] = True
                #         reduction = int(math.floor(int(current_cost) / 10.0))
                #         keeper_cost = int(current_cost) - reduction
                #     player['keeper_cost'] = keeper_cost
            if not pickup_found:
                player['keeper_cost'] += [int(result['cost']) for result in auction_results['results']
                                          if result['player_key'] == player['player_key']][0]
                player['keeper_found'] = True
    current_rosters = [team for team in current_rosters if team not in teams_to_remove]
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
    # TODO: i have no doubt this can be simplified
    for league in leagues:
        settings = get_league_settings(league['league_key'], user, redirect)
        db_league = [db_lg for db_lg in db_leagues if db_lg.league_key == league['league_key']]
        prev_year_db_league = [db_lg for db_lg in db_leagues if db_lg.league_key == league['prev_year']]
        prev_year_league = prev_year_db_league[0] if prev_year_db_league else None
        now = datetime.now()
        #if no league
        if not db_league:
            league_start_datetime = datetime.strptime(settings['start_date'], '%Y-%m-%d')

            # if no league & preseason
            if league_start_datetime > now:
                # if preseason & predraft
                if settings['draft_status'] == 'predraft':
                    save_league(user=user, prev_year_league=prev_year_league, league_name=settings['Name'], league_key=settings['League Key'],
                                team_count=settings['Max Teams'], max_ip=settings['Max Innings Pitched'],
                                batting_pos=settings['Batting POS'], pitcher_pos=settings['Pitching POS'],
                                bench_pos=settings['Bench POS'], dl_pos=settings['DL POS'], na_pos=settings['NA POS'],
                                draft_status=settings['draft_status'], start_date=settings['start_date'],
                                end_date=settings['end_date'], prev_year_key=settings['Prev Year Key'],
                                season=settings['Season'])
                # if preseason & postdraft
                else:
                    results = get_auction_results(league, user, redirect)
                    drafted_batters_over_one_dollar = (results['total_batters_drafted'] - results['one_dollar_batters'])
                    drafted_pitchers_over_one_dollar = (
                            results['total_pitchers_drafted'] - results['one_dollar_pitchers'])

                    batter_fvaaz_over_one_dollar = heapq.nlargest(drafted_batters_over_one_dollar, batter_fvaaz_list)
                    pitcher_fvaaz_over_one_dollar = heapq.nlargest(drafted_pitchers_over_one_dollar, pitcher_fvaaz_list)
                    total_batter_fvaaz_over_one_dollar = sum(batter_fvaaz_over_one_dollar)
                    total_pitcher_fvaaz_over_one_dollar = sum(pitcher_fvaaz_over_one_dollar)

                    batter_budget_over_one_dollar = (results['money_spent_on_batters'] - results['one_dollar_batters'])
                    pitcher_budget_over_one_dollar = (
                            results['money_spent_on_pitchers'] - results['one_dollar_pitchers'])

                    batter_dollar_per_fvaaz = (batter_budget_over_one_dollar / total_batter_fvaaz_over_one_dollar)
                    pitcher_dollar_per_fvaaz = (pitcher_budget_over_one_dollar / total_pitcher_fvaaz_over_one_dollar)

                    b_player_pool_mult = 2.375
                    p_player_pool_mult = 4.45

                    save_league(user=user, prev_year_league=prev_year_league, league_name=settings['Name'],
                                league_key=settings['League Key'], team_count=settings['Max Teams'],
                                max_ip=settings['Max Innings Pitched'], batting_pos=settings['Batting POS'],
                                pitcher_pos=settings['Pitching POS'], bench_pos=settings['Bench POS'],
                                dl_pos=settings['DL POS'], na_pos=settings['NA POS'],
                                draft_status=settings['draft_status'], start_date=settings['start_date'],
                                end_date=settings['end_date'], prev_year_key=settings['Prev Year Key'],
                                season=settings['Season'], batters_over_zero_dollars=results['total_batters_drafted'],
                                pitchers_over_zero_dollars=results['total_pitchers_drafted'],
                                one_dollar_batters=results['one_dollar_batters'],
                                one_dollar_pitchers=results['one_dollar_pitchers'],
                                total_money_spent=results['total_money_spent'],
                                money_spent_on_batters=results['money_spent_on_batters'],
                                money_spent_on_pitchers=results['money_spent_on_pitchers'],
                                batter_budget_pct=results['batter_budget_pct'],
                                pitcher_budget_pct=results['pitcher_budget_pct'],
                                b_dollar_per_fvaaz=batter_dollar_per_fvaaz, p_dollar_per_fvaaz=pitcher_dollar_per_fvaaz,
                                b_player_pool_mult=b_player_pool_mult, p_player_pool_mult=p_player_pool_mult)
                    main_league = league

            # if no league & in season
            else:
                league_status, standings = get_league_standings(league['league_key'], user, redirect)
                results = get_auction_results(league, user, redirect)
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

                save_league(user=user, prev_year_league=prev_year_league, league_name=settings['Name'], league_key=settings['League Key'],
                            team_count=settings['Max Teams'], max_ip=settings['Max Innings Pitched'],
                            batting_pos=settings['Batting POS'], pitcher_pos=settings['Pitching POS'],
                            bench_pos=settings['Bench POS'], dl_pos=settings['DL POS'], na_pos=settings['NA POS'],
                            draft_status=settings['draft_status'], start_date=settings['start_date'],
                            end_date=settings['end_date'], prev_year_key=settings['Prev Year Key'],
                            season=settings['Season'], r_sgp=sgp['R'], hr_sgp=sgp['HR'], rbi_sgp=sgp['RBI'],
                            sb_sgp=sgp['SB'], ops_sgp=ops_sgp, avg_sgp=avg_sgp, w_sgp=sgp['W'], sv_sgp=sgp['SV'],
                            k_sgp=sgp['K'], era_sgp=sgp['ERA'], whip_sgp=sgp['WHIP'],
                            batters_over_zero_dollars=results['total_batters_drafted'],
                            pitchers_over_zero_dollars=results['total_pitchers_drafted'],
                            one_dollar_batters=results['one_dollar_batters'],
                            one_dollar_pitchers=results['one_dollar_pitchers'],
                            total_money_spent=results['total_money_spent'],
                            money_spent_on_batters=results['money_spent_on_batters'],
                            money_spent_on_pitchers=results['money_spent_on_pitchers'],
                            batter_budget_pct=results['batter_budget_pct'],
                            pitcher_budget_pct=results['pitcher_budget_pct'],
                            b_dollar_per_fvaaz=batter_dollar_per_fvaaz, p_dollar_per_fvaaz=pitcher_dollar_per_fvaaz,
                            b_player_pool_mult=b_player_pool_mult, p_player_pool_mult=p_player_pool_mult)

                calc_three_year_avgs(settings['League Key'])
                main_league = league
        #if is league & preseason
        elif db_league[0].start_date.replace(tzinfo=None) > now:
            # if preseason & predraft
            if db_league[0].draft_status == 'predraft':
                update_league(league=db_league[0], user=user, prev_year_league=prev_year_league, league_name=settings['Name'],
                              league_key=settings['League Key'], team_count=settings['Max Teams'],
                              max_ip=settings['Max Innings Pitched'], batting_pos=settings['Batting POS'],
                              pitcher_pos=settings['Pitching POS'], bench_pos=settings['Bench POS'],
                              dl_pos=settings['DL POS'], na_pos=settings['NA POS'],
                              draft_status=settings['draft_status'], start_date=settings['start_date'],
                              end_date=settings['end_date'], prev_year_key=settings['Prev Year Key'],
                              season=settings['Season'])
            # if preseason & postdraft
            else:
                results = get_auction_results(league, user, redirect)
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

                update_league(league=db_league[0], user=user, prev_year_league=prev_year_league,
                              league_name=settings['Name'],
                              league_key=settings['League Key'], team_count=settings['Max Teams'],
                              max_ip=settings['Max Innings Pitched'], batting_pos=settings['Batting POS'],
                              pitcher_pos=settings['Pitching POS'], bench_pos=settings['Bench POS'],
                              dl_pos=settings['DL POS'], na_pos=settings['NA POS'],
                              draft_status=settings['draft_status'], start_date=settings['start_date'],
                              end_date=settings['end_date'], prev_year_key=settings['Prev Year Key'],
                              season=settings['Season'], batters_over_zero_dollars=results['total_batters_drafted'],
                              pitchers_over_zero_dollars=results['total_pitchers_drafted'],
                              one_dollar_batters=results['one_dollar_batters'],
                              one_dollar_pitchers=results['one_dollar_pitchers'],
                              total_money_spent=results['total_money_spent'],
                              money_spent_on_batters=results['money_spent_on_batters'],
                              money_spent_on_pitchers=results['money_spent_on_pitchers'],
                              batter_budget_pct=results['batter_budget_pct'],
                              pitcher_budget_pct=results['pitcher_budget_pct'],
                              b_dollar_per_fvaaz=batter_dollar_per_fvaaz, p_dollar_per_fvaaz=pitcher_dollar_per_fvaaz,
                              b_player_pool_mult=b_player_pool_mult, p_player_pool_mult=p_player_pool_mult)
                main_league = league

        # if league & in season or after season
        else:
            update_league(league=db_league[0], user=user, prev_year_league=prev_year_league)
            calc_three_year_avgs(settings['League Key'])
            main_league = league
    update_profile(user=user, main_league=main_league['league_key'])


# def get_team_query(league_key, user, redirect, endpoint):
#     endpoint = "/teams" + endpoint
#     team_base_dict = get_league_query(league_key, user, redirect, endpoint)
#     return team_base_dict
#
#
# def get_all_team_rosters(league_key, user, redirect):
#     query_dict = get_team_query(league_key, user, redirect, "/roster")
#     rosters_dict = query_dict['fantasy_content']['leagues']['0']['league']
#     return format_all_team_rosters_dict(rosters_dict)


def get_keeper_query(league, user, redirect):
    updated_user = check_token_expiration(user, redirect)
    if updated_user:
        user = updated_user
    keepers = []
    for i in range(league.team_count):
        query_path = f'/team/{league.league_key}.t.{i + 1}/players;status=K'
        team_base_json = yql_query(query_path, user.profile.access_token)
        team_base_dict = json.loads(team_base_json)

        team_data = team_base_dict['fantasy_content']['team']
        team_dict = dict([(key, dct[key]) for dct in team_data[0] for key in dct])

        team = {'team_key': team_dict['team_key'], 'team_name': team_dict['name'],
                'waiver_priority': team_dict['waiver_priority'], 'faab_balance': team_dict['faab_balance']}
        if 'auction_budget_total' in team_dict:
            team['auction_budget'] = team_dict['auction_budget_total']
        managers = team_dict['managers']
        manager_guid_list = []
        for manager in managers:
            guid = manager['manager']['guid']
            manager_guid_list.append(guid)
        team['manager_guids'] = manager_guid_list

        roster = []
        roster_dict = team_data[1]['players']
        if 'count' in roster_dict:
            roster_count = roster_dict['count']
            for j in range(roster_count):
                player = {}
                player_data = roster_dict['{}'.format(j)]['player'][0]
                player_dict = dict([(key, dct[key]) for dct in player_data for key in dct])

                player['player_key'] = player_dict['player_key']
                ascii_first_name = player_dict['name']['ascii_first']
                ascii_last_name = player_dict['name']['ascii_last']
                normalized_name = name_normalizer(ascii_first_name + ' ' + ascii_last_name)
                player['full_name'] = normalized_name['Full']
                player['first_name'] = normalized_name['First']
                player['last_name'] = normalized_name['Last']
                if 'status_full' in player_dict:
                    player['status'] = player_dict['status_full']
                else:
                    player['status'] = ''
                player_team = player_dict['editorial_team_abbr']
                player['team'] = team_normalizer(player_team)
                player['category'] = 'pitcher'
                if 'position_type' in player_dict:
                    if player_dict['position_type'] == 'B':
                        player['category'] = 'batter'
                if 'eligible_positions' in player_dict:
                    positions = player_dict['eligible_positions']
                position_list = []
                for position in positions:
                    pos = position['position']
                    position_list.append(pos)
                player['positions'] = position_list
                roster.append(player)
            team['roster'] = roster
            keepers.append(team)
    return keepers


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
