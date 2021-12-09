from django.contrib import admin

from . import models


@admin.register(models.CodeBox, site=admin.site)
class CodeBoxAdmin(admin.ModelAdmin):
    list_display = ('title', 'get_absolute_url', 'type', 'user', 'created_time')
    readonly_fields = ('created_time', 'last_modify_time')
    search_fields = ('title', )
    fieldsets = (
        (None, {
            'fields': ('title', 'code', 'type', 'user')
        }),
        ('信息', {
            'classes': ('wide',),
            'fields': readonly_fields
        }),
    )
