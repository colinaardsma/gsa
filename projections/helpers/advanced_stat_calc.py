"""zScore Calculation"""
import math
import collections
import pprint


def avg_calc(stat_list):
    """Calculate the average of a list"""
    stat_total = 0
    stat_count = 0
    for stat in stat_list:
        stat_total += float(stat)
        stat_count += 1
    avg = stat_total / stat_count
    return avg


def std_dev_calc(stat_list, stat_avg):
    """Calculate the standard deviation of a list"""
    z_list = []
    for stat in stat_list:
        z_stat = math.pow(float(stat) - stat_avg, 2)
        z_list.append(z_stat)
    std_dev = math.sqrt(avg_calc(z_list))
    return std_dev


def z_score_calc(stat, stat_avg, std_dev):
    """Calculate the zScore for a list."""
    z_score = (float(stat) - stat_avg) / std_dev
    return z_score


def z_score_calc_era_whip(stat, stat_avg, std_dev):
    """Calculate the zScore for a list."""
    z_score = (stat_avg - float(stat)) / std_dev
    return z_score


def calc_sgp(stats):
    """Calculate the SGP of a list of stats"""
    stat_diff = []
    stat_diff_sum = 0
    ordered_dict = collections.OrderedDict(sorted(stats.items()))
    # dict_keys = [k for k in ordered_dict.keys()]
    dict_keys = [*ordered_dict]
    for key in ordered_dict:
        dict_keys.remove(key)
        if not dict_keys:
            continue
        next_key = min(dict_keys)

        diff = ordered_dict[next_key] - ordered_dict[key]
        stat_diff.append(diff)
    stat_diff.remove(max(stat_diff))
    stat_diff.remove(min(stat_diff))

    for diff in stat_diff:
        stat_diff_sum += diff

    avg_diff = stat_diff_sum / len(stat_diff)

    return avg_diff


def get_sgp(standings):
    sgp = {}
    stats = {}
    for team in standings:
        for key in team['Stats']:
            if key == 'IP' or key == 'TotalGP':
                continue
            stat = team['Stats'][key]
            point_value = stat['Point_Value']
            stat_value = stat['Stat_Value']
            if key not in stats:
                stats[key] = {}
            checked_point_value = check_key(stats[key], point_value)
            stats[key][checked_point_value] = stat_value
    for stat in stats:
        sgp[stat] = calc_sgp(stats[stat])
    return sgp


def check_key(stat_dict, value):
    if value in stat_dict:
        value += 0.01
        check_key(stat_dict, value)
    return value
