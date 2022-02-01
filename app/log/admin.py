from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _

from . import models


class DNSLogAdmin(admin.ModelAdmin):
    list_display = ('hostname', 'dns_type', 'user')


class WebLogAdmin(admin.ModelAdmin):
    list_display = ('path', 'ip_addr', 'user')


class NoteAdmin(admin.ModelAdmin):
    list_display = ('filename', 'content_type', 'user')


admin.site.register(models.DNSLog, DNSLogAdmin)
admin.site.register(models.WebLog, WebLogAdmin)
admin.site.register(models.Note, NoteAdmin)


@admin.register(models.ShortDomain, site=admin.site)
class ShortDomainAdmin(admin.ModelAdmin):
    list_display = ('target', 'user', 'reserve_params', 'click')
    readonly_fields = ('click', 'created_time', 'last_modify_time')
    search_fields = ('target', 'user')
    fieldsets = (
        (None, {
            'fields': ('target', 'user', 'reserve_params')
        }),
        ('信息', {
            'classes': ('wide',),
            'fields': readonly_fields
        }),
    )
