from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter
def intpoint(value):
    if value is None:
        return "0"

    try:
        return "{:,}".format(int(value)).replace(",", ".")
    except (ValueError, TypeError):
        return value