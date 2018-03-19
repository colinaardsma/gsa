"""Rate players"""
import operator
import math
import re
import ast
import copy
import collections
import itertools
import pprint

from .normalizer import team_normalizer, name_normalizer, player_comparer
from ..models import BatterProjection, BatterValue, PitcherProjection, PitcherValue


def rate_avail_players(fa_list, ros_projection_list):
    """Compare available FAs with Projections\n
    Args:\n
        fa_list: list of available FA on Yahoo!.\n
        ros_projection_list: Rest of Season projection list.\n
    Returns:\n
        list of players using FA projections.\n
    Raises:\n
        None.
    """
    fa_player_list = []
    for player_proj, fa_player in itertools.product(ros_projection_list, fa_list):
        if player_comparer(fa_player, player_proj):
            player_proj.isFA = True
            fa_player_list.append(player_proj)
    fa_above_repl = []
    dollar_value = 100.00
    player_number = 0
    while dollar_value > 1.0:
        fa_above_repl.append(fa_player_list[player_number])
        dollar_value = fa_player_list[player_number].dollarValue
        player_number += 1
    return fa_above_repl


def rate_team(team_dict, ros_projection_list):
    """Compare team with Projections\n
    Args:\n
        team_dict: dict of players on team.\n
        ros_projection_list: Rest of Season projection list.\n
    Returns:\n
        list of players using team projections.\n
    Raises:\n
        None.
    """
    team_player_list = []
    for player_proj, roster_player in itertools.product(ros_projection_list, team_dict['ROSTER']):
        if player_comparer(roster_player, player_proj):
            team_player_list.append(player_proj)
    return team_player_list


def team_optimizer(team_dict, ros_proj_b_list, ros_proj_p_list, league_pos_dict, current_stangings, league):
    """Optimizes full season lineups for team\n
    Args:\n
        team_dict: dict of players on team.\n
        ros_proj_b_list: Rest of Season batter projection list.\n
        ros_proj_p_list: Rest of Season pitcher projection list.\n
        league_pos_dict: dict of team positions.\n
        current_stangings: current league standings.\n
        league_settings: league settings.\n
    Returns:\n
        Optimized team lineup as a dict.\n
    Raises:\n
        None.
    """
    opt_batters = batting_roster_optimizer(team_dict, ros_proj_b_list, league_pos_dict)
    opt_pitchers = pitching_roster_optimizer(team_dict, ros_proj_p_list, league_pos_dict, current_stangings, league)
    opt_bench = bench_roster_optimizer(team_dict, ros_proj_b_list, ros_proj_p_list, league_pos_dict, current_stangings,
                                       league, opt_batters, opt_pitchers)
    team_stats = {}
    for standing in current_stangings:
        if [mg for mg in standing['manager_guids'] if mg in team_dict['manager_guids']]:
            batters = [val for sublist in opt_batters.values() for val in sublist]
            batters.extend(opt_bench['batters'])
            team_stats['StatsR'] = int(standing['StatsR'])
            team_stats['StatsHR'] = int(standing['StatsHR'])
            team_stats['StatsRBI'] = int(standing['StatsRBI'])
            team_stats['StatsSB'] = int(standing['StatsSB'])
            team_stats['StatsOPS'] = float(standing['StatsOPS'])
            team_stats['StatsTotalGP'] = int(standing['StatsTotalGP'])
            for batter in batters:
                team_stats['StatsR'] += int(batter.r)
                team_stats['StatsHR'] += int(batter.hr)
                team_stats['StatsRBI'] += int(batter.rbi)
                team_stats['StatsSB'] += int(batter.sb)
                # calc ab and gp for use in ops weighting
                avg_ab_per_team = 34.1  # per game
                avg_ab_per_player = avg_ab_per_team / 9
                batter_est_gp = batter.ab / avg_ab_per_player
                team_abs = int(team_stats['StatsTotalGP']) * avg_ab_per_player
                total_abs = team_abs + batter.ab
                # calc ops
                current_weighted_ops = float(team_stats['StatsOPS']) * team_abs
                batter_weighted_ops = batter.ops * batter.ab
                team_stats['StatsOPS'] = (current_weighted_ops + batter_weighted_ops) / total_abs
                team_stats['StatsTotalGP'] += batter_est_gp
            pitchers = [val for sublist in opt_pitchers.values() for val in sublist]
            pitchers.extend(opt_bench['pitchers'])
            team_stats['StatsW'] = int(standing['StatsW'])
            team_stats['StatsSV'] = int(standing['StatsSV'])
            team_stats['StatsK'] = int(standing['StatsK'])
            team_stats['StatsERA'] = float(standing['StatsERA'])
            team_stats['StatsWHIP'] = float(standing['StatsWHIP'])
            team_stats['StatsIP'] = float(standing['StatsIP'])
            for pitcher in pitchers:
                team_stats['StatsW'] += int(pitcher.w)
                team_stats['StatsSV'] += int(pitcher.sv)
                team_stats['StatsK'] += int(pitcher.k)
                # calc ip
                ip_add = team_stats['StatsIP'] + pitcher.ip
                current_ip = ip_add if (1 - ip_add % 1) < .3 else math.ceil(ip_add)
                # calc era and whip
                weighted_team_era = float(team_stats['StatsERA']) * float(team_stats['StatsIP'])
                weighted_pitcher_era = pitcher.era * pitcher.ip
                team_stats['StatsERA'] = (weighted_team_era + weighted_pitcher_era) / current_ip
                weighted_team_whip = float(team_stats['StatsWHIP']) * float(team_stats['StatsIP'])
                weighted_pitcher_whip = pitcher.whip * pitcher.ip
                team_stats['StatsWHIP'] = (weighted_team_whip + weighted_pitcher_whip) / current_ip
                team_stats['StatsIP'] = current_ip
            team_stats['TEAM_NAME'] = standing['PointsTeam']
            team_stats['manager_guids'] = standing['manager_guids']
    return team_stats


