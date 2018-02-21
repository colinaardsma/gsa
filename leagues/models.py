# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Max
from django.contrib.postgres.fields import ArrayField


class League(models.Model):
    """The League Database Model"""
    # Foreign Keys
    users = models.ManyToManyField(User)
    prev_year_league = models.OneToOneField('League', null=True, blank=True, on_delete=models.DO_NOTHING,)
    # Descriptive Properties
    league_name = models.CharField(max_length=200)
    league_key = models.CharField(max_length=200)
    team_count = models.IntegerField()
    max_ip = models.IntegerField()
    season = models.IntegerField()
    batting_pos = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list)
    pitcher_pos = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list)
    bench_pos = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list)
    dl_pos = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list)
    na_pos = ArrayField(models.CharField(max_length=200, blank=True), blank=True, default=list)
    last_modified = models.DateTimeField(auto_now=True)
    draft_status = models.CharField(max_length=200)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    # Advanced Stats
    total_money_spent = models.IntegerField(blank=True, null=True)
    money_spent_on_batters = models.IntegerField(blank=True, null=True)
    money_spent_on_pitchers = models.IntegerField(blank=True, null=True)
    batter_budget_pct = models.FloatField(blank=True, null=True)
    pitcher_budget_pct = models.FloatField(blank=True, null=True)
    batters_over_zero_dollars = models.IntegerField(blank=True, null=True)
    pitchers_over_zero_dollars = models.IntegerField(blank=True, null=True)
    one_dollar_batters = models.IntegerField(blank=True, null=True)
    one_dollar_pitchers = models.IntegerField(blank=True, null=True)
    b_dollar_per_fvaaz = models.FloatField(blank=True, null=True)
    p_dollar_per_fvaaz = models.FloatField(blank=True, null=True)
    b_player_pool_mult = models.FloatField(blank=True, null=True)
    p_player_pool_mult = models.FloatField(blank=True, null=True)
    # SGP
    r_sgp = models.FloatField(blank=True, null=True)
    hr_sgp = models.FloatField(blank=True, null=True)
    rbi_sgp = models.FloatField(blank=True, null=True)
    sb_sgp = models.FloatField(blank=True, null=True)
    ops_sgp = models.FloatField(blank=True, null=True)
    avg_sgp = models.FloatField(blank=True, null=True)
    w_sgp = models.FloatField(blank=True, null=True)
    sv_sgp = models.FloatField(blank=True, null=True)
    k_sgp = models.FloatField(blank=True, null=True)
    era_sgp = models.FloatField(blank=True, null=True)
    whip_sgp = models.FloatField(blank=True, null=True)
    # Historical
    prev_year_key = models.CharField(max_length=200)
    # 3 Year Advanced Stats Avg
    total_money_spent_avg = models.IntegerField(blank=True, null=True)
    money_spent_on_batters_avg = models.IntegerField(blank=True, null=True)
    money_spent_on_pitchers_avg = models.IntegerField(blank=True, null=True)
    batter_budget_pct_avg = models.FloatField(blank=True, null=True)
    pitcher_budget_pct_avg = models.FloatField(blank=True, null=True)
    batters_over_zero_dollars_avg = models.IntegerField(blank=True, null=True)
    pitchers_over_zero_dollars_avg = models.IntegerField(blank=True, null=True)
    one_dollar_batters_avg = models.IntegerField(blank=True, null=True)
    one_dollar_pitchers_avg = models.IntegerField(blank=True, null=True)
    b_dollar_per_fvaaz_avg = models.FloatField(blank=True, null=True)
    p_dollar_per_fvaaz_avg = models.FloatField(blank=True, null=True)
    b_player_pool_mult_avg = models.FloatField(blank=True, null=True)
    p_player_pool_mult_avg = models.FloatField(blank=True, null=True)
    # 3 Year SGP Avg
    r_sgp_avg = models.FloatField(blank=True, null=True)
    hr_sgp_avg = models.FloatField(blank=True, null=True)
    rbi_sgp_avg = models.FloatField(blank=True, null=True)
    sb_sgp_avg = models.FloatField(blank=True, null=True)
    ops_sgp_avg = models.FloatField(blank=True, null=True)
    avg_sgp_avg = models.FloatField(blank=True, null=True)
    w_sgp_avg = models.FloatField(blank=True, null=True)
    sv_sgp_avg = models.FloatField(blank=True, null=True)
    k_sgp_avg = models.FloatField(blank=True, null=True)
    era_sgp_avg = models.FloatField(blank=True, null=True)
    whip_sgp_avg = models.FloatField(blank=True, null=True)

    def __str__(self):
        name = "%s %s" % (self.season, self.league_name)
        return name


