"""Create players"""
import heapq
import operator
import pprint
import logging
import re

from django.forms.models import model_to_dict

from .advanced_stat_calc import avg_calc, std_dev_calc, z_score_calc, z_score_calc_era_whip
from .csv_parser import parse_batters_from_csv, parse_pitchers_from_csv
from .html_parser import fantasy_pro_players, scrape_closer_monkey, scrape_razzball_batters, scrape_razzball_pitchers
from .normalizer import name_normalizer


def create_full_batter_html(url):
    """Create batters using html"""
    # raw_batter_list = scrape_razzball_batters(url)
    raw_batter_list = fantasy_pro_players(url)
    return create_full_batter(raw_batter_list)


def create_full_batter_csv(user, league, csv):
    """Create batters using csv"""
    raw_batter_list = parse_batters_from_csv(user, league, csv)
    return create_full_batter(raw_batter_list)


def create_full_batter(raw_batter_list):
    """Create batters"""
    batter_model_list = []
    for raw_batter in raw_batter_list:
        raw_batter['category'] = 'batter'
        batter_model_list.append(raw_batter)
    return batter_model_list


def calc_batter_z_score(batter_list, players_over_zero_dollars, one_dollar_players,
                        dollar_per_fvaaz, player_pool_multiplier, add_original_value=False):
    """Calculate zScores for batters"""
    player_pool = int(players_over_zero_dollars * player_pool_multiplier)
    # Standard Calculations
    run_list = []
    hr_list = []
    rbi_list = []
    sb_list = []
    ops_list = []
    avg_list = []
    # weighted_batter_list = []
    batter_dict_list = []
    if not isinstance(batter_list[0], dict):
        for batter in batter_list:
            b = model_to_dict(batter)
            batter_dict_list.append(b)
    else:
        batter_dict_list = batter_list
    for batter in batter_dict_list:
        if add_original_value:
            batter['original_value'] = batter['dollarValue']

        run_list.append(batter['r'])
        hr_list.append(batter['hr'])
        rbi_list.append(batter['rbi'])
        sb_list.append(batter['sb'])
        ops_list.append(batter['ops'])
        avg_list.append(batter['avg'])
    run_list_nlargest = heapq.nlargest(player_pool, run_list)
    hr_list_nlargest = heapq.nlargest(player_pool, hr_list)
    rbi_list_nlargest = heapq.nlargest(player_pool, rbi_list)
    sb_list_nlargest = heapq.nlargest(player_pool, sb_list)
    ops_list_nlargest = heapq.nlargest(player_pool, ops_list)
    avg_list_nlargest = heapq.nlargest(player_pool, avg_list)
    # Average Calculation
    r_avg = avg_calc(run_list_nlargest)
    hr_avg = avg_calc(hr_list_nlargest)
    rbi_avg = avg_calc(rbi_list_nlargest)
    sb_avg = avg_calc(sb_list_nlargest)
    ops_avg = avg_calc(ops_list_nlargest)
    avg_avg = avg_calc(avg_list_nlargest)
    # Standard Deviation Calculation
    r_std_dev = std_dev_calc(run_list_nlargest, r_avg)
    hr_std_dev = std_dev_calc(hr_list_nlargest, hr_avg)
    rbi_std_dev = std_dev_calc(rbi_list_nlargest, rbi_avg)
    sb_std_dev = std_dev_calc(sb_list_nlargest, sb_avg)
    ops_std_dev = std_dev_calc(ops_list_nlargest, ops_avg)
    avg_std_dev = std_dev_calc(avg_list_nlargest, avg_avg)
    # zScore Calculation
    for batter in batter_dict_list:
        batter['zScoreR'] = z_score_calc(batter['r'], r_avg, r_std_dev)
        batter['weightedR'] = batter['zScoreR'] * float(batter['ab'])
        batter['zScoreHr'] = z_score_calc(batter['hr'], hr_avg, hr_std_dev)
        batter['weightedHr'] = batter['zScoreHr'] * float(batter['ab'])
        batter['zScoreRbi'] = z_score_calc(batter['rbi'], rbi_avg, rbi_std_dev)
        batter['weightedRbi'] = batter['zScoreRbi'] * float(batter['ab'])
        batter['zScoreSb'] = z_score_calc(batter['sb'], sb_avg, sb_std_dev)
        batter['weightedSb'] = batter['zScoreSb'] * float(batter['ab'])
        batter['zScoreOps'] = z_score_calc(batter['ops'], ops_avg, ops_std_dev)
        batter['weightedOps'] = batter['zScoreOps'] * float(batter['ab'])
        batter['zScoreAvg'] = z_score_calc(batter['avg'], ops_avg, ops_std_dev)
        batter['weightedAvg'] = batter['zScoreAvg'] * float(batter['ab'])
        # weighted_batter_list.append(batter)
    # Weighted Calculations
    weighted_run_list = []
    weighted_hr_list = []
    weighted_rbi_list = []
    weighted_sb_list = []
    weighted_ops_list = []
    weighted_avg_list = []
    # for batter in weighted_batter_list:
    for batter in batter_dict_list:
        weighted_run_list.append(batter['weightedR'])
        weighted_hr_list.append(batter['weightedHr'])
        weighted_rbi_list.append(batter['weightedRbi'])
        weighted_sb_list.append(batter['weightedSb'])
        weighted_ops_list.append(batter['weightedOps'])
        weighted_avg_list.append(batter['weightedOps'])
    weighted_run_list_nlargest = heapq.nlargest(player_pool, weighted_run_list)
    weighted_hr_list_nlargest = heapq.nlargest(player_pool, weighted_hr_list)
    weighted_rbi_list_nlargest = heapq.nlargest(player_pool, weighted_rbi_list)
    weighted_sb_list_nlargest = heapq.nlargest(player_pool, weighted_sb_list)
    weighted_ops_list_nlargest = heapq.nlargest(player_pool, weighted_ops_list)
    weighted_avg_list_nlargest = heapq.nlargest(player_pool, weighted_avg_list)
    # Weighted Average Calculation
    weighted_r_avg = avg_calc(weighted_run_list_nlargest)
    weighted_hr_avg = avg_calc(weighted_hr_list_nlargest)
    weighted_rbi_avg = avg_calc(weighted_rbi_list_nlargest)
    weighted_sb_avg = avg_calc(weighted_sb_list_nlargest)
    weighted_ops_avg = avg_calc(weighted_ops_list_nlargest)
    weighted_avg_avg = avg_calc(weighted_avg_list_nlargest)
    # Weighted Standard Deviation Calculation
    weighted_r_std_dev = std_dev_calc(weighted_run_list_nlargest, weighted_r_avg)
    weighted_hr_std_dev = std_dev_calc(weighted_hr_list_nlargest, weighted_hr_avg)
    weighted_rbi_std_dev = std_dev_calc(weighted_rbi_list_nlargest, weighted_rbi_avg)
    weighted_sb_std_dev = std_dev_calc(weighted_sb_list_nlargest, weighted_sb_avg)
    weighted_ops_std_dev = std_dev_calc(weighted_ops_list_nlargest, weighted_ops_avg)
    weighted_avg_std_dev = std_dev_calc(weighted_avg_list_nlargest, weighted_avg_avg)
    # Weighted zScore Calculation
    for batter in batter_dict_list:
        batter['weightedZscoreR'] = z_score_calc(batter['weightedR'], weighted_r_avg,
                                                 weighted_r_std_dev)
        batter['weightedZscoreHr'] = z_score_calc(batter['weightedHr'], weighted_hr_avg,
                                                  weighted_hr_std_dev)
        batter['weightedZscoreRbi'] = z_score_calc(batter['weightedRbi'], weighted_rbi_avg,
                                                   weighted_rbi_std_dev)
        batter['weightedZscoreSb'] = z_score_calc(batter['weightedSb'], weighted_sb_avg,
                                                  weighted_sb_std_dev)
        batter['weightedZscoreOps'] = z_score_calc(batter['weightedOps'], weighted_ops_avg,
                                                   weighted_ops_std_dev)
        batter['weightedZscoreAvg'] = z_score_calc(batter['weightedAvg'], weighted_avg_avg,
                                                   weighted_avg_std_dev)
    # Calculate Values
    fvaaz_list = []
    for batter in batter_dict_list:
        # TODO: how to handle an avg version of this?
        batter['fvaaz'] = (batter['zScoreR'] + batter['zScoreHr'] + batter['zScoreRbi'] + batter['zScoreSb'] +
                           batter['weightedZscoreOps'])
        fvaaz_list.append(batter['fvaaz'])
    players_over_one_dollar = players_over_zero_dollars - one_dollar_players
    fvaaz_list_over_zero = heapq.nlargest(players_over_zero_dollars, fvaaz_list)
    fvaaz_list_over_one = heapq.nlargest(players_over_one_dollar, fvaaz_list)
    for batter in batter_dict_list:
        if batter['fvaaz'] >= fvaaz_list_over_one[players_over_one_dollar - 1]:
            # TODO: dollar_per_fvaaz seems to be a circular reference, how to resolve this?
            batter['dollarValue'] = batter['fvaaz'] * dollar_per_fvaaz
        elif batter['fvaaz'] >= fvaaz_list_over_zero[players_over_zero_dollars - 1]:
            batter['dollarValue'] = 1.0
        else:
            batter['dollarValue'] = 0.0
    return sorted(batter_dict_list, key=operator.itemgetter('fvaaz'), reverse=True)
    # sorts by fvaaz (largest to smallest)


