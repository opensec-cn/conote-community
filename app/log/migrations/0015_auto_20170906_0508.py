# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-09-05 21:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('log', '0014_auto_20170906_0437'),
    ]

    operations = [
        migrations.RenameField(
            model_name='dnslog',
            old_name='type',
            new_name='dns_type',
        ),
    ]
