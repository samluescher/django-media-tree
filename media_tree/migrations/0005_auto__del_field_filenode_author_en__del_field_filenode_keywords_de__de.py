# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'FileNode.author_en'
        db.delete_column('media_tree_filenode', 'author_en')

        # Deleting field 'FileNode.keywords_de'
        db.delete_column('media_tree_filenode', 'keywords_de')

        # Deleting field 'FileNode.description_de'
        db.delete_column('media_tree_filenode', 'description_de')

        # Deleting field 'FileNode.override_caption_en'
        db.delete_column('media_tree_filenode', 'override_caption_en')

        # Deleting field 'FileNode.description_en'
        db.delete_column('media_tree_filenode', 'description_en')

        # Deleting field 'FileNode.copyright_en'
        db.delete_column('media_tree_filenode', 'copyright_en')

        # Deleting field 'FileNode.author_de'
        db.delete_column('media_tree_filenode', 'author_de')

        # Deleting field 'FileNode.keywords_en'
        db.delete_column('media_tree_filenode', 'keywords_en')

        # Deleting field 'FileNode.override_caption_de'
        db.delete_column('media_tree_filenode', 'override_caption_de')

        # Deleting field 'FileNode.override_alt_de'
        db.delete_column('media_tree_filenode', 'override_alt_de')

        # Deleting field 'FileNode.title_de'
        db.delete_column('media_tree_filenode', 'title_de')

        # Deleting field 'FileNode.copyright_de'
        db.delete_column('media_tree_filenode', 'copyright_de')

        # Deleting field 'FileNode.override_alt_en'
        db.delete_column('media_tree_filenode', 'override_alt_en')

        # Deleting field 'FileNode.title_en'
        db.delete_column('media_tree_filenode', 'title_en')

        # Deleting field 'FileNode.focal_y'
        db.delete_column('media_tree_filenode', 'focal_y')

        # Deleting field 'FileNode.focal_x'
        db.delete_column('media_tree_filenode', 'focal_x')

        # Adding field 'FileNode.site'
        db.add_column('media_tree_filenode', 'site',
                      self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='file', null=True, to=orm['sites.Site']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'FileNode.author_en'
        db.add_column('media_tree_filenode', 'author_en',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.keywords_de'
        db.add_column('media_tree_filenode', 'keywords_de',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.description_de'
        db.add_column('media_tree_filenode', 'description_de',
                      self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.override_caption_en'
        db.add_column('media_tree_filenode', 'override_caption_en',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.description_en'
        db.add_column('media_tree_filenode', 'description_en',
                      self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.copyright_en'
        db.add_column('media_tree_filenode', 'copyright_en',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.author_de'
        db.add_column('media_tree_filenode', 'author_de',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.keywords_en'
        db.add_column('media_tree_filenode', 'keywords_en',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.override_caption_de'
        db.add_column('media_tree_filenode', 'override_caption_de',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.override_alt_de'
        db.add_column('media_tree_filenode', 'override_alt_de',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.title_de'
        db.add_column('media_tree_filenode', 'title_de',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.copyright_de'
        db.add_column('media_tree_filenode', 'copyright_de',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.override_alt_en'
        db.add_column('media_tree_filenode', 'override_alt_en',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.title_en'
        db.add_column('media_tree_filenode', 'title_en',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, null=True, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.focal_y'
        db.add_column('media_tree_filenode', 'focal_y',
                      self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=3, blank=True),
                      keep_default=False)

        # Adding field 'FileNode.focal_x'
        db.add_column('media_tree_filenode', 'focal_x',
                      self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=3, blank=True),
                      keep_default=False)

        # Deleting field 'FileNode.site'
        db.delete_column('media_tree_filenode', 'site_id')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'media_tree.filenode': {
            'Meta': {'ordering': "['tree_id', 'lft']", 'object_name': 'FileNode'},
            'author': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'copyright': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'date_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'extension': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '10', 'null': 'True'}),
            'extra_metadata': ('django.db.models.fields.TextField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'has_metadata': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'height': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'media_type': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mimetype': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modified_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'modified_by'", 'null': 'True', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'node_type': ('django.db.models.fields.IntegerField', [], {}),
            'override_alt': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'override_caption': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['media_tree.FileNode']"}),
            'position': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'preview_file': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'publish_author': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'publish_copyright': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'publish_date_time': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'site': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'file'", 'null': 'True', 'to': "orm['sites.Site']"}),
            'size': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'width': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'sites.site': {
            'Meta': {'ordering': "('domain',)", 'object_name': 'Site', 'db_table': "'django_site'"},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        }
    }

    complete_apps = ['media_tree']