def batting_roster_optimizer(team_dict, ros_projection_list, league_pos_dict):
    """Optimizes Batting Roster for remainder of year\n
    Args:\n
        team_dict: dict of players on team.\n
        ros_projection_list: Rest of Season projection list.\n
        league_pos_dict: dict of team positions.\n
    Returns:\n
        dict of recommended starting batters.\n
    Raises:\n
        None.
    """
    team_player_list = []
    for player_proj, roster_player in itertools.product(ros_projection_list, team_dict['ROSTER']):
        if player_comparer(roster_player, player_proj):
            # for player_proj in ros_projection_list:
            #     if any(team_comparer(player_proj.team, roster_player['TEAM']) and
            #            name_comparer(player_proj.name, roster_player['NAME'])
            #            for roster_player in team_dict['ROSTER']):
            team_player_list.append(player_proj)
    sorted(team_player_list, key=operator.attrgetter('dollarValue'))
    starting_batters = {}
    batting_pos_scarc = order_batting_pos_by_scarcity(league_pos_dict['Batting POS'])
    batting_pos_scarc_elig = []
    pos_elig_dict = {}
    for pos in batting_pos_scarc:
        for player in team_player_list:
            if pos == "C" and "CF" in player.pos:
                continue
            elif pos in player.pos or (pos == "OF" and ("RF" in player.pos or "LF" in player.pos
                                                        or "CF" in player.pos)):
                if pos not in pos_elig_dict:
                    pos_elig_dict[pos] = 1
                else:
                    pos_elig_dict[pos] += 1
            elif pos == "Util":
                pos_elig_dict[pos] = len(team_player_list)
    for pos in batting_pos_scarc:
        if pos in pos_elig_dict:
            if pos_elig_dict[pos] == 1:
                batting_pos_scarc_elig.append(pos)
    for pos in batting_pos_scarc:
        if pos in pos_elig_dict:
            if pos_elig_dict[pos] != 1:
                batting_pos_scarc_elig.append(pos)
    for pos in batting_pos_scarc_elig:
        i = 0
        multi_pos = False
        while i < len(team_player_list):
            player = team_player_list[i]
            if pos == "C" and "CF" in player.pos:
                i += 1
            elif pos in player.pos or pos == "Util" or (pos == "OF" and ("RF" in player.pos or "LF" in player.pos
                                                                         or "CF" in player.pos)):
                if multi_pos is True or batting_pos_scarc_elig.count(pos) > 1:
                    multi_pos = True
                    if (pos in starting_batters and len(starting_batters[pos]) < batting_pos_scarc_elig.count(pos)):
                        starting_batters[pos].append(player)
                        del team_player_list[i]
                    elif pos not in starting_batters:
                        starting_batters[pos] = [player]
                        del team_player_list[i]
                    else:
                        i += 1
                else:
                    multi_pos = False
                    if pos in starting_batters:
                        i += 1
                    else:
                        starting_batters[pos] = [player]
                        del team_player_list[i]
            else:
                i += 1
    return starting_batters


