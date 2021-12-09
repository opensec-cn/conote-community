import uuid
from pathlib import Path

from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
from conote.const import SANDBIX_CHOICE


User = get_user_model()


class CodeBox(models.Model):
    id = models.UUIDField('ID', default=uuid.uuid4, editable=False, primary_key=True)
    title = models.CharField('标题', max_length=256)
    code = models.TextField('代码')
    type = models.CharField('类型', max_length=32, choices=SANDBIX_CHOICE, default='php-5.6')

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='用户',
        on_delete=models.CASCADE
    )

    created_time = models.DateTimeField('创建时间', auto_now_add=True)
    last_modify_time = models.DateTimeField('修改时间', auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_time']
        verbose_name = '代码盒子'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return '{}://{}.{}/{}.php'.format(
            settings.O_SERVER_SCHEME,
            self.user.domain,
            settings.O_SERVER_DOMAIN,
            str(self.pk)
        )

    def delete(self, using=None, keep_parents=False):
        filename = Path(settings.SANDBOX_ROOT) / str(self.user_id) / (str(self.id) + '.php')
        if filename.exists():
            filename.unlink()

        return super().delete(using, keep_parents)
