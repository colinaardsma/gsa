# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import models
from django.conf import settings

from leagues import models as league_models
from .helpers.player_creator import calc_batter_z_score, calc_pitcher_z_score

# Create your models here.


class BatterProjection(models.Model):
    """The Batter Projection Database Model"""
    # Descriptive Properties
    name = models.CharField(max_length=200)
    normalized_first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    pos = models.CharField(max_length=200)
    status = models.CharField(max_length=200)
    last_modified = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=200)
    # Raw Stat Properties
    ab = models.FloatField()
    r = models.FloatField()
    hr = models.FloatField()
    rbi = models.FloatField()
    sb = models.FloatField()
    avg = models.FloatField()
    ops = models.FloatField()
    # Initial zScore Properties
    zScoreR = models.FloatField()
    zScoreHr = models.FloatField()
    zScoreRbi = models.FloatField()
    zScoreSb = models.FloatField()
    zScoreAvg = models.FloatField()
    zScoreOps = models.FloatField()
    # Weighted (Multiplied by AB) Properties
    weightedR = models.FloatField()
    weightedHr = models.FloatField()
    weightedRbi = models.FloatField()
    weightedSb = models.FloatField()
    weightedAvg = models.FloatField()
    weightedOps = models.FloatField()
    # Weighted and RezScored Properties
    weightedZscoreR = models.FloatField()
    weightedZscoreHr = models.FloatField()
    weightedZscoreRbi = models.FloatField()
    weightedZscoreSb = models.FloatField()
    weightedZscoreAvg = models.FloatField()
    weightedZscoreOps = models.FloatField()
    # Values
    fvaaz = models.FloatField()
    dollarValue = models.FloatField()
    keeper = models.FloatField(default=0.0)
    # FA Status
    isFA = models.BooleanField(default=False)

    def setpos(self, x):
        self.pos = json.dumps(x)

    def getpos(self):
        return json.loads(self.pos)

    def __str__(self):
        return self.name


class BatterValue(models.Model):
    """The Batter Value Database Model"""
    # Foreign Keys
    batter = models.ForeignKey(BatterProjection, on_delete=models.CASCADE)
    league = models.ForeignKey(league_models.League, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    yahoo_guid = models.CharField(max_length=200)
    # Descriptive Properties
    name = models.CharField(max_length=200)
    normalized_first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    pos = models.CharField(max_length=200)
    last_modified = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=200)
    league_key = models.CharField(max_length=200)
    # Initial zScore Properties
    zScoreR = models.FloatField()
    zScoreHr = models.FloatField()
    zScoreRbi = models.FloatField()
    zScoreSb = models.FloatField()
    zScoreAvg = models.FloatField()
    zScoreOps = models.FloatField()
    # Weighted (Multiplied by AB) Properties
    weightedR = models.FloatField()
    weightedHr = models.FloatField()
    weightedRbi = models.FloatField()
    weightedSb = models.FloatField()
    weightedAvg = models.FloatField()
    weightedOps = models.FloatField()
    # Weighted and RezScored Properties
    weightedZscoreR = models.FloatField()
    weightedZscoreHr = models.FloatField()
    weightedZscoreRbi = models.FloatField()
    weightedZscoreSb = models.FloatField()
    weightedZscoreAvg = models.FloatField()
    weightedZscoreOps = models.FloatField()
    # Values
    fvaaz = models.FloatField()
    dollarValue = models.FloatField()
    keeper = models.FloatField(default=0.0)
    # FA Status
    isFA = models.BooleanField(default=False)

    def __str__(self):
        name = "%s|%s|%s" % (self.batter.name, self.league.league_name, self.user.name)
        return name


def save_batter(batter):
    batter = BatterProjection(name=batter['name'], normalized_first_name=batter['normalized_first_name'],
                              last_name=batter['last_name'], team=batter['team'], pos=batter['pos'],
                              status=batter['status'],
                              category=batter['category'], ab=batter['ab'], r=batter['r'],
                              hr=batter['hr'], rbi=batter['rbi'], sb=batter['sb'], avg=batter['avg'],
                              ops=batter['ops'], zScoreR=batter['zScoreR'], zScoreHr=batter['zScoreHr'],
                              zScoreRbi=batter['zScoreRbi'], zScoreSb=batter['zScoreSb'],
                              zScoreAvg=batter['zScoreAvg'], zScoreOps=batter['zScoreOps'],
                              weightedR=batter['weightedR'], weightedHr=batter['weightedHr'],
                              weightedRbi=batter['weightedRbi'], weightedSb=batter['weightedSb'],
                              weightedAvg=batter['weightedAvg'], weightedOps=batter['weightedOps'],
                              weightedZscoreR=batter['weightedZscoreR'],
                              weightedZscoreHr=batter['weightedZscoreHr'],
                              weightedZscoreRbi=batter['weightedZscoreRbi'],
                              weightedZscoreSb=batter['weightedZscoreSb'],
                              weightedZscoreAvg=batter['weightedZscoreAvg'],
                              weightedZscoreOps=batter['weightedZscoreOps'], fvaaz=batter['fvaaz'],
                              dollarValue=batter['dollarValue'], keeper=batter.get('keeper'), isFA=batter.get('isFA'))
    batter.save()
    return batter