def order_batting_pos_by_scarcity(league_batting_roster_pos):
    """Order league specific roster batting positions based on position scarcity\n
    Args:\n
        league_batting_roster_pos: Yahoo! league roster batting positions.\n
    Returns:\n
        ordered list of league roster positions based on scarcity.\n
    Raises:\n
        None.
    """
    scarcity_order = ["C", "SS", "2B", "MI", "3B", "1B", "CI",
                      "IF", "CF", "LF", "RF", "OF", "Util"]
    ordered_roster_pos_list = []
    for pos in scarcity_order:
        while pos in league_batting_roster_pos:
            ordered_roster_pos_list.append(pos)
            league_batting_roster_pos.remove(pos)
    return ordered_roster_pos_list


def pitching_roster_optimizer(team_dict, ros_projection_list, league_pos_dict, current_stangings, league):
    """Optimizes Pitching Roster for remainder of year\n
    Args:\n
        team_dict: dict of players on team.\n
        ros_projection_list: Rest of Season projection list.\n
        league_pos_dict: dict of team positions.\n
        current_stangings: current league standings.\n
        league_settings: league settings.\n
    Returns:\n
        dict of recommended starting pitchers.\n
    Raises:\n
        None.
    """
    team_player_list = []
    current_ip = 0
    starter_ip = 0
    for standing in current_stangings:
        # if standing['PointsTeam'] == team_dict['TEAM_NAME']:
        if [mg for mg in standing['manager_guids'] if mg in team_dict['manager_guids']]:
            current_ip += int(math.ceil(float(standing['StatsIP'])))
    for player_proj, roster_player in itertools.product(ros_projection_list, team_dict['ROSTER']):
        if player_comparer(roster_player, player_proj):
            # for player_proj in ros_projection_list:
            #     if any(team_comparer(player_proj.team, roster_player['TEAM']) and
            #            name_comparer(player_proj.name, roster_player['NAME'])
            #            for roster_player in team_dict['ROSTER']):
            team_player_list.append(player_proj)
    sorted(team_player_list, key=operator.attrgetter('dollarValue'))
    starting_pitchers = {}
    pitching_pos = league_pos_dict['Pitching POS']
    for pos in pitching_pos:
        if pos not in starting_pitchers:
            starting_pitchers[pos] = []
        i = 0
        regex_pos = re.compile(pos)
        multi_pos = False
        if isinstance(league, dict):
            max_ip = league['Max Innings Pitched']
        else:
            max_ip = league.max_ip
        if current_ip >= max_ip:
            break
        else:
            while i < len(team_player_list):
                player = team_player_list[i]
                if player.ip + current_ip > max_ip:
                    player = partial_pitcher(player, max_ip, current_ip)
                if filter(regex_pos.match, player.pos) or pos == "P":
                    if (pos == "SP" and not player.is_sp) or (pos == "RP" and player.is_sp):
                        i += 1
                        continue
                    elif multi_pos is True or pitching_pos.count(pos) > 1:
                        multi_pos = True
                        if (filter(regex_pos.match, starting_pitchers.keys()) and
                                len(starting_pitchers[pos]) < pitching_pos.count(pos)):
                            starting_pitchers[pos].append(player)
                            current_ip += player.ip
                            starter_ip += player.ip
                            del team_player_list[i]
                        elif not filter(regex_pos.match, starting_pitchers.keys()):
                            starting_pitchers[pos] = [player]
                            current_ip += player.ip
                            starter_ip += player.ip
                            del team_player_list[i]
                        else:
                            i += 1
                    else:
                        multi_pos = False
                        if filter(regex_pos.match, starting_pitchers.keys()):
                            i += 1
                        else:
                            starting_pitchers[pos] = [player]
                            current_ip += player.ip
                            starter_ip += player.ip
                            del team_player_list[i]
                else:
                    i += 1
    starting_pitchers['Starter IP'] = starter_ip
    return starting_pitchers


