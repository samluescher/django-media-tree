# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media_tree', '0002_mptt_to_treebeard'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filenode',
            name='depth',
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='filenode',
            name='lft',
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='filenode',
            name='rgt',
            field=models.PositiveIntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='filenode',
            name='tree_id',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
