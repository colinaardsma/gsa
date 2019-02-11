from datetime import datetime

from django import template
from django.template.defaultfilters import stringfilter
from django.forms.widgets import CheckboxInput

from ..helpers.normalizer import name_normalizer

register = template.Library()


@register.filter
@stringfilter
def url_safe_spaces(value):
    """Replaces a string with another string"""
    return value.replace(' ', '%20')


@register.filter
def divide(value, denom):
    """Divides a value by another value"""
    return value / denom


@register.filter
def subtract(value, arg):
    return value - arg


@register.filter
@stringfilter
def lower_and_remove_spaces(value):
    """Replaces a string with another string"""
    return value.lower().replace(' ', '')


@register.filter
def is_checkbox(field):
    """See if field is a checkbox"""
    if isinstance(field.field.widget, CheckboxInput):
        return True
    else:
        return False


@register.filter
@stringfilter
def remove_colon(value):
    """Replaces a string with another string"""
    return value.lower().replace(':', '')


@register.simple_tag
def update_variable(value):
    """Allows to update existing variable in template"""
    return value


@register.filter
def greater_than_eq_10_pct(value, arg):
    profit = value - arg
    great_threshold = arg * 0.10
    return profit >= great_threshold


@register.filter
def less_than_eq_10_pct(value, arg):
    profit = value - arg
    great_threshold = arg * 0.10
    return profit >= great_threshold


@register.filter
def get_league_no(value):
    return value.split('.l.')[1]


@register.filter
def create_player_dict(value, team):
    norm_name = name_normalizer(value)
    player_dict = {'name': value, 'normalized_first_name': norm_name['First'], 'last_name': norm_name['Last'],
                   'team': team}
    return player_dict


@register.filter
def is_in_past(value):
    return value.replace(tzinfo=None) < datetime.now()


@register.filter
def is_in_future(value):
    return value.replace(tzinfo=None) > datetime.now()


@register.filter
def current_league(leagues):
    current_leagues = []
    current_season = next(l for l in leagues if l.season == datetime.now().year)
    last_season = next(l for l in leagues if l.season == datetime.now().year - 1)

    print(current_season)
    print(last_season)

    if current_season:
        current_leagues.append(current_season)
        if current_season.draft_status == "predraft":
            current_leagues.append(last_season)
    elif last_season:
        current_leagues.append(last_season)

    return current_leagues