def bench_roster_optimizer(team_dict, ros_batter_projection_list, ros_pitcher_projection_list, league_pos_dict,
                           current_stangings, league, optimized_batters, optimized_pitchers):
    """Optimizes Bench Roster for remainder of year\n
    Args:\n
        team_dict: dict of players on team.\n
        ros_batter_projection_list: Rest of Season batter projection list.\n
        ros_pitcher_projection_list: Rest of Season pitcher projection list.\n
        league_pos_dict: dict of team positions.\n
        current_stangings: current league standings.\n
        league_settings: league settings.\n
        optimized_batters: optimized batters from batter_roster_optimizer.\n
        optimized_pitchers: optimized batters from pitcher_roster_optimizer.\n
    Returns:\n
        dict of recommended bench players.\n
    Raises:\n
        None.
    """
    bench_pos = league_pos_dict['Bench POS']
    bench_roster_list = []
    team_player_list = []
    starter_ip = optimized_pitchers.pop('Starter IP')
    opt_batters = list(sum(optimized_batters.values(), []))
    opt_pitchers = list(sum(optimized_pitchers.values(), []))
    for player in team_dict['ROSTER']:
        if (not any(player_comparer(player, batter)
                    for batter in opt_batters) and
                not any(player_comparer(player, pitcher)
                        for pitcher in opt_pitchers)):
            bench_roster_list.append(player)
    for player_proj, bench_player in itertools.product(ros_pitcher_projection_list,
                                                       bench_roster_list):
        if player_comparer(bench_player, player_proj):
            # for player in ros_pitcher_projection_list:
            #     if any(team_comparer(player.team, bench_player['TEAM']) and
            #            name_comparer(player.name, bench_player['NAME'])
            #            for bench_player in bench_roster_list):
            team_player_list.append(player_proj)
    for player_proj, bench_player in itertools.product(ros_batter_projection_list,
                                                       bench_roster_list):
        if player_comparer(bench_player, player_proj):
            # for player in ros_batter_projection_list:
            #     if any(team_comparer(player.team, bench_player['TEAM']) and
            #            name_comparer(player.name, bench_player['NAME'])
            #            for bench_player in bench_roster_list):
            team_player_list.append(player_proj)
    bench_players = {'pitchers': [], 'batters': []}
    current_ip = 0
    bench_ip = 0
    for standing in current_stangings:
        # if standing['PointsTeam'] == team_dict['TEAM_NAME']:
        if [mg for mg in standing['manager_guids'] if mg in team_dict['manager_guids']]:
                current_ip += int(math.ceil(float(standing['StatsIP'])))
    current_ip += starter_ip
    for player in team_player_list:
        if player.category == "pitcher":
            if isinstance(league, dict):
                max_ip = league['Max Innings Pitched']
            else:
                max_ip = league.max_ip
            if current_ip < max_ip:
                if player.ip + current_ip > max_ip:
                    player = partial_pitcher(player, max_ip, current_ip)
                bench_players['pitchers'].append(player)
                current_ip += player.ip
                bench_ip += player.ip
                if (sum(map(len, bench_players.values()))) == len(bench_pos):
                    break
        else:
            bench_players['batters'].append(bench_batter(player))
            if (sum(map(len, bench_players.values()))) == len(bench_pos):
                break
    return bench_players