def save_league(user, prev_year_league, league_name, league_key, team_count, max_ip, batting_pos, pitcher_pos,
                bench_pos, dl_pos, na_pos, draft_status, start_date, end_date, prev_year_key, season, r_sgp=0.00,
                hr_sgp=0.00, rbi_sgp=0.00, sb_sgp=0.00, ops_sgp=0.00, avg_sgp=0.00, w_sgp=0.00, sv_sgp=0.00, k_sgp=0.00,
                era_sgp=0.00, whip_sgp=0.00, batters_over_zero_dollars=0.00, pitchers_over_zero_dollars=0.00,
                one_dollar_batters=0.00, one_dollar_pitchers=0.00, total_money_spent=0, money_spent_on_batters=0.00,
                money_spent_on_pitchers=0.00, batter_budget_pct=0.00, pitcher_budget_pct=0.00, b_dollar_per_fvaaz=0.00,
                p_dollar_per_fvaaz=0.00, b_player_pool_mult=0.00, p_player_pool_mult=0.00):
    league = League(prev_year_league=prev_year_league, league_name=league_name, league_key=league_key,
                    team_count=team_count, max_ip=max_ip, batting_pos=batting_pos, pitcher_pos=pitcher_pos,
                    bench_pos=bench_pos, dl_pos=dl_pos, na_pos=na_pos, draft_status=draft_status, start_date=start_date,
                    end_date=end_date, prev_year_key=prev_year_key, season=season, r_sgp=r_sgp, hr_sgp=hr_sgp,
                    rbi_sgp=rbi_sgp, sb_sgp=sb_sgp, ops_sgp=ops_sgp, avg_sgp=avg_sgp, w_sgp=w_sgp, sv_sgp=sv_sgp,
                    k_sgp=k_sgp, era_sgp=era_sgp, whip_sgp=whip_sgp,
                    batters_over_zero_dollars=batters_over_zero_dollars,
                    pitchers_over_zero_dollars=pitchers_over_zero_dollars,
                    one_dollar_batters=one_dollar_batters, one_dollar_pitchers=one_dollar_pitchers,
                    total_money_spent=total_money_spent, money_spent_on_batters=money_spent_on_batters,
                    money_spent_on_pitchers=money_spent_on_pitchers,
                    batter_budget_pct=batter_budget_pct, pitcher_budget_pct=pitcher_budget_pct,
                    b_dollar_per_fvaaz=b_dollar_per_fvaaz, p_dollar_per_fvaaz=p_dollar_per_fvaaz,
                    b_player_pool_mult=b_player_pool_mult, p_player_pool_mult=p_player_pool_mult)
    league.save()
    league.users.add(user)
    league.save()
    user.profile.leagues.add(league)
    user.profile.save()
    return league


