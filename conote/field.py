import json

from django import forms
from django.forms.widgets import CheckboxInput, ClearableFileInput, Textarea
from django.core.exceptions import ValidationError

HEADERS_BLACKLIST = ('set-cookie', 'content-length', )


class MyCheckboxInput(CheckboxInput):
    template_name = 'widgets/checkbox.html'


class MyClearableFileInput(ClearableFileInput):
    template_name = 'widgets/clearable_file_input.html'


class HeadersField(forms.JSONField):
    def __init__(self, max_line=50, empty_value=None, blacklist=HEADERS_BLACKLIST, whitelist=None, *args, **kwargs):
        self.max_line = max_line
        self.empty_value = empty_value or []
        self.blacklist = blacklist
        self.whitelist = whitelist
        super().__init__(*args, **kwargs)

    def text_to_headers(self, text):
        headers = []
        try:
            i = 0
            for line in text.strip().split('\n'):
                i += 1
                if i > self.max_line:
                    raise ValidationError('HTTP头过多')

                key, val = line.split(':', maxsplit=1)
                key = key.strip()
                val = val.strip()

                if self.whitelist and key.lower() not in map(str.lower, self.whitelist):
                    raise ValidationError('不允许使用{}头'.format(key))

                if key.lower() in map(str.lower, self.blacklist):
                    raise ValidationError('不允许使用{}头'.format(key))

                headers.append((key, val))
        except ValidationError as e:
            raise e
        except:
            raise ValidationError('HTTP头解析错误，格式是每行一个“Key: Value”')
        else:
            return headers

    def headers_to_text(self, headers):
        text = []
        for key, val in headers:
            text.append('{}: {}'.format(key, val))

        return '\n'.join(text)

    def to_python(self, value: str):
        if value and isinstance(value, str):
            return self.text_to_headers(value)
        else:
            return self.empty_value

    def prepare_value(self, value):
        if isinstance(value, str) and value:
            try:
                value = json.loads(value)
            except:
                return value
            else:
                return self.headers_to_text(value)
        elif value and (isinstance(value, list) or isinstance(value, set)):
            return self.headers_to_text(value)
        else:
            return ''


class AceEditorTextarea(Textarea):
    template_name = 'widgets/ace_editor_textarea.html'
