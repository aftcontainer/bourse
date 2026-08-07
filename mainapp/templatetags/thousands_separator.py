from django import template
from django.template.defaultfilters import stringfilter


register = template.Library()

@register.filter
@stringfilter
def intpoint(value):
    try:
        return '{:,}'.format(int(value)).replace(",",".")
    except (ValueError,TypeError):
        return value