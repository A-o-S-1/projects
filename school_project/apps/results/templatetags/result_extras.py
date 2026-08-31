from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Look up a dict value by a variable key in templates — Django's
    built-in `dict.key` lookup only works for literal, hardcoded keys."""
    if dictionary is None:
        return None
    return dictionary.get(key)
