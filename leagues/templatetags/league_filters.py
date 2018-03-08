from django import template
from django.forms.widgets import CheckboxInput

register = template.Library()


@register.filter
def is_checkbox(field):
    if isinstance(field.field.widget, CheckboxInput):
        return True
    else:
        return False
