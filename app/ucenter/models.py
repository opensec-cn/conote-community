from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.crypto import get_random_string
from django.conf import settings
from django.db.models import JSONField


def get_domain_key():
    return get_random_string(8, 'abcdef0123456789')


def get_api_key():
    return get_random_string(32, 'abcdef0123456789')


def get_default_options():
    return dict(
        ignore_note=True,
        filter=None,
        drop='robots.txt|favicon.ico',
        default_status_code=200
    )


class User(AbstractUser):
    email = models.EmailField('邮箱', unique=True)
    auth_id = models.UUIDField('唯一ID', null=True, blank=True, unique=True)
    token = models.CharField('Token', max_length=256, blank=True, null=True)
    option = JSONField('设置', default=get_default_options)
    is_vip = models.BooleanField('VIP用户', default=False)

    domain = models.CharField('子域名', max_length=8, default=get_domain_key, unique=True)
    apikey = models.CharField('API密钥', max_length=32, default=get_api_key, unique=True)

    class Meta(AbstractUser.Meta):
        swappable = 'AUTH_USER_MODEL'

    def __str__(self):
        return self.username

    def get_user_domain(self):
        return "{}.{}".format(self.domain, settings.O_SERVER_DOMAIN)

    def get_dns_record(self):
        return "{}.{}".format(self.domain, settings.O_REBIND_DOMAIN)

    def refresh_apikey(self):
        self.apikey = get_api_key()
        self.save()