def create_full_pitcher_html(url):
    """Create pitchers using html"""
    # raw_pitcher_list = scrape_razzball_pitchers(url)
    raw_pitcher_list = fantasy_pro_players(url)
    return create_full_pitcher(raw_pitcher_list)


def create_full_pitcher_csv(user, league, csv):
    """Create pitchers using csv"""
    raw_pitcher_list = parse_pitchers_from_csv(user, league, csv)
    return create_full_pitcher(raw_pitcher_list)


def create_full_pitcher(raw_pitcher_list):
    """Create pitchers"""
    pitcher_model_list = []
    # max_ip = 0.0
    # for raw_pitcher in raw_pitcher_list:
    #     if raw_pitcher.get("IP") > max_ip:
    #         max_ip = raw_pitcher.get("IP")
    closers = scrape_closer_monkey()
    for raw_pitcher in raw_pitcher_list:
        raw_pitcher['category'] = "pitcher"
        for closer in closers:
            if (raw_pitcher['last_name'].lower() == closer['last_name'].lower()
                    and raw_pitcher['team'].upper() == closer['team'].upper()):
                raw_pitcher['pos'].append(closer['pos'])
                continue
        pitcher_model_list.append(raw_pitcher)
    return pitcher_model_list


def calc_pitcher_z_score(pitcher_list, players_over_zero_dollars, one_dollar_players,
                         dollar_per_fvaaz, player_pool_multiplier, add_original_value=False):
    """Calculate zScores for pitchers"""
    player_pool = int(players_over_zero_dollars * player_pool_multiplier)
    # max_ip = max(pitcher['ips ']for pitcher in pitcher_list)
    # Standard Calculations
    win_list = []
    sv_list = []
    k_list = []
    era_list = []
    whip_list = []
    # weighted_pitcher_list = []
    pitcher_dict_list = []
    if not isinstance(pitcher_list[0], dict):
        for pitcher in pitcher_list:
            p = model_to_dict(pitcher)
            pitcher_dict_list.append(p)
    else:
        pitcher_dict_list = pitcher_list
    for pitcher in pitcher_dict_list:
        if add_original_value:
            pitcher['original_value'] = pitcher['dollarValue']
        # if pitcher['w'] < 0 or pitcher['sv'] < 0 or pitcher['k'] < 0 or pitcher['era'] <= 0 or pitcher['whip'] <= 0:
        #     continue
        win_list.append(pitcher['w'])
        sv_list.append(pitcher['sv'])
        k_list.append(pitcher['k'])
        # TODO: is dividing by 15 the best route here?
        era_list.append(pitcher['era'])
        whip_list.append(pitcher['whip'])
        # era_list.append(pitcher['era'] * (pitcher['ip'] / 15))
        # whip_list.append(pitcher['whip'] * (pitcher['ip'] / 15))
    win_list_nlargest = heapq.nlargest(player_pool, win_list)
    sv_list_nlargest = heapq.nlargest(player_pool, sv_list)
    k_list_nlargest = heapq.nlargest(player_pool, k_list)
    era_list_nsmallest = heapq.nsmallest(player_pool, era_list)
    whip_list_nsmallest = heapq.nsmallest(player_pool, whip_list)
    # Average Calculation
    w_avg = avg_calc(win_list_nlargest)
    sv_avg = avg_calc(sv_list_nlargest)
    k_avg = avg_calc(k_list_nlargest)
    era_avg = avg_calc(era_list_nsmallest)
    whip_avg = avg_calc(whip_list_nsmallest)
    # Standard Deviation Calculation
    w_std_dev = std_dev_calc(win_list_nlargest, w_avg)
    sv_std_dev = std_dev_calc(sv_list_nlargest, sv_avg)
    k_std_dev = std_dev_calc(k_list_nlargest, k_avg)
    era_std_dev = std_dev_calc(era_list_nsmallest, era_avg)
    whip_std_dev = std_dev_calc(whip_list_nsmallest, whip_avg)
    # zScore Calculation
    for pitcher in pitcher_dict_list:
        pitcher['zScoreW'] = z_score_calc(pitcher['w'], w_avg, w_std_dev)
        pitcher['weightedW'] = pitcher['zScoreW'] * float(pitcher['ip'])
        pitcher['zScoreSv'] = z_score_calc(pitcher['sv'], sv_avg, sv_std_dev)
        pitcher['weightedSv'] = pitcher['zScoreSv'] * float(pitcher['ip'])
        pitcher['zScoreK'] = z_score_calc(pitcher['k'], k_avg, k_std_dev)
        pitcher['weightedK'] = pitcher['zScoreK'] * float(pitcher['ip'])
        pitcher['zScoreEra'] = z_score_calc_era_whip(pitcher['era'], era_avg, era_std_dev)
        pitcher['weightedEra'] = pitcher['zScoreEra'] * float(pitcher['ip'])
        pitcher['zScoreWhip'] = z_score_calc_era_whip(pitcher['whip'], whip_avg,
                                                      whip_std_dev)
        pitcher['weightedWhip']= pitcher['zScoreWhip'] * float(pitcher['ip'])
        # weighted_pitcher_list.append(pitcher)
    # Weighted Calculations
    weighted_win_list = []
    weighted_sv_list = []
    weighted_k_list = []
    weighted_era_list = []
    weighted_whip_list = []
    # for pitcher in weighted_pitcher_list:
    for pitcher in pitcher_dict_list:
        weighted_win_list.append(pitcher['weightedW'])
        weighted_sv_list.append(pitcher['weightedSv'])
        weighted_k_list.append(pitcher['weightedK'])
        weighted_era_list.append(pitcher['weightedEra'])
        weighted_whip_list.append(pitcher['weightedWhip'])
    weighted_win_list_nlargest = heapq.nlargest(player_pool, weighted_win_list)
    weighted_sv_list_nlargest = heapq.nlargest(player_pool, weighted_sv_list)
    weighted_k_list_nlargest = heapq.nlargest(player_pool, weighted_k_list)
    weighted_era_list_nlargest = heapq.nlargest(player_pool, weighted_era_list)
    weighted_whip_list_nlargest = heapq.nlargest(player_pool, weighted_whip_list)
    # Weighted Average Calculation
    weighted_w_avg = avg_calc(weighted_win_list_nlargest)
    weighted_sv_avg = avg_calc(weighted_sv_list_nlargest)
    weighted_k_avg = avg_calc(weighted_k_list_nlargest)
    weighted_era_avg = avg_calc(weighted_era_list_nlargest)
    weighted_whip_avg = avg_calc(weighted_whip_list_nlargest)
    # Weighted Standard Deviation Calculation
    weighted_w_std_dev = std_dev_calc(weighted_win_list_nlargest, weighted_w_avg)
    weighted_sv_std_dev = std_dev_calc(weighted_sv_list_nlargest, weighted_sv_avg)
    weighted_k_std_dev = std_dev_calc(weighted_k_list_nlargest, weighted_k_avg)
    weighted_era_std_dev = std_dev_calc(weighted_era_list_nlargest, weighted_era_avg)
    weighted_whip_std_dev = std_dev_calc(weighted_whip_list_nlargest,
                                         weighted_whip_avg)
    # Weighted zScore Calculation
    for pitcher in pitcher_dict_list:
        pitcher['weightedZscoreW'] = z_score_calc(pitcher['weightedW'], weighted_w_avg,
                                                  weighted_w_std_dev)
        pitcher['weightedZscoreSv'] = z_score_calc(pitcher['weightedSv'], weighted_sv_avg,
                                                   weighted_sv_std_dev)
        pitcher['weightedZscoreK'] = z_score_calc(pitcher['weightedK'], weighted_k_avg,
                                                  weighted_k_std_dev)
        pitcher['weightedZscoreEra'] = z_score_calc(pitcher['weightedEra'], weighted_era_avg,
                                                    weighted_era_std_dev)
        pitcher['weightedZscoreWhip'] = z_score_calc(pitcher['weightedWhip'],
                                                     weighted_whip_avg,
                                                     weighted_whip_std_dev)
    # Calculate Values
    fvaaz_list = []
    for pitcher in pitcher_dict_list:
        # TODO: is 0.06 the best cutoff?
        if "SP" not in pitcher['pos'] or ("RP" in pitcher['pos'] and pitcher['winsip'] < 0.06):
            pitcher['fvaaz'] = (pitcher['zScoreSv'] + pitcher['zScoreK'] +
                                pitcher['weightedZscoreEra'] + pitcher['weightedZscoreWhip'])
        else:
            pitcher['fvaaz'] = (pitcher['zScoreW'] + pitcher['zScoreSv'] +
                                pitcher['zScoreK'] + pitcher['weightedZscoreEra'] +
                                pitcher['weightedZscoreWhip'])
        #     pitcher['fvaaz'] = (pitcher['weightedZscoreSv'] + pitcher['weightedZscoreK'] +
        #                      pitcher['weightedZscoreEra'] + pitcher['weightedZscoreWhip'])
        # else:
        #     pitcher['fvaaz'] = (pitcher['weightedZscoreW'] + pitcher['weightedZscoreSv'] +
        #                      pitcher['weightedZscoreK'] + pitcher['weightedZscoreEra'] +
        #                      pitcher['weightedZscoreWhip'])
        fvaaz_list.append(pitcher['fvaaz'])
    players_over_one_dollar = players_over_zero_dollars - one_dollar_players
    fvaaz_list_over_zero = heapq.nlargest(players_over_zero_dollars, fvaaz_list)
    fvaaz_list_over_one = heapq.nlargest(players_over_one_dollar, fvaaz_list)
    for pitcher in pitcher_dict_list:
        if pitcher['fvaaz'] >= fvaaz_list_over_one[players_over_one_dollar - 1]:
            pitcher['dollarValue'] = pitcher['fvaaz'] * dollar_per_fvaaz
        elif pitcher['fvaaz'] >= fvaaz_list_over_zero[players_over_zero_dollars - 1]:
            pitcher['dollarValue'] = 1.0
        else:
            pitcher['dollarValue'] = 0.0
    return sorted(pitcher_dict_list, key=operator.itemgetter('fvaaz'), reverse=True)
    # sorts by fvaaz (largest to smallest)


def is_useless_pitcher(pitcher):
    return pitcher['w'] < 0 or pitcher['sv'] < 0 or pitcher['k'] < 0 or pitcher['era'] <= 0 or pitcher['whip'] <= 0

