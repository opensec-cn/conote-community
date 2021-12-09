from django import template
from django.utils.encoding import force_text
from conote.ipdata.parser import IPData


register = template.Library()


@register.filter
def location(data):
    data = IPData().find(data)
    return '/'.join(data.strip().split())
