import re

from django import template
from django.utils.encoding import force_text
from conote.const import VICTIM_SORT


register = template.Library()


@register.simple_tag
def victim_sort(key):
    return force_text(dict(VICTIM_SORT).get(key, key))
