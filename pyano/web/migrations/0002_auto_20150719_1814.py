# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pyanoroll',
            name='roleimage',
            field=models.ImageField(upload_to=b'pyanoroll'),
        ),
    ]
