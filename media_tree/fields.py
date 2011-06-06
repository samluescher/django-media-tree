from media_tree import app_settings
from media_tree.models import FileNode
from media_tree.widgets import FileNodeForeignKeyRawIdWidget
from mptt.forms import TreeNodeChoiceField
from django.forms.widgets import Select
from django.db import models
from django import forms
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
from django.conf import settings

LEVEL_INDICATOR = app_settings.get('MEDIA_TREE_LEVEL_INDICATOR')


class FileNodeChoiceField(TreeNodeChoiceField):

    # TODO: FileNodeForeignKeyRawIdWidget should only be the standard widget when in admin
    widget = Select
    #widget = ForeignKeyRawIdWidget

    def __init__(self, allowed_node_types=None, allowed_media_types=None, allowed_extensions=None, level_indicator=LEVEL_INDICATOR, rel=None, *args, **kwargs):
        self.allowed_node_types = allowed_node_types
        self.allowed_media_types = allowed_media_types
        self.allowed_extensions = allowed_extensions
        kwargs['level_indicator'] = level_indicator;
        if not kwargs.has_key('widget'):
            # For FileNodeForeignKeyRawIdWidget
            #kwargs['widget'] = self.widget(rel) 
            kwargs['widget'] = self.widget
        super(FileNodeChoiceField, self).__init__(*args, **kwargs)
        # TODO there should nonetheless be an "empty item", also if not required
        if not self.required:
            self.empty_label = FileNode.get_top_node().name
        else:
            self.empty_label = '---------'

    def clean(self, value):
        result = super(FileNodeChoiceField, self).clean(value)
        errors = []
        if result != None:
            if self.allowed_node_types != None and not result.node_type in self.allowed_node_types:
                if len(self.allowed_node_types) == 1 and FileNode.FILE in self.allowed_node_types:
                    errors.append(_('Please select a file.'))
                elif len(self.allowed_node_types) == 1 and FileNode.FOLDER in self.allowed_node_types:
                    errors.append(_('Please select a folder.'))
                else:
                    errors.append(_('You cannot select this node type.'))
            if self.allowed_media_types != None and not result.media_type in self.allowed_media_types:
                if len(self.allowed_media_types) == 1:
                    label = app_settings.get('MEDIA_TREE_CONTENT_TYPES')[self.allowed_media_types[0]]
                    errors.append(_('The required media type is %s.') % label)
                else: 
                    errors.append(_('You cannot select this media type.'))
            if self.allowed_extensions != None and not result.extension in self.allowed_extensions:
                if len(self.allowed_extensions) == 1:
                    errors.append(_('The required file type is %s.') % self.allowed_extensions[0])
                else: 
                    errors.append(_('You cannot select this file type.'))
            if len(errors) > 0:
                raise forms.ValidationError(errors)
        return result

    def label_from_instance(self, obj):
        """
        Creates labels which represent the tree level of each node when
        generating option labels.
        """
        return u'%s %s' % (self.level_indicator * (getattr(obj, obj._meta.level_attr) + (1 if not self.required else 0)), smart_unicode(obj))


class FileNodeForeignKey(models.ForeignKey):

    def __init__(self, allowed_node_types=None, allowed_media_types=None, allowed_extensions=None, level_indicator=LEVEL_INDICATOR, *args, **kwargs):
        self.allowed_node_types = allowed_node_types
        self.allowed_media_types = allowed_media_types
        self.allowed_extensions = allowed_extensions
        self.level_indicator = level_indicator
        super(FileNodeForeignKey, self).__init__(FileNode, *args, **kwargs)
    
    def formfield(self, **kwargs):
        defaults = {
            'form_class': FileNodeChoiceField,
            'rel': self.rel,
            'allowed_node_types': self.allowed_node_types,
            'allowed_media_types': self.allowed_media_types,
            'allowed_extensions': self.allowed_extensions,
            'empty_label': '',
        }
        defaults.update(kwargs)
        return super(FileNodeForeignKey, self).formfield(**defaults)