def partial_pitcher(player, max_ip, current_ip):
    """Calculates percentage of pitcher values based on remaining ip\n
    Args:\n
        player: player object.\n
        max_ip: maximum ip for the league.\n
        current_ip: current ip for the team.\n
    Returns:\n
        player object with stats based on remaining ip.\n
    Raises:\n
        None.
    """
    pitcher = copy.deepcopy(player)
    stat_pct = (float(max_ip) - current_ip) / pitcher.ip
    pitcher.ip *= stat_pct
    pitcher.w *= stat_pct
    pitcher.sv *= stat_pct
    pitcher.k *= stat_pct
    return pitcher


def bench_batter(player):
    """Reduces the stat values of a bench batter by a percentage\n
    Args:\n
        player: player object.\n
    Returns:\n
        player object with stats based percentage.\n
    Raises:\n
        None.
    """
    stat_pct = .10
    batter = copy.deepcopy(player)
    batter.ab *= stat_pct
    batter.r *= stat_pct
    batter.hr *= stat_pct
    batter.rbi *= stat_pct
    batter.sb *= stat_pct
    return batter


def single_player_rater_html(player_name, ros_batter_projection_list, ros_pitcher_projection_list):
    """Searches for and returns rating of and individual player\n
    Args:\n
        player_name: name of the player to search for.\n
        ros_batter_projection_list: Rest of Season batter projection list.\n
        ros_pitcher_projection_list: Rest of Season pitcher projection list.\n
    Returns:\n
        rated player object.\n
    Raises:\n
        None.
    """
    player = None
    norm_player_name = name_normalizer(player_name)
    player_name = player_name.lower()
    for player_proj in ros_pitcher_projection_list:
        if (norm_player_name['First'] == player_proj.normalized_first_name and
                norm_player_name['Last'] == player_proj.last_name):
            player = player_proj
    if player is None:
        for player_proj in ros_batter_projection_list:
            if (norm_player_name['First'] == player_proj.normalized_first_name and
                    norm_player_name['Last'] == player_proj.last_name):
                player = player_proj
    return player


def single_player_rater_db(player_name):
    """Searches for and returns rating of and individual player\n
    Args:\n
        player_name: name of the player to search for.\n
    Returns:\n
        rated player object.\n
    Raises:\n
        None.
    """
    player = None
    norm_player_name = name_normalizer(player_name)
    player_name = player_name.lower()
    player = BatterProjection.objects.filter(normalized_first_name=norm_player_name['First'],
                                             last_name=norm_player_name['Last'])
    #    player = queries.get_single_batter(norm_player_name)
    if not player:
        player = PitcherProjection.objects.filter(normalized_first_name=norm_player_name['First'],
                                                  last_name=norm_player_name['Last'])
        # player = queries.get_single_pitcher(norm_player_name)
    return player


