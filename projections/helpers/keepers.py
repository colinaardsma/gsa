import csv
import heapq
import pprint

from .player_creator import calc_batter_z_score, calc_pitcher_z_score
from .data_analysis import evaluate_keepers
from .normalizer import player_comparer
from ..models import BatterProjection, PitcherProjection


def analyze_csv(csv_file):
    csv_dict_list = []
    with open(csv_file) as csv_content:
        dict_reader = csv.DictReader(csv_content, delimiter='\t')
        for row in dict_reader:
            csv_dict_list.append(row)
    return csv_dict_list


def keeper_dict_by_team(dict_list):
    keeper_team_dict = {}
    for player in dict_list:
        team_name = player['fantasy_team']
        if team_name not in keeper_team_dict:
            keeper_team_dict[team_name] = {}
            keeper_team_dict[team_name]['manager_guids'] = player['manager_guids']
            keeper_team_dict[team_name]['total_cost'] = 0
            keeper_team_dict[team_name]['players'] = []
        if player['worth_keeping']:
            keeper_team_dict[team_name]['total_cost'] += player['keeper_cost']
            keeper_team_dict[team_name]['players'].append(player)
    return keeper_team_dict


def keeper_team_dict_creator(csv_file):
    csv_dict_list = analyze_csv(csv_file)
    keeper_team_dict = keeper_dict_by_team(csv_dict_list)
    return keeper_team_dict


def batter_projections():
    csv_dict_list = analyze_csv('BatterProjections.tsv')
    return csv_dict_list


def remove_projected_keepers(keeper_dict_list, batter_dict_list, pitcher_dict_list):
    #TODO: if batter_dict_list and pitcher_dict_list are cast as dicts then many players are missed, why?
    remaining_batters, batter_dollars_kept = get_remaining_players(keeper_dict_list, batter_dict_list)
    remaining_pitchers, pitcher_dollars_kept = get_remaining_players(keeper_dict_list, pitcher_dict_list)
    dollars_kept = batter_dollars_kept + pitcher_dollars_kept
    return {'dollars_kept': dollars_kept, 'remaining_batters': remaining_batters,
            'remaining_pitchers': remaining_pitchers}


def get_remaining_players(keeper_list, player_list):
    dollars_kept = 0
    if isinstance(player_list[0], dict):
        for keeper in keeper_list:
            dollars_kept += keeper['keeper_cost']
            for player in list(player_list):
                if keeper['full_name'] == player['name']:
                    player_list.remove(player)
                    break
    else:
        for keeper in keeper_list:
            dollars_kept += keeper['keeper_cost']
            for player in list(player_list):
                if keeper['full_name'] == player.name:
                    player_list.remove(player)
                    break
    return player_list, dollars_kept


def process_keepers(batter_dict_list, pitcher_dict_list, potential_keepers):
    proj_keeper_dict_list = []
    evaluated_keepers = evaluate_keepers(list(potential_keepers), list(batter_dict_list), list(pitcher_dict_list))
    for team in evaluated_keepers:
        team['remaining_roster'] = []
        for potential_keeper in team['roster']:
            if potential_keeper['worth_keeping']:
                potential_keeper['fantasy_team'] = team['team_name']
                potential_keeper['manager_guids'] = team['manager_guids']
                proj_keeper_dict_list.append(potential_keeper)
            else:
                team['remaining_roster'].append(potential_keeper)
        team['roster'] = list(team['remaining_roster'])
        team['remaining_roster'] = []
    orig_batter_pool = list(batter_dict_list)
    orig_pitcher_pool = list(pitcher_dict_list)
    processed_keepers = remove_projected_keepers(list(proj_keeper_dict_list), orig_batter_pool, orig_pitcher_pool)
    processed_keepers['batters_kept'] = len(batter_dict_list) - len(processed_keepers['remaining_batters'])
    processed_keepers['pitchers_kept'] = len(pitcher_dict_list) - len(processed_keepers['remaining_pitchers'])
    processed_keepers['keepers'] = proj_keeper_dict_list
    processed_keepers['remaining_potential_keepers'] = evaluated_keepers
    return processed_keepers