def save_batter_values(yahoo_guid, league, batter_proj_list):
    batter_value_list = []
    for batter_proj in batter_proj_list:
        batter_values = calc_batter_z_score(batter_proj_list,
                                            league.batters_over_zero_dollars_avg,
                                            league.one_dollar_batters_avg,
                                            league.b_dollar_per_fvaaz_avg,
                                            league.b_player_pool_mult_avg)
        batter_proj_value = [batter for batter in batter_values
                             if batter.name == batter_proj.name
                             and batter.team == batter_proj.team
                             and batter.pos == batter_proj.pos][0]

        batter_value = BatterValue(name=batter_proj.name,
                                   normalized_first_name=batter_proj.normalized_first_name,
                                   last_name=batter_proj.last_name, team=batter_proj.team,
                                   pos=batter_proj.pos, category=batter_proj.category,
                                   league_key=league.league_key, yahoo_guid=yahoo_guid,
                                   zScoreR=batter_proj_value.zScoreR,
                                   zScoreHr=batter_proj_value.zScoreHr,
                                   zScoreRbi=batter_proj_value.zScoreRbi,
                                   zScoreSb=batter_proj_value.zScoreSb,
                                   zScoreAvg=batter_proj_value.zScoreAvg,
                                   zScoreOps=batter_proj_value.zScoreOps,
                                   weightedR=batter_proj_value.weightedR,
                                   weightedHr=batter_proj_value.weightedHr,
                                   weightedRbi=batter_proj_value.weightedRbi,
                                   weightedSb=batter_proj_value.weightedSb,
                                   weightedAvg=batter_proj_value.weightedAvg,
                                   weightedOps=batter_proj_value.weightedOps,
                                   weightedZscoreR=batter_proj_value.weightedZscoreR,
                                   weightedZscoreHr=batter_proj_value.weightedZscoreHr,
                                   weightedZscoreRbi=batter_proj_value.weightedZscoreRbi,
                                   weightedZscoreSb=batter_proj_value.weightedZscoreSb,
                                   weightedZscoreAvg=batter_proj_value.weightedZscoreAvg,
                                   weightedZscoreOps=batter_proj_value.weightedZscoreOps,
                                   fvaaz=batter_proj_value.fvaaz,
                                   dollarValue=batter_proj_value.dollarValue,
                                   keeper=batter_proj_value.keeper)
        batter_value.save()
        batter_value_list.append(batter_value)
    return batter_value_list


class PitcherProjection(models.Model):
    """The Pitcher Projection Database Model"""
    # Descriptive Properties
    name = models.CharField(max_length=200)
    normalized_first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    pos = models.CharField(max_length=200)
    is_sp = models.BooleanField()
    status = models.CharField(max_length=200)
    last_modified = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=200)
    # Raw Stat Properties
    ip = models.FloatField()
    w = models.FloatField()
    sv = models.FloatField()
    k = models.FloatField()
    era = models.FloatField()
    whip = models.FloatField()
    kip = models.FloatField()
    winsip = models.FloatField()
    # Initial zScore Properties
    zScoreW = models.FloatField()
    zScoreSv = models.FloatField()
    zScoreK = models.FloatField()
    zScoreEra = models.FloatField()
    zScoreWhip = models.FloatField()
    # Weighted (Multiplied by IP) Properties
    weightedW = models.FloatField()
    weightedSv = models.FloatField()
    weightedK = models.FloatField()
    weightedEra = models.FloatField()
    weightedWhip = models.FloatField()
    # Weighted and RezScored Properties
    weightedZscoreW = models.FloatField()
    weightedZscoreSv = models.FloatField()
    weightedZscoreK = models.FloatField()
    weightedZscoreEra = models.FloatField()
    weightedZscoreWhip = models.FloatField()
    # Values
    fvaaz = models.FloatField()
    dollarValue = models.FloatField()
    keeper = models.FloatField(default=0.0)
    # FA Status
    isFA = models.BooleanField(default=False)

    def setpos(self, x):
        self.pos = json.dumps(x)

    def getpos(self):
        return json.loads(self.pos)

    def __str__(self):
        return self.name


