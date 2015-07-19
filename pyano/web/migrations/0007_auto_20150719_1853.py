# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_auto_20150719_1845'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pyanoroll',
            name='roleimage',
            field=models.ImageField(upload_to=b'/home/limlug/pyano/media'),
        ),
    ]
