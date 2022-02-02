import re

from django import template
from django.utils.encoding import force_str
from conote.const import VICTIM_SORT


register = template.Library()


@register.simple_tag
def victim_sort(key):
    return force_str(dict(VICTIM_SORT).get(key, key))
