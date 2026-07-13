from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Permet d'accéder à dictionary[key] depuis un template Django.
    Usage : {{ mon_dict|get_item:"ma_cle" }}
    """
    if not dictionary:
        return None
    return dictionary.get(key)
