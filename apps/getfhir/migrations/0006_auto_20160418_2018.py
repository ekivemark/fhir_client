# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-18 20:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('getfhir', '0005_session_state_expires'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session_state',
            name='expires',
            field=models.DateTimeField(null=True),
        ),
    ]