from django.contrib import admin
from django.db.models import FilePathField
from django.forms.widgets import TextInput

from . import models


@admin.register(models.MailBox, site=admin.site)
class MailBoxAdmin(admin.ModelAdmin):
    list_display = ('email', 'user', 'created_time')
    readonly_fields = ('created_time', 'last_modify_time')
    search_fields = ('email', )
    fieldsets = (
        (None, {
            'fields': ('email', 'user')
        }),
        ('信息', {
            'classes': ('wide',),
            'fields': readonly_fields
        }),
    )


@admin.register(models.Envelope, site=admin.site)
class EnvelopeAdmin(admin.ModelAdmin):
    list_display = ('subject', 'mail_from', 'user', 'created_time', 'send_time')
    readonly_fields = ('created_time', 'last_modify_time')
    search_fields = ('subject', )
    fieldsets = (
        (None, {
            'fields': ('subject', 'mail_from', 'user', 'send_time', 'path')
        }),
        ('信息', {
            'classes': ('wide',),
            'fields': readonly_fields
        }),
    )
