from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _
from django.db import transaction
from django.db.models import F

from . import models


class MyUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password', 'token')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_vip',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    list_display = ('username', 'email', 'is_vip', 'is_staff', 'is_superuser', 'date_joined')
    list_display_links = ('username', )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_vip')
    actions = ['set_vip']

    @transaction.atomic
    def set_vip(self, request, queryset):
        queryset.update(is_vip=True)
    set_vip.short_description = '切换为VIP用户'


admin.site.register(models.User, MyUserAdmin)