def update_league(league, user=None, prev_year_league=None, league_name=None, league_key=None, team_count=None,
                  max_ip=None, batting_pos=None, pitcher_pos=None, bench_pos=None, dl_pos=None, na_pos=None,
                  draft_status=None, start_date=None, end_date=None, prev_year_key=None, season=None, r_sgp=None,
                  hr_sgp=None, rbi_sgp=None, sb_sgp=None, ops_sgp=None, avg_sgp=None, w_sgp=None, sv_sgp=None,
                  k_sgp=None, era_sgp=None, whip_sgp=None, batters_over_zero_dollars=None,
                  pitchers_over_zero_dollars=None, one_dollar_batters=None, one_dollar_pitchers=None,
                  total_money_spent=None, money_spent_on_batters=None, money_spent_on_pitchers=None,
                  batter_budget_pct=None, pitcher_budget_pct=None, b_dollar_per_fvaaz=None, p_dollar_per_fvaaz=None,
                  b_player_pool_mult=None, p_player_pool_mult=None):
    if user and user not in league.users.all():
        league.users.add(user)
        update_profile(user=user, league=league)
    if prev_year_league:
        league.prev_year_league = prev_year_league
    if league_name:
        league.league_name = league_name
    if league_key:
        league.league_key = league_key
    if team_count:
        league.team_count = team_count
    if max_ip:
        league.max_ip = max_ip
    if batting_pos:
        league.batting_pos = batting_pos
    if pitcher_pos:
        league.pitcher_pos = pitcher_pos
    if bench_pos:
        league.bench_pos = bench_pos
    if dl_pos:
        league.dl_pos = dl_pos
    if na_pos:
        league.na_pos = na_pos
    if draft_status:
        league.draft_status = draft_status
    if start_date:
        league.start_date = start_date
    if end_date:
        league.end_date = end_date
    if prev_year_key:
        league.prev_year_key = prev_year_key
    if season:
        league.season = season
    if r_sgp:
        league.r_sgp = r_sgp
    if hr_sgp:
        league.hr_sgp = hr_sgp
    if rbi_sgp:
        league.rbi_sgp = rbi_sgp
    if sb_sgp:
        league.sb_sgp = sb_sgp
    if ops_sgp:
        league.ops_sgp = ops_sgp
    if avg_sgp:
        league.avg_sgp = avg_sgp
    if w_sgp:
        league.w_sgp = w_sgp
    if sv_sgp:
        league.sv_sgp = sv_sgp
    if k_sgp:
        league.k_sgp = k_sgp
    if era_sgp:
        league.era_sgp = era_sgp
    if whip_sgp:
        league.whip_sgp = whip_sgp
    if batters_over_zero_dollars:
        league.batters_over_zero_dollars = batters_over_zero_dollars
    if pitchers_over_zero_dollars:
        league.pitchers_over_zero_dollars = pitchers_over_zero_dollars
    if one_dollar_batters:
        league.one_dollar_batters = one_dollar_batters
    if one_dollar_pitchers:
        league.one_dollar_pitchers = one_dollar_pitchers
    if total_money_spent:
        league.total_money_spent = total_money_spent
    if money_spent_on_batters:
        league.money_spent_on_batters = money_spent_on_batters
    if money_spent_on_pitchers:
        league.money_spent_on_pitchers = money_spent_on_pitchers
    if batter_budget_pct:
        league.batter_budget_pct = batter_budget_pct
    if pitcher_budget_pct:
        league.pitcher_budget_pct = pitcher_budget_pct
    if b_dollar_per_fvaaz:
        league.b_dollar_per_fvaaz = b_dollar_per_fvaaz
    if p_dollar_per_fvaaz:
        league.p_dollar_per_fvaaz = p_dollar_per_fvaaz
    if b_player_pool_mult:
        league.b_player_pool_mult = b_player_pool_mult
    if p_player_pool_mult:
        league.p_player_pool_mult = p_player_pool_mult

    league.save()
    return league


# TODO: this needs to be refactored to include multiple years in case of user with multiple leagues and some that have not yet drafted
def max_year_leagues(user):
    try:
        user_leagues = user.profile.leagues.filter(draft_status='postdraft')
    except User.DoesNotExist:
        user_leagues = None
    if not user_leagues:
        return None

    max_year = user_leagues.aggregate(Max('season'))['season__max']
    return user_leagues.filter(season=max_year)


