# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0007_auto_20150719_1853'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pyanoroll',
            name='roleimage',
            field=models.ImageField(upload_to=b''),
        ),
    ]
