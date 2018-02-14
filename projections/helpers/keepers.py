import csv
import heapq
import pprint

from .player_creator import calc_batter_z_score, calc_pitcher_z_score
from .data_analysis import evaluate_keepers


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
            keeper_team_dict[team_name]['total_cost'] = 0
            keeper_team_dict[team_name]['players'] = []
        keeper_team_dict[team_name]['total_cost'] += player['keeper_cost'] if player['worth_keeping'] else 0
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
                proj_keeper_dict_list.append(potential_keeper)
            else:
                team['remaining_roster'].append(potential_keeper)
        team['roster'] = list(team['remaining_roster'])
        team['remaining_roster'] = []
    orig_batter_pool = list(batter_dict_list)
    orig_pitcher_pool = list(pitcher_dict_list)
    processed_keepers = remove_projected_keepers(list(proj_keeper_dict_list), orig_batter_pool, orig_pitcher_pool)
    # orig_batter_pool = 0
    # orig_pitcher_pool = 0
    # for player in batter_dict_list:
    #     orig_batter_pool += 1
    # for player in pitcher_dict_list:
    #     orig_pitcher_pool += 1
    processed_keepers['batters_kept'] = len(batter_dict_list) - len(processed_keepers['remaining_batters'])
    processed_keepers['pitchers_kept'] = len(pitcher_dict_list) - len(processed_keepers['remaining_pitchers'])
    # processed_keepers['batters_kept'] = 0
    # processed_keepers['pitchers_kept'] = 0
    processed_keepers['projected_keepers'] = proj_keeper_dict_list
    processed_keepers['remaining_potential_keepers'] = evaluated_keepers
    return processed_keepers


def project_keepers(batter_projections_, pitcher_projections_, potential_keepers, league):
    b_over_zero = league.batters_over_zero_dollars_avg
    if not b_over_zero:
        b_over_zero = league.batters_over_zero_dollars

    p_over_zero = league.pitchers_over_zero_dollars_avg
    if not p_over_zero:
        p_over_zero = league.pitchers_over_zero_dollars

    b_one_dollar = league.one_dollar_batters_avg
    if not b_one_dollar:
        b_one_dollar = league.one_dollar_batters

    p_one_dollar = league.one_dollar_pitchers_avg
    if not p_one_dollar:
        p_one_dollar = league.one_dollar_pitchers

    b_dollar_per_fvaaz = league.b_dollar_per_fvaaz_avg
    if not b_dollar_per_fvaaz:
        b_dollar_per_fvaaz = league.b_dollar_per_fvaaz

    p_dollar_per_fvaaz = league.p_dollar_per_fvaaz_avg
    if not p_dollar_per_fvaaz:
        p_dollar_per_fvaaz = league.p_dollar_per_fvaaz

    b_mult = league.b_player_pool_mult
    p_mult = league.p_player_pool_mult

    all_projected_keepers = []
    total_dollars_spent_on_keepers = 0
    total_batters_kept = 0
    total_pitchers_kept = 0

    passes = 2

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
    print("Pass %s" % passes)
    print("Batters Over $0 Start:")
    print(b_over_zero)
    print("Total Batters Kept:")
    print(total_batters_kept)
    print("Current Batters Kept:")
    print(processed_keepers['batters_kept'])
    print("Batters Over $0 Remaining:")
    print(b_over_zero_remaining)
    print("#################################")
    print("Pitchers Over $0 Start:")
    print(p_over_zero)
    print("Total Pitchers Kept:")
    print(total_pitchers_kept)
    print("Current Pitchers Kept:")
    print(processed_keepers['pitchers_kept'])
    print("Pitchers Over $0 Remaining:")
    print(p_over_zero_remaining)
    print("-----------------------------------------------")
    batter_pool_ = calc_batter_z_score(processed_keepers['remaining_batters'], b_over_zero_remaining, b_one_dollar,
                                       b_dollar_per_fvaaz, b_mult)
    pitcher_pool_ = calc_pitcher_z_score(processed_keepers['remaining_pitchers'], p_over_zero_remaining, p_one_dollar,
                                         p_dollar_per_fvaaz, p_mult)
    all_projected_keepers.extend(processed_keepers['projected_keepers'])
    potential_keepers_ = processed_keepers['remaining_potential_keepers']

    while passes > 0:
        passes -= 1
        if passes == 0:
            result = {'projected_keepers': keeper_dict_by_team(all_projected_keepers), 'batter_pool': batter_pool_,
                      'pitcher_pool': pitcher_pool_, 'dollars_spent_on_keepers': total_dollars_spent_on_keepers}
            return result
        else:
            return run_keeper_passes(batter_pool_, pitcher_pool_, potential_keepers_, total_dollars_spent_on_keepers,
                                     total_batters_kept, total_pitchers_kept, b_over_zero_remaining, p_over_zero_remaining,
                                     b_one_dollar, p_one_dollar, b_dollar_per_fvaaz, p_dollar_per_fvaaz, b_mult, p_mult,
                                     all_projected_keepers, passes)


def dump_to_json():
    import json
    projected_keepers = project_keepers()
    with open('keepers.txt', 'w') as outfile:
        json.dump(projected_keepers['projected_keepers'], outfile, indent=4, sort_keys=True)
    with open('batters.txt', 'w') as outfile:
        json.dump(projected_keepers['batter_pool'], outfile, indent=4, sort_keys=True)
    with open('pitchers.txt', 'w') as outfile:
        json.dump(projected_keepers['pitcher_pool'], outfile, indent=4, sort_keys=True)
    print("FILE OUTPUT COMPLETE")