def calc_three_year_avgs(league_key):
    r_sgp_list = []
    rbi_sgp_list = []
    hr_sgp_list = []
    sb_sgp_list = []
    avg_sgp_list = []
    ops_sgp_list = []
    w_sgp_list = []
    sv_sgp_list = []
    k_sgp_list = []
    era_sgp_list = []
    whip_sgp_list = []
    total_money_spent_avg_list = []
    money_spent_on_batters_avg_list = []
    money_spent_on_pitchers_avg_list = []
    batter_budget_pct_avg_list = []
    pitcher_budget_pct_avg_list = []
    batters_over_zero_dollars_avg_list = []
    pitchers_over_zero_dollars_avg_list = []
    one_dollar_batters_avg_list = []
    one_dollar_pitchers_avg_list = []
    b_dollar_per_fvaaz_avg_list = []
    p_dollar_per_fvaaz_avg_list = []
    # TODO: populate mults
    b_player_pool_mult_avg_list = []
    p_player_pool_mult_avg_list = []

    league = League.objects.get(league_key=league_key)
    if league:
        r_sgp_list.append(league.r_sgp)
        rbi_sgp_list.append(league.rbi_sgp)
        hr_sgp_list.append(league.hr_sgp)
        sb_sgp_list.append(league.sb_sgp)
        avg_sgp_list.append(league.avg_sgp)
        ops_sgp_list.append(league.ops_sgp)
        w_sgp_list.append(league.w_sgp)
        sv_sgp_list.append(league.sv_sgp)
        k_sgp_list.append(league.k_sgp)
        era_sgp_list.append(league.era_sgp)
        whip_sgp_list.append(league.whip_sgp)
        total_money_spent_avg_list.append(league.total_money_spent)
        money_spent_on_batters_avg_list.append(league.money_spent_on_batters)
        money_spent_on_pitchers_avg_list.append(league.money_spent_on_pitchers)
        batter_budget_pct_avg_list.append(league.batter_budget_pct)
        pitcher_budget_pct_avg_list.append(league.pitcher_budget_pct)
        batters_over_zero_dollars_avg_list.append(league.batters_over_zero_dollars)
        pitchers_over_zero_dollars_avg_list.append(league.pitchers_over_zero_dollars)
        one_dollar_batters_avg_list.append(league.one_dollar_batters)
        one_dollar_pitchers_avg_list.append(league.one_dollar_pitchers)
        b_dollar_per_fvaaz_avg_list.append(league.b_dollar_per_fvaaz)
        p_dollar_per_fvaaz_avg_list.append(league.p_dollar_per_fvaaz)
        b_player_pool_mult_avg_list.append(league.b_player_pool_mult)
        p_player_pool_mult_avg_list.append(league.p_player_pool_mult)
        try:
            prev_year_league = League.objects.get(league_key=league.prev_year_key)
        except League.DoesNotExist:
            prev_year_league = None
        if prev_year_league:
            r_sgp_list.append(prev_year_league.r_sgp)
            rbi_sgp_list.append(prev_year_league.rbi_sgp)
            hr_sgp_list.append(prev_year_league.hr_sgp)
            sb_sgp_list.append(prev_year_league.sb_sgp)
            avg_sgp_list.append(prev_year_league.avg_sgp)
            ops_sgp_list.append(prev_year_league.ops_sgp)
            w_sgp_list.append(prev_year_league.w_sgp)
            sv_sgp_list.append(prev_year_league.sv_sgp)
            k_sgp_list.append(prev_year_league.k_sgp)
            era_sgp_list.append(prev_year_league.era_sgp)
            whip_sgp_list.append(prev_year_league.whip_sgp)
            total_money_spent_avg_list.append(prev_year_league.total_money_spent)
            money_spent_on_batters_avg_list.append(prev_year_league.money_spent_on_batters)
            money_spent_on_pitchers_avg_list.append(prev_year_league.money_spent_on_pitchers)
            batter_budget_pct_avg_list.append(prev_year_league.batter_budget_pct)
            pitcher_budget_pct_avg_list.append(prev_year_league.pitcher_budget_pct)
            batters_over_zero_dollars_avg_list.append(prev_year_league.batters_over_zero_dollars)
            pitchers_over_zero_dollars_avg_list.append(prev_year_league.pitchers_over_zero_dollars)
            one_dollar_batters_avg_list.append(prev_year_league.one_dollar_batters)
            one_dollar_pitchers_avg_list.append(prev_year_league.one_dollar_pitchers)
            b_dollar_per_fvaaz_avg_list.append(prev_year_league.b_dollar_per_fvaaz)
            p_dollar_per_fvaaz_avg_list.append(prev_year_league.p_dollar_per_fvaaz)
            b_player_pool_mult_avg_list.append(prev_year_league.b_player_pool_mult)
            p_player_pool_mult_avg_list.append(prev_year_league.p_player_pool_mult)
            try:
                two_years_prev_league = League.objects.get(league_key=prev_year_league.prev_year_key)
            except League.DoesNotExist:
                two_years_prev_league = None
            if two_years_prev_league:
                r_sgp_list.append(two_years_prev_league.r_sgp)
                rbi_sgp_list.append(two_years_prev_league.rbi_sgp)
                hr_sgp_list.append(two_years_prev_league.hr_sgp)
                sb_sgp_list.append(two_years_prev_league.sb_sgp)
                avg_sgp_list.append(two_years_prev_league.avg_sgp)
                ops_sgp_list.append(two_years_prev_league.ops_sgp)
                w_sgp_list.append(two_years_prev_league.w_sgp)
                sv_sgp_list.append(two_years_prev_league.sv_sgp)
                k_sgp_list.append(two_years_prev_league.k_sgp)
                era_sgp_list.append(two_years_prev_league.era_sgp)
                whip_sgp_list.append(two_years_prev_league.whip_sgp)
                total_money_spent_avg_list.append(two_years_prev_league.total_money_spent)
                money_spent_on_batters_avg_list.append(two_years_prev_league.money_spent_on_batters)
                money_spent_on_pitchers_avg_list.append(two_years_prev_league.money_spent_on_pitchers)
                batter_budget_pct_avg_list.append(two_years_prev_league.batter_budget_pct)
                pitcher_budget_pct_avg_list.append(two_years_prev_league.pitcher_budget_pct)
                batters_over_zero_dollars_avg_list.append(two_years_prev_league.batters_over_zero_dollars)
                pitchers_over_zero_dollars_avg_list.append(two_years_prev_league.pitchers_over_zero_dollars)
                one_dollar_batters_avg_list.append(two_years_prev_league.one_dollar_batters)
                one_dollar_pitchers_avg_list.append(two_years_prev_league.one_dollar_pitchers)
                b_dollar_per_fvaaz_avg_list.append(two_years_prev_league.b_dollar_per_fvaaz)
                p_dollar_per_fvaaz_avg_list.append(two_years_prev_league.p_dollar_per_fvaaz)
                b_player_pool_mult_avg_list.append(two_years_prev_league.b_player_pool_mult)
                p_player_pool_mult_avg_list.append(two_years_prev_league.p_player_pool_mult)
    r_sgp_avg = sum(r_sgp_list) / len(r_sgp_list)
    rbi_sgp_avg = sum(rbi_sgp_list) / len(rbi_sgp_list)
    hr_sgp_avg = sum(hr_sgp_list) / len(hr_sgp_list)
    sb_sgp_avg = sum(sb_sgp_list) / len(sb_sgp_list)
    avg_sgp_avg = sum(avg_sgp_list) / len(avg_sgp_list)
    ops_sgp_avg = sum(ops_sgp_list) / len(ops_sgp_list)
    w_sgp_avg = sum(w_sgp_list) / len(w_sgp_list)
    sv_sgp_avg = sum(sv_sgp_list) / len(sv_sgp_list)
    k_sgp_avg = sum(k_sgp_list) / len(k_sgp_list)
    era_sgp_avg = sum(era_sgp_list) / len(era_sgp_list)
    whip_sgp_avg = sum(whip_sgp_list) / len(whip_sgp_list)
    total_money_spent_avg = sum(total_money_spent_avg_list) / len(total_money_spent_avg_list)
    money_spent_on_batters_avg = (sum(money_spent_on_batters_avg_list)
                                  / len(money_spent_on_batters_avg_list))
    money_spent_on_pitchers_avg = (sum(money_spent_on_pitchers_avg_list)
                                   / len(money_spent_on_pitchers_avg_list))
    batter_budget_pct_avg = sum(batter_budget_pct_avg_list) / len(batter_budget_pct_avg_list)
    pitcher_budget_pct_avg = sum(pitcher_budget_pct_avg_list) / len(pitcher_budget_pct_avg_list)
    batters_over_zero_dollars_avg = (sum(batters_over_zero_dollars_avg_list)
                                     / len(batters_over_zero_dollars_avg_list))
    pitchers_over_zero_dollars_avg = (sum(pitchers_over_zero_dollars_avg_list)
                                      / len(pitchers_over_zero_dollars_avg_list))
    one_dollar_batters_avg = sum(one_dollar_batters_avg_list) / len(one_dollar_batters_avg_list)
    one_dollar_pitchers_avg = sum(one_dollar_pitchers_avg_list) / len(one_dollar_pitchers_avg_list)
    b_dollar_per_fvaaz_avg = sum(b_dollar_per_fvaaz_avg_list) / len(b_dollar_per_fvaaz_avg_list)
    p_dollar_per_fvaaz_avg = sum(p_dollar_per_fvaaz_avg_list) / len(p_dollar_per_fvaaz_avg_list)
    b_player_pool_mult_avg = sum(b_player_pool_mult_avg_list) / len(b_player_pool_mult_avg_list)
    p_player_pool_mult_avg = sum(p_player_pool_mult_avg_list) / len(p_player_pool_mult_avg_list)

    league.r_sgp_avg = r_sgp_avg
    league.hr_sgp_avg = hr_sgp_avg
    league.rbi_sgp_avg = rbi_sgp_avg
    league.sb_sgp_avg = sb_sgp_avg
    league.ops_sgp_avg = ops_sgp_avg
    league.avg_sgp_avg = avg_sgp_avg
    league.w_sgp_avg = w_sgp_avg
    league.sv_sgp_avg = sv_sgp_avg
    league.k_sgp_avg = k_sgp_avg
    league.era_sgp_avg = era_sgp_avg
    league.whip_sgp_avg = whip_sgp_avg
    league.total_money_spent_avg = total_money_spent_avg
    league.money_spent_on_batters_avg = money_spent_on_batters_avg
    league.money_spent_on_pitchers_avg = money_spent_on_pitchers_avg
    league.batter_budget_pct_avg = batter_budget_pct_avg
    league.pitcher_budget_pct_avg = pitcher_budget_pct_avg
    league.batters_over_zero_dollars_avg = batters_over_zero_dollars_avg
    league.pitchers_over_zero_dollars_avg = pitchers_over_zero_dollars_avg
    league.one_dollar_batters_avg = one_dollar_batters_avg
    league.one_dollar_pitchers_avg = one_dollar_pitchers_avg
    league.b_dollar_per_fvaaz_avg = b_dollar_per_fvaaz_avg
    league.p_dollar_per_fvaaz_avg = p_dollar_per_fvaaz_avg
    league.b_player_pool_mult_avg = b_player_pool_mult_avg
    league.p_player_pool_mult_avg = p_player_pool_mult_avg

    league.save()
    return league


