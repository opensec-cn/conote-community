from django import forms
from django.core import exceptions

from . import models
from conote.field import AceEditorTextarea


class ProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = [
            'name',
            'description',
            'payload'
        ]
        widgets = {
            'payload': AceEditorTextarea()
        }
