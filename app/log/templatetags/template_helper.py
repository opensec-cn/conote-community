import re
import base64

from django import template
from django.utils.encoding import force_text
from django.template.defaultfilters import stringfilter
from django.conf import settings
from django.utils.html import conditional_escape, strip_tags
from django.utils.safestring import mark_safe
from django.db.models import Count, F


register = template.Library()
VIEWER_PATTERN = re.compile(b'[^\x20-\x7E\x0A]')


@register.filter
def remove_unobservable(data):
    data = VIEWER_PATTERN.sub(b'.', data)
    return force_text(data)


@register.filter(is_safe=True)
@stringfilter
def base64encode(data: str):
    return base64.b64encode(data.encode(errors='ignore')).decode()