def dummy_league():
    league = League(avg_sgp=0,
                    avg_sgp_avg=0,
                    b_dollar_per_fvaaz=2.8867152723551364,
                    b_dollar_per_fvaaz_avg=2.9278729965790475,
                    b_player_pool_mult=2.375,
                    b_player_pool_mult_avg=2.375,
                    batter_budget_pct=0.6187720990035358,
                    batter_budget_pct_avg=0.6192661880489748,
                    batters_over_zero_dollars=177,
                    batters_over_zero_dollars_avg=175,
                    batting_pos=["C", "1B", "2B", "3B", "SS", "OF", "OF", "OF", "OF", "Util", "Util"],
                    bench_pos=["BN", "BN", "BN", "BN", "BN", "BN"],
                    dl_pos=["DL", "DL"],
                    era_sgp=-0.06777777777777781,
                    era_sgp_avg=-0.08185185185185188,
                    hr_sgp=7.777777777777778,
                    hr_sgp_avg=8.148148148148147,
                    k_sgp=39.333333333333336,
                    k_sgp_avg=40.00000000000001,
                    # last_modified="2018-01-28 (11:21:11.856) CST",
                    league_key="370.l.5091",
                    league_name="Grays Sports Almanac",
                    max_ip=1500,
                    money_spent_on_batters=1925,
                    money_spent_on_batters_avg=1933,
                    money_spent_on_pitchers=1186,
                    money_spent_on_pitchers_avg=1188,
                    na_pos=["NA", "NA"],
                    one_dollar_batters=18,
                    one_dollar_batters_avg=25,
                    one_dollar_pitchers=18,
                    one_dollar_pitchers_avg=21,
                    ops_sgp=0.00855555555555555,
                    ops_sgp_avg=0.007111111111111109,
                    p_dollar_per_fvaaz=2.0620231755340748,
                    p_dollar_per_fvaaz_avg=2.076577289354652,
                    p_player_pool_mult=4.45,
                    p_player_pool_mult_avg=4.45,
                    pitcher_budget_pct=0.38122790099646414,
                    pitcher_budget_pct_avg=0.3807338119510251,
                    pitcher_pos=["SP", "SP", "RP", "RP", "P", "P", "P", "P"],
                    pitchers_over_zero_dollars=123,
                    pitchers_over_zero_dollars_avg=124,
                    prev_year_key="357.l.3091",
                    r_sgp=26.444444444444443,
                    r_sgp_avg=21.48148148148148,
                    rbi_sgp=18.11111111111111,
                    rbi_sgp_avg=17.814814814814813,
                    sb_sgp=8.222222222222221,
                    sb_sgp_avg=8.222222222222221,
                    season=2017,
                    sv_sgp=8.777777777777779,
                    sv_sgp_avg=8.37037037037037,
                    team_count=12,
                    total_money_spent=3111,
                    total_money_spent_avg=3121,
                    w_sgp=3.6666666666666665,
                    w_sgp_avg=3.509259259259259,
                    whip_sgp=-0.014444444444444458,
                    whip_sgp_avg=-0.016666666666666673)
    return league