def final_stats_projection(team_list, ros_proj_b_list, ros_proj_p_list, current_stangings, league):
    """Calculates final stats of the team based on an optimized lineup\n
    Args:\n
        team_list: a list of dicts of teams in the league with current rosters and stats.\n
        ros_proj_b_list: Rest of Season batter projection list.\n
        ros_proj_p_list: Rest of Season pitcher projection list.\n
        current_stangings: current league standings.\n
        league_settings: league settings.\n
    Returns:\n
        list of dicts of teams with full season stat projections.\n
    Raises:\n
        None.
    """
    final_standings = []
    for team in team_list:
        # TODO: refactor these lists before they get to this point
        if isinstance(league, dict):
            roster_pos = {'Batting POS': list(league['Batting POS']), 'Pitching POS': list(league['Pitching POS']),
                          'Bench POS': list(league['Bench POS']), 'DL POS': list(league['DL POS']),
                          'NA_POS': list(league['NA POS'])}
        else:
            roster_pos = {'Batting POS': list(league.batting_pos), 'Pitching POS': list(league.pitcher_pos),
                          'Bench POS': list(league.bench_pos), 'DL POS': list(league.dl_pos),
                          'NA_POS': list(league.na_pos)}
        optimized_team = team_optimizer(team, ros_proj_b_list, ros_proj_p_list, roster_pos, current_stangings,
                                        league)
        # TODO: this is a shitty way of finding a missing team, what if the guids simply don't match (ie new manager)?
        if optimized_team == {}:
            continue
        final_standings.append(optimized_team)
    return final_standings


# TODO: seems like this could be refactored/sped up
def rank_list(projected_final_stats_list):
    """Ranks each stat and calculates total points in final stat projections\n
    Args:\n
        projected_final_stats_list: a list of dicts of teams with full season stat projections.\n
    Returns:\n
        list of dicts of teams with full season stat projections, ranks, and final point totals.\n
    Raises:\n
        None.
    """
    stat_ranker(projected_final_stats_list, "R")
    stat_ranker(projected_final_stats_list, "HR")
    stat_ranker(projected_final_stats_list, "RBI")
    stat_ranker(projected_final_stats_list, "SB")
    stat_ranker(projected_final_stats_list, "OPS")
    stat_ranker(projected_final_stats_list, "W")
    stat_ranker(projected_final_stats_list, "SV")
    stat_ranker(projected_final_stats_list, "K")
    stat_ranker(projected_final_stats_list, "ERA", False)
    stat_ranker(projected_final_stats_list, "WHIP", False)
    for team in projected_final_stats_list:
        team['PointsTotal'] = sum([value for key, value in team.items() if 'Points' in key])
    projected_final_stats_list.sort(key=operator.itemgetter('PointsTotal'), reverse=True)
    return projected_final_stats_list


def stat_ranker(projected_final_stats_list, stat, reverse=True):
    """Orders stats by value and calculates point value\n
    Args:\n
        projected_final_stats_list: a list of dicts of teams with full season stat projections.\n
        stat: statistic to calculate\n
        reverse: whether or not to reverse the ranking (ERA/WHIP = False, else = True)\n
    Returns:\n
        list of dicts of teams with full season stat projections and rank for secific stat.\n
    Raises:\n
        None.
    """
    stats_title = "Stats" + stat
    points_title = "Points" + stat
    projected_final_stats_list.sort(key=operator.itemgetter(stats_title), reverse=reverse)
    points = 12
    highest_shared_point = 0
    new_stat_value = 0
    old_stat_value = 0
    for team in projected_final_stats_list:
        counter = collections.Counter([s[stats_title] for s in projected_final_stats_list])
        shared_count = counter[team[stats_title]]
        if shared_count > 1:
            new_stat_value = team[stats_title]
            if new_stat_value == 0 or new_stat_value != old_stat_value:
                highest_shared_point = points
            lowest_shared_point = (highest_shared_point - shared_count)
            shared_point_total = (((float(highest_shared_point) / 2) * (highest_shared_point + 1)) -
                                  ((float(lowest_shared_point) / 2) * (lowest_shared_point + 1)))
            shared_points = float(shared_point_total) / float(shared_count)
            team[points_title] = shared_points
            old_stat_value = new_stat_value
        else:
            highest_shared_point = 0
            team[points_title] = points
        points -= 1


