import logging
import os
from pathlib import Path

from django.db import models
from django.shortcuts import resolve_url
from django.conf import settings
from django.utils.timezone import now
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_delete


logger = logging.getLogger('conote')


def gen_email_path():
    return os.path.join(settings.MEDIA_ROOT, 'email')


class Domain(models.Model):
    name = models.CharField('域名', max_length=128, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='用户',
        related_name='mail_domains',
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_time']
        verbose_name = '域名'
        verbose_name_plural = verbose_name


class MailBox(models.Model):
    email = models.EmailField('邮件地址', unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='用户',
        related_name='mail_boxes',
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.email

    class Meta:
        ordering = ['-created_time']
        verbose_name = '邮箱'
        verbose_name_plural = verbose_name


class Envelope(models.Model):
    subject = models.CharField('标题', max_length=512, null=True, blank=True)
    mail_from = models.EmailField('发件人', null=True, blank=True)
    path = models.FilePathField('原始文件位置', path=gen_email_path, match=r'.*\.eml', recursive=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='用户', on_delete=models.CASCADE)

    send_time = models.DateTimeField('原始发送时间', default=now)
    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.subject

    class Meta:
        ordering = ['-created_time']
        verbose_name = '邮件'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return resolve_url('email:detail', pk=self.pk)

    def get_origin_file(self):
        return resolve_url('email:download', pk=self.pk)

    def get_path(self) -> Path:
        return Path(settings.MEDIA_ROOT) / self.path


@receiver(post_delete, sender=Envelope)
def auto_delete_mail_files(sender, instance, using, **kwargs):
    try:
        if instance.path:
            path = instance.get_path()
            if path.exists():
                path.unlink()
    except Exception as e:
        pass