def project_keepers(batter_projections_, pitcher_projections_, potential_keepers, league):
    b_over_zero = league.batters_over_zero_dollars_avg or league.batters_over_zero_dollars or league.prev_year_league.batters_over_zero_dollars_avg
    p_over_zero = league.pitchers_over_zero_dollars_avg or league.pitchers_over_zero_dollars or league.prev_year_league.pitchers_over_zero_dollars_avg
    b_one_dollar = league.one_dollar_batters_avg or league.one_dollar_batters or league.prev_year_league.one_dollar_batters_avg
    p_one_dollar = league.one_dollar_pitchers_avg or league.one_dollar_pitchers or league.prev_year_league.one_dollar_pitchers_avg
    b_dollar_per_fvaaz = league.b_dollar_per_fvaaz_avg or league.b_dollar_per_fvaaz or league.prev_year_league.b_dollar_per_fvaaz_avg
    p_dollar_per_fvaaz = league.p_dollar_per_fvaaz_avg or league.p_dollar_per_fvaaz or league.prev_year_league.p_dollar_per_fvaaz_avg

    b_mult = league.b_player_pool_mult or league.prev_year_league.b_player_pool_mult
    p_mult = league.p_player_pool_mult or league.prev_year_league.p_player_pool_mult

    all_projected_keepers = []
    total_dollars_spent_on_keepers = 0
    total_batters_kept = 0
    total_pitchers_kept = 0

    # TODO: what is the best number of passes?
    passes = 3

    batter_pool = batter_projections_
    pitcher_pool = pitcher_projections_

    keepers = run_keeper_passes(batter_pool, pitcher_pool, potential_keepers, total_dollars_spent_on_keepers,
                                total_batters_kept, total_pitchers_kept, b_over_zero, p_over_zero, b_one_dollar,
                                p_one_dollar, b_dollar_per_fvaaz, p_dollar_per_fvaaz, b_mult, p_mult,
                                all_projected_keepers, passes)
    return keepers


def run_keeper_passes(batter_pool, pitcher_pool, potential_keepers, total_dollars_spent_on_keepers, total_batters_kept,
                      total_pitchers_kept, b_over_zero, p_over_zero, b_one_dollar, p_one_dollar, b_dollar_per_fvaaz,
                      p_dollar_per_fvaaz, b_mult, p_mult, all_projected_keepers, passes):
    processed_keepers = process_keepers(batter_pool, pitcher_pool, potential_keepers)
    total_dollars_spent_on_keepers += processed_keepers['dollars_kept']
    total_batters_kept += processed_keepers['batters_kept']
    total_pitchers_kept += processed_keepers['pitchers_kept']
    b_over_zero_remaining = b_over_zero - processed_keepers['batters_kept']
    p_over_zero_remaining = p_over_zero - processed_keepers['pitchers_kept']
    # print("Pass %s" % passes)
    # print("Batters Over $0 Start:")
    # print(b_over_zero)
    # print("Total Batters Kept:")
    # print(total_batters_kept)
    # print("Current Batters Kept:")
    # print(processed_keepers['batters_kept'])
    # print("Batters Over $0 Remaining:")
    # print(b_over_zero_remaining)
    # print("#################################")
    # print("Pitchers Over $0 Start:")
    # print(p_over_zero)
    # print("Total Pitchers Kept:")
    # print(total_pitchers_kept)
    # print("Current Pitchers Kept:")
    # print(processed_keepers['pitchers_kept'])
    # print("Pitchers Over $0 Remaining:")
    # print(p_over_zero_remaining)
    # print("-----------------------------------------------")
    batter_pool_ = calc_batter_z_score(processed_keepers['remaining_batters'], b_over_zero_remaining, b_one_dollar,
                                       b_dollar_per_fvaaz, b_mult, True)
    pitcher_pool_ = calc_pitcher_z_score(processed_keepers['remaining_pitchers'], p_over_zero_remaining, p_one_dollar,
                                         p_dollar_per_fvaaz, p_mult, True)
    all_projected_keepers.extend(processed_keepers['keepers'])
    potential_keepers_ = processed_keepers['remaining_potential_keepers']

    # TODO: none of this works well, may be a bad idea to begin with
    # old_batter_total_dollar_value = 0.0
    # old_pitcher_total_dollar_value = 0.0
    #
    # if isinstance(batter_pool[0], dict):
    #     for batter in batter_pool:
    #         old_batter_total_dollar_value += batter['dollarValue']
    #     for pitcher in pitcher_pool:
    #         old_pitcher_total_dollar_value += pitcher['dollarValue']
    # else:
    #     for batter in batter_pool:
    #         old_batter_total_dollar_value += batter.dollarValue
    #     for pitcher in pitcher_pool:
    #         old_pitcher_total_dollar_value += pitcher.dollarValue
    #
    # old_batter_avg_dollar_value = old_batter_total_dollar_value / len(batter_pool)
    # old_pitcher_avg_dollar_value = old_pitcher_total_dollar_value / len(pitcher_pool)
    #
    # new_batter_total_dollar_value = 0.0
    # new_pitcher_total_dollar_value = 0.0
    #
    # for batter in batter_pool_:
    #     new_batter_total_dollar_value += batter['dollarValue']
    # for pitcher in pitcher_pool_:
    #     new_pitcher_total_dollar_value += pitcher['dollarValue']
    #
    # new_batter_avg_dollar_value = new_batter_total_dollar_value / len(batter_pool_)
    # new_pitcher_avg_dollar_value = new_pitcher_total_dollar_value / len(pitcher_pool_)
    #
    # batter_dollar_value_mult = old_batter_avg_dollar_value / new_batter_avg_dollar_value
    # pitcher_dollar_value_mult = old_pitcher_avg_dollar_value / new_pitcher_avg_dollar_value
    #
    # for player in all_projected_keepers:
    #     if player['category'] == 'batter':
    #         player['value'] *= batter_dollar_value_mult
    #     elif player['category'] == 'pitcher':
    #         player['value'] *= pitcher_dollar_value_mult

    while passes > 0:
        passes -= 1
        if passes == 0:
            result = {'keepers': keeper_dict_by_team(all_projected_keepers), 'batter_pool': batter_pool_,
                      'pitcher_pool': pitcher_pool_, 'dollars_spent_on_keepers': total_dollars_spent_on_keepers}
            return result
        else:
            return run_keeper_passes(batter_pool_, pitcher_pool_, potential_keepers_, total_dollars_spent_on_keepers,
                                     total_batters_kept, total_pitchers_kept, b_over_zero_remaining, p_over_zero_remaining,
                                     b_one_dollar, p_one_dollar, b_dollar_per_fvaaz, p_dollar_per_fvaaz, b_mult, p_mult,
                                     all_projected_keepers, passes)


