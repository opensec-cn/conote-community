from django import template
from conote.ipdata.parser import IPData


register = template.Library()


@register.filter
def location(data):
    data = IPData().find(data)
    return '/'.join(data.strip().split())
