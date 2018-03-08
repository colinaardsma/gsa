from django import template
from django.template.defaultfilters import stringfilter
from django.forms.widgets import CheckboxInput

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