def get_auction_values(league, batter_pool, pitcher_pool, potential_keepers, actual_keepers):
    b_over_zero = league.batters_over_zero_dollars_avg or league.batters_over_zero_dollars or league.prev_year_league.batters_over_zero_dollars_avg
    p_over_zero = league.pitchers_over_zero_dollars_avg or league.pitchers_over_zero_dollars or league.prev_year_league.pitchers_over_zero_dollars_avg
    b_one_dollar = league.one_dollar_batters_avg or league.one_dollar_batters or league.prev_year_league.one_dollar_batters_avg
    p_one_dollar = league.one_dollar_pitchers_avg or league.one_dollar_pitchers or league.prev_year_league.one_dollar_pitchers_avg
    b_dollar_per_fvaaz = league.b_dollar_per_fvaaz_avg or league.b_dollar_per_fvaaz or league.prev_year_league.b_dollar_per_fvaaz_avg
    p_dollar_per_fvaaz = league.p_dollar_per_fvaaz_avg or league.p_dollar_per_fvaaz or league.prev_year_league.p_dollar_per_fvaaz_avg

    b_mult = league.b_player_pool_mult or league.prev_year_league.b_player_pool_mult
    p_mult = league.p_player_pool_mult or league.prev_year_league.p_player_pool_mult

    total_batters_kept = 0
    total_pitchers_kept = 0
    total_dollars_spent_on_keepers = 0
    keeper_dict_list = []

    if league.draft_status == "predraft":
        for team in actual_keepers:
            for keeper in team['roster']:
                keeper['fantasy_team'] = team['team_name']
                keeper['manager_guids'] = team['manager_guids']
                keeper['worth_keeping'] = True
                if keeper['category'] == 'batter':
                    try:
                        original_batter = batter_pool.get(last_name=keeper['last_name'], team=keeper['team'],
                                                          normalized_first_name=keeper['first_name'])
                        keeper['value'] = original_batter.dollarValue
                    except BatterProjection.DoesNotExist:
                        keeper['value'] = 0
                    total_batters_kept += 1
                if keeper['category'] == 'pitcher':
                    try:
                        original_pitcher = pitcher_pool.get(last_name=keeper['last_name'], team=keeper['team'],
                                                            normalized_first_name=keeper['first_name'])
                        keeper['value'] = original_pitcher.dollarValue
                    except PitcherProjection.DoesNotExist:
                        keeper['value'] = 0
                    total_pitchers_kept += 1
                for tm in potential_keepers:
                    for ptkpr in tm['roster']:
                        if (keeper['last_name'] == ptkpr['last_name'] and keeper['team'] == ptkpr['team']
                                and keeper['first_name'] == ptkpr['first_name']):
                            keeper['keeper_cost'] = ptkpr['keeper_cost']
                            total_dollars_spent_on_keepers += ptkpr['keeper_cost']
                # TODO: this is a super shitty workaround, need to find out why some players (ie. carlos corrasco) arent showing up properly
                if 'keeper_cost' not in keeper:
                    keeper['keeper_cost'] = 10
                keeper_dict_list.append(keeper)

    elif league.draft_status == "postdraft":
        for team in actual_keepers:
            for keeper in team['roster']:
                for tm in potential_keepers:
                    for ptkpr in tm['roster']:
                        if (keeper['last_name'] == ptkpr['last_name'] and keeper['team'] == ptkpr['team']
                                and keeper['first_name'] == ptkpr['first_name']):
                            keeper['keeper_cost'] = ptkpr['keeper_cost']
                keeper['fantasy_team'] = team['team_name']
                keeper['manager_guids'] = team['manager_guids']
                keeper['worth_keeping'] = False
                if keeper['category'] == 'batter':
                    try:
                        original_batter = batter_pool.get(last_name=keeper['last_name'], team=keeper['team'],
                                                          normalized_first_name=keeper['first_name'])
                        keeper['value'] = original_batter.dollarValue
                    except BatterProjection.DoesNotExist:
                        keeper['value'] = 0
                    if keeper['value'] > keeper['keeper_cost']:
                        keeper['worth_keeping'] = True
                        total_batters_kept += 1
                        total_dollars_spent_on_keepers += keeper['keeper_cost']
                if keeper['category'] == 'pitcher':
                    try:
                        original_pitcher = pitcher_pool.get(last_name=keeper['last_name'], team=keeper['team'],
                                                            normalized_first_name=keeper['first_name'])
                        keeper['value'] = original_pitcher.dollarValue
                    except PitcherProjection.DoesNotExist:
                        keeper['value'] = 0
                    if keeper['value'] > keeper['keeper_cost']:
                        keeper['worth_keeping'] = True
                        total_pitchers_kept += 1
                        total_dollars_spent_on_keepers += keeper['keeper_cost']
                # TODO: this is a super shitty workaround, need to find out why some players (ie. carlos corrasco) arent showing up properly
                if 'keeper_cost' not in keeper:
                    keeper['keeper_cost'] = 10
                keeper_dict_list.append(keeper)

    processed_keepers = remove_projected_keepers(list(keeper_dict_list), list(batter_pool), list(pitcher_pool))
    b_over_zero_remaining = b_over_zero - total_batters_kept
    p_over_zero_remaining = p_over_zero - total_pitchers_kept

    batter_pool_ = calc_batter_z_score(processed_keepers['remaining_batters'], b_over_zero_remaining, b_one_dollar,
                                       b_dollar_per_fvaaz, b_mult, True)
    pitcher_pool_ = calc_pitcher_z_score(processed_keepers['remaining_pitchers'], p_over_zero_remaining, p_one_dollar,
                                         p_dollar_per_fvaaz, p_mult, True)

    result = {'keepers': keeper_dict_by_team(keeper_dict_list), 'batter_pool': batter_pool_,
              'pitcher_pool': pitcher_pool_, 'dollars_spent_on_keepers': total_dollars_spent_on_keepers}
    return result


def dump_to_json():
    import json
    keepers = project_keepers()
    with open('keepers.txt', 'w') as outfile:
        json.dump(keepers['keepers'], outfile, indent=4, sort_keys=True)
    with open('batters.txt', 'w') as outfile:
        json.dump(keepers['batter_pool'], outfile, indent=4, sort_keys=True)
    with open('pitchers.txt', 'w') as outfile:
        json.dump(keepers['pitcher_pool'], outfile, indent=4, sort_keys=True)
    print("FILE OUTPUT COMPLETE")
