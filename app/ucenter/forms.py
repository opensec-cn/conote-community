import copy

from django import forms
from django.core import exceptions

from . import models
from conote.field import MyCheckboxInput, MyClearableFileInput, HeadersField


PLACE_HEADERS = '''X-XSS-Protection: 0
Access-Control-Allow-Origin: *
Content-Security-Policy: default-src 'self'
X-Frame-Options: ALLOW-FROM https://example.com/
X-Content-Type-Options: nosniff;
'''


class OptionForm(forms.Form):
    ignore_note = forms.BooleanField(label='忽略笔记', help_text='不记录笔记包含的URI', required=False)
    default_status_code = forms.IntegerField(label='默认状态码', help_text='文件不存在时返回的状态码', initial=200)
    filter = forms.CharField(
        label='URI白名单',
        help_text='只记录匹配上这个通配符的URI，<code>*</code>表示多个字符，<code>?</code>表示一个字符, <code>|</code>表示或者。'
                  '黑白名单同时存在时，只考虑白名单，留空则忽略。',
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': "*.action|*.do"
        })
    )
    drop = forms.CharField(
        label='URI黑名单',
        help_text='不记录匹配上这个通配符的URI，<code>*</code>表示多个字符，<code>?</code>表示一个字符, <code>|</code>表示或者。'
                  '黑白名单同时存在时，只考虑白名单，留空则忽略。',
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': "robots.txt|favicon.ico"
        }))
    headers = HeadersField(
        label='HTTP头',
        help_text='输出内容的时候同时输出的HTTP头（全局配置）',
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': PLACE_HEADERS}),
        required=False
    )
    serverchan_token = forms.CharField(label='Server酱SCKEY', help_text='填写Server酱的SCKEY，你将可以在微信接受到一些通知（如XSS收信通知等）', required=False)

    def clean_default_status_code(self):
        default_status_code = self.cleaned_data['default_status_code']
        if default_status_code >= 600 or default_status_code < 100:
            raise forms.ValidationError('状态码错误')

        return default_status_code