class PitcherValue(models.Model):
    """The Pitcher Value Database Model"""
    # Foreign Keys
    pitcher = models.ForeignKey(PitcherProjection, on_delete=models.CASCADE)
    league = models.ForeignKey(league_models.League, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Descriptive Properties
    name = models.CharField(max_length=200)
    normalized_first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    team = models.CharField(max_length=200)
    pos = models.CharField(max_length=200)
    last_modified = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=200)
    league_key = models.CharField(max_length=200)
    yahoo_guid = models.CharField(max_length=200)
    # Initial zScore Properties
    zScoreW = models.FloatField()
    zScoreSv = models.FloatField()
    zScoreK = models.FloatField()
    zScoreEra = models.FloatField()
    zScoreWhip = models.FloatField()
    # Weighted (Multiplied by IP) Properties
    weightedW = models.FloatField()
    weightedSv = models.FloatField()
    weightedK = models.FloatField()
    weightedEra = models.FloatField()
    weightedWhip = models.FloatField()
    # Weighted and RezScored Properties
    weightedZscoreW = models.FloatField()
    weightedZscoreSv = models.FloatField()
    weightedZscoreK = models.FloatField()
    weightedZscoreEra = models.FloatField()
    weightedZscoreWhip = models.FloatField()
    # Values
    fvaaz = models.FloatField()
    dollarValue = models.FloatField()
    keeper = models.FloatField(default=0.0)
    # FA Status
    isFA = models.BooleanField(default=False)

    def __str__(self):
        name = "%s|%s|%s" % (self.pitcher.name, self.league.league_name, self.user.name)
        return name


def save_pitcher(pitcher):
    pitcher = PitcherProjection(name=pitcher['name'], normalized_first_name=pitcher['normalized_first_name'],
                                last_name=pitcher['last_name'], team=pitcher['team'], pos=pitcher['pos'],
                                is_sp=pitcher['is_sp'], status=pitcher['status'], category=pitcher['category'],
                                ip=pitcher['ip'], w=pitcher['w'], sv=pitcher['sv'], k=pitcher['k'], era=pitcher['era'],
                                whip=pitcher['whip'], kip=pitcher['kip'], winsip=pitcher['winsip'],
                                zScoreW=pitcher['zScoreW'], zScoreSv=pitcher['zScoreSv'],
                                zScoreK=pitcher['zScoreK'], zScoreEra=pitcher['zScoreEra'],
                                zScoreWhip=pitcher['zScoreWhip'], weightedW=pitcher['weightedW'],
                                weightedSv=pitcher['weightedSv'], weightedK=pitcher['weightedK'],
                                weightedEra=pitcher['weightedEra'], weightedWhip=pitcher['weightedWhip'],
                                weightedZscoreW=pitcher['weightedZscoreW'],
                                weightedZscoreSv=pitcher['weightedZscoreSv'],
                                weightedZscoreK=pitcher['weightedZscoreK'],
                                weightedZscoreEra=pitcher['weightedZscoreEra'],
                                weightedZscoreWhip=pitcher['weightedZscoreWhip'], fvaaz=pitcher['fvaaz'],
                                dollarValue=pitcher['dollarValue'], keeper=pitcher.get('keeper'),
                                isFA=pitcher.get('isFA'))
    pitcher.save()
    return pitcher


def save_pitcher_values(yahoo_guid, league, pitcher_proj_list):
    pitcher_value_list = []
    for pitcher_proj in pitcher_proj_list:
        pitcher_values = calc_pitcher_z_score(pitcher_proj_list,
                                              league.pitchers_over_zero_dollars_avg,
                                              league.one_dollar_pitchers_avg,
                                              league.p_dollar_per_fvaaz_avg,
                                              league.p_player_pool_mult_avg)
        pitcher_proj_value = [pitcher for pitcher in pitcher_values
                              if pitcher.name == pitcher_proj.name
                              and pitcher.team == pitcher_proj.team
                              and pitcher.pos == pitcher_proj.pos][0]

        pitcher_value = PitcherValue(name=pitcher_proj.name,
                                     normalized_first_name=pitcher_proj.normalized_first_name,
                                     last_name=pitcher_proj.last_name, team=pitcher_proj.team,
                                     pos=pitcher_proj.pos, category=pitcher_proj.category,
                                     league_key=league.league_key, yahoo_guid=yahoo_guid,
                                     zScoreW=pitcher_proj_value.zScoreW,
                                     zScoreSv=pitcher_proj_value.zScoreSv,
                                     zScoreK=pitcher_proj_value.zScoreK,
                                     zScoreEra=pitcher_proj_value.zScoreEra,
                                     zScoreWhip=pitcher_proj_value.zScoreWhip,
                                     weightedW=pitcher_proj_value.weightedW,
                                     weightedSv=pitcher_proj_value.weightedSv,
                                     weightedK=pitcher_proj_value.weightedK,
                                     weightedEra=pitcher_proj_value.weightedEra,
                                     weightedWhip=pitcher_proj_value.weightedWhip,
                                     weightedZscoreW=pitcher_proj_value.weightedZscoreW,
                                     weightedZscoreSv=pitcher_proj_value.weightedZscoreSv,
                                     weightedZscoreK=pitcher_proj_value.weightedZscoreK,
                                     weightedZscoreEra=pitcher_proj_value.weightedZscoreEra,
                                     weightedZscoreWhip=pitcher_proj_value.weightedZscoreWhip,
                                     fvaaz=pitcher_proj_value.fvaaz,
                                     dollarValue=pitcher_proj_value.dollarValue,
                                     keeper=pitcher_proj_value.keeper)
        pitcher_value.save()
        pitcher_value_list.append(pitcher_value)
    return pitcher_value_list
