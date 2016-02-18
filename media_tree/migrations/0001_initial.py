# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import media_tree.models
import django.core.files.storage


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FileNode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(storage=django.core.files.storage.FileSystemStorage(), upload_to=b'upload', null=True, verbose_name='file')),
                ('preview_file', models.ImageField(storage=django.core.files.storage.FileSystemStorage(), upload_to=b'upload/_preview', blank=True, help_text='Use this field to upload a preview image for video or similar media types.', null=True, verbose_name='preview')),
                ('node_type', models.IntegerField(verbose_name='node type', editable=False, choices=[(100, b'Folder'), (200, b'File')])),
                ('media_type', models.IntegerField(blank=True, verbose_name='media type', null=True, editable=False, choices=[(100, 'folder'), (210, 'archive'), (220, 'audio'), (230, 'document'), (240, 'image'), (241, 'web image'), (242, 'vector image'), (250, 'text'), (260, 'video'), (200, 'other')])),
                ('allowed_child_node_types', media_tree.models.MultipleChoiceCommaSeparatedIntegerField(choices=[(200, 'file'), (100, 'folder')], max_length=64, blank=True, help_text='If none selected, all are allowed.', null=True, verbose_name='allowed ')),
                ('published', models.BooleanField(default=True, verbose_name='is published')),
                ('mimetype', models.CharField(verbose_name='mimetype', max_length=64, null=True, editable=False)),
                ('name', models.CharField(max_length=255, null=True, verbose_name='name')),
                ('title', models.CharField(default=b'', max_length=255, null=True, verbose_name='title', blank=True)),
                ('description', models.TextField(default=b'', null=True, verbose_name='description', blank=True)),
                ('author', models.CharField(default=b'', max_length=255, null=True, verbose_name='author', blank=True)),
                ('publish_author', models.BooleanField(default=False, verbose_name='publish author')),
                ('copyright', models.CharField(default=b'', max_length=255, null=True, verbose_name='copyright', blank=True)),
                ('publish_copyright', models.BooleanField(default=False, verbose_name='publish copyright')),
                ('date_time', models.DateTimeField(null=True, verbose_name='date/time', blank=True)),
                ('publish_date_time', models.BooleanField(default=False, verbose_name='publish date/time')),
                ('keywords', models.CharField(max_length=255, null=True, verbose_name='keywords', blank=True)),
                ('override_alt', models.CharField(default=b'', max_length=255, blank=True, help_text='If you leave this blank, the alternative text will be compiled automatically from the available metadata.', null=True, verbose_name='alternative text')),
                ('override_caption', models.CharField(default=b'', max_length=255, blank=True, help_text='If you leave this blank, the caption will be compiled automatically from the available metadata.', null=True, verbose_name='caption')),
                ('has_metadata', models.BooleanField(default=False, verbose_name='metadata entered', editable=False)),
                ('extension', models.CharField(default=b'', max_length=10, null=True, editable=False, verbose_name='type')),
                ('size', models.IntegerField(verbose_name='size', null=True, editable=False)),
                ('width', models.IntegerField(help_text='Detected automatically for supported images', null=True, verbose_name='width', blank=True)),
                ('height', models.IntegerField(help_text='Detected automatically for supported images', null=True, verbose_name='height', blank=True)),
                ('slug', models.CharField(verbose_name='slug', max_length=255, null=True, editable=False)),
                ('is_default', models.BooleanField(default=False, help_text='The default object of a folder can be used for folder previews etc.', verbose_name='use as default object for folder')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('position', models.IntegerField(default=0, verbose_name='position', blank=True)),
                ('extra_metadata', models.TextField(verbose_name='extra metadata', editable=None)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('created_by', models.ForeignKey(related_name=b'created_by', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='created by')),
                ('modified_by', models.ForeignKey(related_name=b'modified_by', blank=True, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='modified by')),
                ('parent', models.ForeignKey(related_name=b'children', verbose_name='folder', blank=True, to='media_tree.FileNode', null=True)),
            ],
            options={
                'ordering': ['tree_id', 'lft'],
                'verbose_name': 'media object',
                'verbose_name_plural': 'media objects',
                'permissions': (('manage_filenode', 'Can perform management tasks'),),
            },
            bases=(models.Model,),
        ),
    ]
