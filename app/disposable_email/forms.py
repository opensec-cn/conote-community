import re
import socket
from django import forms
from django.core import exceptions
from django.conf import settings

from . import models
from conote.utils import query_dns


DOMAIN_REGEX = re.compile(r'\A([a-zA-Z0-9-_]+\.)*[a-zA-Z0-9][a-zA-Z0-9-_]*\.[a-zA-Z]{2,11}\Z', re.I | re.S)


class DomainForm(forms.Form):
    name = forms.RegexField(label='域名',
                            strip=True,
                            regex=DOMAIN_REGEX,
                            max_length=127,
                            required=True,
                            widget=forms.TextInput(attrs=dict(placeholder='example.com'))
                            )
    email = forms.EmailField(label='邮箱',
                             widget=forms.EmailInput(attrs=dict(placeholder='foo@example.com'))
                             )

    def __init__(self, user, **kwargs):
        super().__init__(**kwargs)
        self.user = user

    def clean_email(self):
        if models.MailBox.objects.filter(user=self.user, email=self.cleaned_data['email']).exists():
            raise exceptions.ValidationError('你已经添加过该邮箱')

        return self.cleaned_data['email']

    def clean_name(self):
        if not self.user.is_superuser:
            for reserve_domain in settings.O_RESERVE_DOMAINS:
                suffix = '.{}'.format(reserve_domain)
                if self.cleaned_data['name'] == reserve_domain or self.cleaned_data['name'].endswith(suffix):
                    raise exceptions.ValidationError('保留域名，不可以使用')

        if models.Domain.objects.exclude(user=self.user).filter(name=self.cleaned_data['name']).exists():
            raise exceptions.ValidationError('已有其他用户使用该域名')

        return self.cleaned_data['name']

    def clean(self):
        cleaned_data = super().clean()

        if 'name' in cleaned_data and 'email' in cleaned_data:
            suffix = '@{}'.format(cleaned_data['name'])
            if not cleaned_data['email'].endswith(suffix):
                self.add_error('email', '邮箱与域名不对应')
                return

            try:
                record = query_dns(cleaned_data['name'], 'MX')
                if record:
                    for a, b in (line.split() for line in record.split('\n')):
                        if b.rstrip('.') == settings.O_MAIN_DOMAIN:
                            return
                raise Exception()
            except socket.timeout:
                raise exceptions.ValidationError('MX记录获取错误，请重试')
            except Exception:
                self.add_error('name', f'请先将域名的MX记录设置为{settings.O_MAIN_DOMAIN}')
