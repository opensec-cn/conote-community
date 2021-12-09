import os
import json
from uuid import uuid4
from django.db.models import JSONField

from django.db import models
from django.conf import settings
from django.template.defaultfilters import date
from django.utils import timezone
from django.db.models.signals import post_delete
from django.dispatch import receiver

from conote.utils import from10_to62, from62_to10
from conote.const import CODE_LANGUAGE, NOTE_CATEGORY


def return_object():
    return {}


def return_list():
    return []


def generate_attachment_filename(instance, filename):
    filename = str(uuid4())
    date_dir = date(timezone.localtime(timezone.now()), 'Y/m/d')

    return "attachment/%s/%s" % (date_dir, filename)


class WebLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.CASCADE)
    method = models.TextField('方法', default='GET')
    path = models.TextField('Path')
    ip_addr = models.GenericIPAddressField('IP地址')
    body = models.BinaryField('原始记录', blank=True, null=True)
    headers = JSONField('HTTP头', default=return_object)
    hostname = models.TextField('Host', default='')

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.path

    class Meta:
        ordering = ['-created_time']
        verbose_name = 'Web日志'
        verbose_name_plural = verbose_name


class DNSLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.CASCADE)
    ip_addr = models.GenericIPAddressField('IP地址', default='127.0.0.1')
    hostname = models.TextField('Host')
    dns_type = models.TextField('Dns类型')

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.hostname

    class Meta:
        ordering = ['-created_time']
        verbose_name = 'DNS日志'
        verbose_name_plural = verbose_name


class Note(models.Model):
    filename = models.CharField('文件名', max_length=256)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.CASCADE)
    attachment = models.FileField('附件', null=True, blank=True, upload_to=generate_attachment_filename)
    content_type = models.CharField('Content Type', default='application/octet-stream', max_length=128)
    content = models.TextField('文件内容', null=True, blank=True)
    title = models.CharField('标题', max_length=256, null=True, blank=True)
    language = models.CharField('代码语言', null=True, blank=True, choices=CODE_LANGUAGE, max_length=32)
    headers = JSONField('HTTP头', default=return_list)

    category = models.CharField('类型', max_length=16, choices=NOTE_CATEGORY, default='text')
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.filename

    class Meta:
        ordering = ['-created_time']
        verbose_name = '笔记'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return 'http://{}.{}/{}'.format(
            self.user.domain,
            settings.O_SERVER_DOMAIN,
            self.filename
        )


@receiver(post_delete, sender=Note)
def attachment_delete_handler(sender, **kwargs):
    instance = kwargs['instance']
    if instance.attachment:
        storage, path = instance.attachment.storage, instance.attachment.path
        storage.delete(path)


class ShortDomain(models.Model):
    target = models.TextField('原始链接')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.CASCADE)
    click = models.PositiveIntegerField('点击数', default=0)
    reserve_params = models.BooleanField('保留参数', default=False)

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.target

    class Meta:
        ordering = ['-created_time']
        verbose_name = '短域名'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return "http://{}/{}".format(settings.O_SHORT_DOMAIN, from10_to62(self.pk))


class DNSRecord(models.Model):
    ips = JSONField('目标IP', default=return_list)
    click = models.PositiveIntegerField('访问次数', default=0)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.CASCADE)

    last_visited = models.DateTimeField('上次访问时间')
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    limit_interval = 5

    def __str__(self):
        return self.ips

    class Meta:
        ordering = ['-created_time']
        verbose_name = 'DNS记录'
        verbose_name_plural = verbose_name

    def get_ip_display(self):
        return json.dumps(self.ips)
