from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.views.decorators.http import require_http_methods
from django.core import exceptions
from django.shortcuts import redirect, get_object_or_404, resolve_url

from . import models


@admin.register(models.Project, site=admin.site)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_time', 'user')
    readonly_fields = ('user', 'created_time', 'last_modify_time')
    search_fields = ('name', )
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'payload')
        }),
        ('信息', {
            'classes': ('wide',),
            'fields': readonly_fields
        }),
    )

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        obj.save()


@admin.register(models.Payload, site=admin.site)
class PayloadAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'data')
    readonly_fields = ('created_time', 'last_modify_time')
    search_fields = ('data', )
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'data', )
        }),
        ('信息', {
            'classes': ('wide',),
            'fields': readonly_fields
        }),
    )