# TODO: seems like this could be refactored/sped up
def league_volatility(sgp_dict, final_stats, factor=1):
    """Calculates volatility for each position. Volatility = # of teams within factor * SGP\n
    Args:\n
        sgp_dict: dict of sgp values for each statistic\n
        final_stats: list of dicts of teams with full season stat projections, ranks, and
        final point totals.\n
        factor: sgp multiplier\n
    Returns:\n
        list of dicts of teams with full season stat projections, ranks, final point totals,
        and upward/downward volatility.\n
    Raises:\n
        None.
    """
    calc_volatility(sgp_dict, final_stats, "R", factor)
    calc_volatility(sgp_dict, final_stats, "HR", factor)
    calc_volatility(sgp_dict, final_stats, "RBI", factor)
    calc_volatility(sgp_dict, final_stats, "SB", factor)
    calc_volatility(sgp_dict, final_stats, "OPS", factor)
    calc_volatility(sgp_dict, final_stats, "W", factor)
    calc_volatility(sgp_dict, final_stats, "SV", factor)
    calc_volatility(sgp_dict, final_stats, "K", factor)
    calc_volatility(sgp_dict, final_stats, "ERA", factor, False)
    calc_volatility(sgp_dict, final_stats, "WHIP", factor, False)
    for team in final_stats:
        team['Total_Upward_Volatility'] = sum([value for key, value in team.items()
                                               if 'UpVol' in key])
        team['Total_Downward_Volatility'] = sum([value for key, value in team.items()
                                                 if 'DownVol' in key])
    return final_stats


def calc_volatility(sgp_dict, final_stats, stat, factor, reverse=True):
    """Calculates volatility for individual stat. Volatility = # of teams within factor * SGP\n
    Args:\n
        sgp_dict: dict of sgp values for each statistic\n
        final_stats: list of dicts of teams with full season stat projections, ranks, and
        final point totals.\n
        stat: statistic to calculate\n
        factor: sgp multiplier\n
        reverse: whether or not to reverse the ranking (ERA/WHIP = False, else = True)\n
    Returns:\n
        list of dicts of teams with full season stat projections, ranks, final point totals,
        and upward/downward volatility for specific stat.\n
    Raises:\n
        None.
    """
    stats_title = "Stats" + stat
    up_vol_title = "UpVol_" + stat
    down_vol_title = "DownVol_" + stat
    sgp_title = stat + " SGP"
    sgp = abs(sgp_dict[sgp_title] * factor)
    final_stats.sort(key=operator.itemgetter(stats_title), reverse=reverse)
    list_length = len(final_stats)

    for i in range(list_length):
        up_counter = 0
        down_counter = 0
        j = i - 1
        k = i + 1
        current_team_stat = final_stats[i][stats_title]
        while j > 0 and (abs(final_stats[j][stats_title] - current_team_stat) <= abs(sgp)):
            if final_stats[j][stats_title] - current_team_stat == sgp:
                up_counter -= .5
            j -= 1
            up_counter += 1
        while (k < list_length and
               (abs(current_team_stat - final_stats[k][stats_title]) <= abs(sgp))):
            if current_team_stat - final_stats[k][stats_title] == sgp:
                down_counter -= .5
            k += 1
            down_counter += 1
        final_stats[i][up_vol_title] = up_counter
        final_stats[i][down_vol_title] = down_counter


