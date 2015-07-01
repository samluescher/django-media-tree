# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media_tree', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='filenode',
            options={'verbose_name': 'media object', 'verbose_name_plural': 'media objects', 'permissions': (('manage_filenode', 'Can perform management tasks'),)},
        ),
        migrations.RenameField(
            model_name='filenode',
            old_name='level',
            new_name='depth'
        ),
        migrations.RenameField(
            model_name='filenode',
            old_name='rght',
            new_name='rgt'
        ),
        migrations.RemoveField(
            model_name='filenode',
            name='parent',
        ),
    ]