class Profile(models.Model):
    """The User database model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    leagues = models.ManyToManyField(League, blank=True)
    yahoo_guid = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(auto_now=True)
    location = models.CharField(max_length=30, blank=True)
    access_token = models.TextField(blank=True)
    token_expiration = models.DateTimeField(blank=True, null=True)
    refresh_token = models.CharField(max_length=200, blank=True)
    main_league = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return str(self.user)


def update_profile(user, league=None, username=None, hashed_password=None, email=None,
                   yahoo_guid=None, last_accessed=None,
                   location=None, access_token=None, token_expiration=None,
                   refresh_token=None, main_league=None):
    if league and league not in user.profile.leagues.all():
        user.profile.leagues.add(league)
    # if username:
    #     user.username = username
    # if hashed_password:
    #     # password = hashing.make_pw_hash(username, password) # hash password for storage in db
    #     user.password = hashed_password
    # if email:
    #     user.email = email
    if yahoo_guid:
        user.profile.yahoo_guid = yahoo_guid
    # if last_accessed:
    #     user.profile.last_accessed = last_accessed
    if location:
        user.profile.location = location
    if access_token:
        user.profile.access_token = access_token
    if token_expiration:
        user.profile.token_expiration = token_expiration
    if refresh_token:
        user.profile.refresh_token = refresh_token
    if main_league:
        user.profile.main_league = main_league
    user.save()
    # time.sleep(.5) # wait .5 seconds while post is entered into db and memcache
    # update_user_memcache(user, user_id)
    return user


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
