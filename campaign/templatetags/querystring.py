
from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag(takes_context=True)
def qs_replace(context, **kwargs):
    """
    Usage in templates: href="?{% qs_replace page=3 %}"
    Keeps existing GET params, replaces only specified keys.
    """
    request = context["request"]
    params = request.GET.copy()
    for k, v in kwargs.items():
        if v is None or v == "":
            params.pop(k, None)
        else:
            params[k] = v
    return params.urlencode()