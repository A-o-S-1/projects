from django import template
from django.urls import NoReverseMatch, reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, url_name, css_class="is-active"):
    """
    Returns css_class if the current request path matches the given URL
    name, else ''. Used in the navbar so the current page's nav link gets
    both a visual indicator and aria-current="page" for screen readers —
    without repeating '{% url ... as x %}' boilerplate for every link.
    """
    request = context.get("request")
    if not request:
        return ""
    try:
        target = reverse(url_name)
    except NoReverseMatch:
        return ""
    return css_class if request.path == target else ""


@register.simple_tag(takes_context=True)
def nav_aria_current(context, url_name):
    request = context.get("request")
    if not request:
        return ""
    try:
        target = reverse(url_name)
    except NoReverseMatch:
        return ""
    return mark_safe('aria-current="page"') if request.path == target else ""
