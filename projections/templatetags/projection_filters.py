from django import template
from django.template.defaultfilters import stringfilter

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
