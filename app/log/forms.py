import copy

from django import forms
from django.core import exceptions
from django.forms import formset_factory

from . import models
from conote.field import MyCheckboxInput, MyClearableFileInput, HeadersField
from conote.const import CODE_LANGUAGE


PLACE_HEADERS = '''X-XSS-Protection: 0
Access-Control-Allow-Origin: *
Content-Security-Policy: default-src 'self'
X-Frame-Options: ALLOW-FROM https://example.com/
X-Content-Type-Options: nosniff;
'''


class NoteForm(forms.ModelForm):
    title = forms.CharField(label='标题', required=True)
    attachment = forms.FileField(label='文件',
                                 help_text='需要显示的文件',
                                 required=True,
                                 widget=MyClearableFileInput(
                                     attrs={'style': 'position: absolute; clip: rect(0px 0px 0px 0px);',
                                               'id': 'fileinput', 'class': 'form-control filestyle'})
                                 )
    language = forms.ChoiceField(label='语言', required=True, choices=CODE_LANGUAGE)
    content = forms.CharField(label='内容', widget=forms.Textarea(attrs={'rows': 10}), strip=False, required=False)
    content_type = forms.CharField(label='Content Type', required=True,
                                   help_text='更多类型请<a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Complete_list_of_MIME_types" target="_blank">阅读文档</a>')
    headers = HeadersField(
        label='HTTP头',
        help_text='输出内容的时候同时输出的HTTP头',
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': PLACE_HEADERS}),
        required=False
    )

    class Meta:
        model = models.Note
        fields = [
            'filename',
            'title',
            'content_type',
            'attachment',
            'language',
            'content',
            'headers'
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        fields = kwargs.pop('init_fields', [])
        super().__init__(*args, **kwargs)
        temp_fields = copy.deepcopy(self.fields)
        for field, _ in temp_fields.items():
            if field not in fields:
                self.fields.pop(field)

    def clean_filename(self):
        if self.cleaned_data['filename'] != self.instance.filename and self.user.note_set.filter(filename=self.cleaned_data['filename']).exists():
            raise exceptions.ValidationError('文件名已存在')

        return self.cleaned_data['filename']


class ShortDomainForm(forms.ModelForm):
    target = forms.URLField(label='目标网址')

    class Meta:
        model = models.ShortDomain
        fields = [
            'target',
            'reserve_params'
        ]
