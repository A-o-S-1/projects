from django import template

register = template.Library()


@register.filter
def get_item(value, key):
    if value is None:
        return None
    try:
        if isinstance(value, dict):
            return value.get(key)
        return value[key]
    except (KeyError, IndexError, TypeError):
        return None
