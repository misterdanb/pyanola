# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='pyanoroll',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('titel_text', models.CharField(max_length=200)),
                ('composer_text', models.CharField(max_length=200)),
                ('roletype_text', models.CharField(max_length=200)),
                ('producer_text', models.CharField(max_length=200)),
                ('playspeed', models.IntegerField()),
                ('roleimage', models.CharField(max_length=200)),
            ],
        ),
    ]
