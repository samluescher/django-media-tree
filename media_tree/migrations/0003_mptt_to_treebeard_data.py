# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def increment_depth(apps, schema_editor):
    FileNode = apps.get_model("media_tree", "FileNode")
    for node in FileNode.objects.all():
        # Treebeard root nodes have a depth of 1
        node.depth += 1
        node.save()

def decrement_depth(apps, schema_editor):
    FileNode = apps.get_model("media_tree", "FileNode")
    for node in FileNode.objects.all():
        # MPTT root nodes have a depth of 0
        node.depth -= 1
        node.save()


class Migration(migrations.Migration):

    dependencies = [
        ('media_tree', '0002_mptt_to_treebeard'),
    ]

    operations = [
        migrations.RunPython(increment_depth, decrement_depth),
    ]
