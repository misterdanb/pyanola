# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0009_auto_20150719_1905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pyanoroll',
            name='roleimage',
            field=models.ImageField(upload_to=b'/media/'),
        ),
    ]
