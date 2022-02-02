import re

from django import template
from django.conf import settings
from django.utils.html import conditional_escape, strip_tags
from django.utils.safestring import mark_safe
from flanker.addresslib.address import EmailAddress


register = template.Library()


@register.filter
def display_email(email: EmailAddress):
    if email.display_name:
        return '{email.display_name} <{email.address}>'.format(email=email)
    else:
        return email.address
