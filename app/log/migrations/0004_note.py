# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-29 19:25
from __future__ import unicode_literals

import app.log.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('log', '0003_auto_20170828_0139'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=256, verbose_name='文件名')),
                ('attachment', models.FileField(blank=True, null=True, upload_to=app.log.models.generate_attachment_filename, verbose_name='附件')),
                ('content_type', models.CharField(default='application/octet-stream', max_length=128, verbose_name='Content Type')),
                ('content', models.TextField(blank=True, null=True, verbose_name='文件内容')),
                ('created_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('last_modify_time', models.DateTimeField(auto_now=True, verbose_name='修改时间')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name_plural': '笔记',
                'verbose_name': '笔记',
                'ordering': ['-created_time'],
            },
        ),
    ]