def roster_change_analyzer(team_a, team_a_players, team_b, team_b_players, team_list, ros_proj_b_list, ros_proj_p_list,
                           current_standings, league, sgp_dict):
    """Analyzes value of trade for 2 teams\n
    Args:\n
        projected_volatility: projected volatility for league\n
        team_a: Team A dict\n
        team_a_players: list of players to be offered\n
        team_b: Team B dict\n
        team_b_players: list of players to be offered\n
        team_list: \n
        ros_proj_b_list: \n
        ros_proj_p_list: \n
        current_standings: \n
        league_settings: \n
        sgp_dict: \n
    Returns:\n
        Updated standings post trade\n
    Raises:\n
        None.
    """
    team_list = ast.literal_eval(team_list)
    team_a = ast.literal_eval(team_a)
    team_b = ast.literal_eval(team_b)
    for player in team_a_players:
        player = ast.literal_eval(player)
        for roster_player in team_a['ROSTER']:
            if (roster_player['TEAM'] == player['TEAM'] and
                    roster_player['LAST_NAME'] == player['LAST_NAME'] and
                    roster_player['NORMALIZED_FIRST_NAME'] == player['NORMALIZED_FIRST_NAME']):
                team_a['ROSTER'].remove(roster_player)
                break
        team_b['ROSTER'].append(copy.deepcopy(player))
    for player in team_b_players:
        player = ast.literal_eval(player)
        team_a['ROSTER'].append(copy.deepcopy(player))
        for roster_player in team_b['ROSTER']:
            if (roster_player['TEAM'] == player['TEAM'] and
                    roster_player['LAST_NAME'] == player['LAST_NAME'] and
                    roster_player['NORMALIZED_FIRST_NAME'] == player['NORMALIZED_FIRST_NAME']):
                team_b['ROSTER'].remove(roster_player)
                break
    for team in team_list:
        if team['TEAM_NUMBER'] == team_a['TEAM_NUMBER']:
            team_list.remove(team)
            team_list.append(team_a)
        if team['TEAM_NUMBER'] == team_b['TEAM_NUMBER']:
            team_list.remove(team)
            team_list.append(team_b)
    final_stats = final_stats_projection(team_list, ros_proj_b_list, ros_proj_p_list, current_standings, league)
    volatility_standings = league_volatility(sgp_dict, final_stats)
    ranked_standings = rank_list(volatility_standings)
    return ranked_standings


def evaluate_keepers(keepers, ros_proj_b_list, ros_proj_p_list):
    for keeper in keepers:
        for player in keeper['roster']:
            value = 0.0
            pos = []
            value_window = player['keeper_cost'] * 0.10
            if isinstance(ros_proj_b_list[0], dict):
                if player['category'] == 'batter':
                    for batter in ros_proj_b_list:
                        if (player['first_name'] == batter['normalized_first_name']
                                and player['last_name'] == batter['last_name']):
                            value = batter['dollarValue']
                            pos = batter['pos']
                    player['value'] = value or 0.00
                    player['positions'] = pos or player['positions']
                    player['worth_keeping'] = player['value'] - player['keeper_cost'] >= -value_window
                else:
                    for pitcher in ros_proj_p_list:
                        if (player['first_name'] == pitcher['normalized_first_name']
                                and player['last_name'] == pitcher['last_name']):
                            value = pitcher['dollarValue']
                            pos = pitcher['pos']
                        player['value'] = value or 0.00
                        player['positions'] = pos or player['positions']
                        player['worth_keeping'] = player['value'] - player['keeper_cost'] >= -value_window
            else:
                if player['category'] == 'batter':
                    for batter in ros_proj_b_list:
                        if (player['first_name'] == batter.normalized_first_name
                                and player['last_name'] == batter.last_name):
                            value = batter.dollarValue
                            pos = batter.pos
                        player['value'] = value or 0.00
                        player['positions'] = pos or player['positions']
                        player['worth_keeping'] = player['value'] - player['keeper_cost'] >= -value_window
                else:
                    for pitcher in ros_proj_b_list:
                        if (player['first_name'] == pitcher.normalized_first_name
                                and player['last_name'] == pitcher.last_name):
                            value = pitcher.dollarValue
                            pos = pitcher.pos
                        player['value'] = value or 0.00
                        player['positions'] = pos or player['positions']
                        player['worth_keeping'] = player['value'] - player['keeper_cost'] >= -value_window
    return keepers
