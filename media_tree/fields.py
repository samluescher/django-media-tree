from media_tree import settings as app_settings, media_types
from media_tree.models import FileNode
from media_tree.widgets import FileNodeForeignKeyRawIdWidget
from mptt.forms import TreeNodeChoiceField
from django.forms.widgets import Select
from django.db import models
from django import forms
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode
from django.conf import settings

LEVEL_INDICATOR = app_settings.MEDIA_TREE_LEVEL_INDICATOR


class FileNodeChoiceField(TreeNodeChoiceField):
    """
    A form field for selecting a ``FileNode`` object.

    Its constructor takes the following arguments that are relevant when selecting ``FileNode`` objects: 

    :param allowed_node_types: A list of node types that are allowed and will validate, e.g. ``(FileNode.FILE,)`` if the user should only be able to select files, but not folders
    :param allowed_media_types: A list of media types that are allowed and will validate, e.g. ``(media_types.DOCUMENT,)``
    :param allowed_extensions: A list of file extensions that are allowed and will validate, e.g. ``("jpg", "jpeg")``

    Since this class is a subclass of ``ModelChoiceField``, you can also pass it that class' 
    parameters, such as ``queryset`` if you would like to restrict the objects that will
    be available for selection.
    """

    def __init__(self, allowed_node_types=None, allowed_media_types=None, allowed_extensions=None, level_indicator=LEVEL_INDICATOR, rel=None, *args, **kwargs):
        self.allowed_node_types = allowed_node_types
        self.allowed_media_types = allowed_media_types
        self.allowed_extensions = allowed_extensions
        kwargs['level_indicator'] = level_indicator;
        if not kwargs.has_key('widget'):
            kwargs['widget'] = self.widget

            # TODO: FileNodeForeignKeyRawIdWidget should only be the standard widget when in admin
            # TODO: It currently does not work with move/copy form
            #kwargs['widget'] = FileNodeForeignKeyRawIdWidget(rel)

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
            if self.allowed_node_types and not result.node_type in self.allowed_node_types:
                if len(self.allowed_node_types) == 1 and FileNode.FILE in self.allowed_node_types:
                    errors.append(_('Please select a file.'))
                elif len(self.allowed_node_types) == 1 and FileNode.FOLDER in self.allowed_node_types:
                    errors.append(_('Please select a folder.'))
                else:
                    errors.append(_('You cannot select this node type.'))
            if self.allowed_media_types and not result.media_type in self.allowed_media_types:
                if len(self.allowed_media_types) == 1:
                    label = app_settings.MEDIA_TREE_CONTENT_TYPES[self.allowed_media_types[0]]
                    errors.append(_('The required media type is %s.') % label)
                else:
                    errors.append(_('You cannot select this media type.'))
            if self.allowed_extensions and not result.extension in self.allowed_extensions:
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
        return u'%s %s' % (self.level_indicator * (getattr(obj, obj._mptt_meta.level_attr) + (1 if not self.required else 0)), smart_unicode(obj))


class FileNodeForeignKey(models.ForeignKey):
    """
    A model field for selecting a ``FileNode`` object.

    Its constructor takes the following arguments that are relevant when selecting ``FileNode`` objects: 

    :param allowed_node_types: A list of node types that are allowed and will validate, e.g. ``(FileNode.FILE,)`` if the user should only be able to select files, but not folders
    :param allowed_media_types: A list of media types that are allowed and will validate, e.g. ``(media_types.DOCUMENT,)``
    :param allowed_extensions: A list of file extensions that are allowed and will validate, e.g. ``("jpg", "jpeg")``

    Since this class is a subclass of ``models.ForeignKey``, you can also pass it that class' 
    parameters, such as ``limit_choices_to`` if you would like to restrict the objects that will
    be available for selection.
    """

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


class ImageFileNodeForeignKey(FileNodeForeignKey):
    """
    A model field for selecting a ``FileNode`` object associated to a supported image format.

    Using this field will ensure that only folders and image files will be visible in the widget, 
    and will require the user to select an image node. 
    """
    def __init__(self, allowed_node_types=None, allowed_media_types=None, allowed_extensions=None, level_indicator=LEVEL_INDICATOR, *args, **kwargs):
        self.allowed_node_types = allowed_node_types
        if not allowed_media_types:
            allowed_media_types = (media_types.SUPPORTED_IMAGE,)
        kwargs['limit_choices_to'] = {'media_type__in': (FileNode.FOLDER, media_types.SUPPORTED_IMAGE)}
        
        super(ImageFileNodeForeignKey, self).__init__(allowed_node_types, allowed_media_types, allowed_extensions, level_indicator, *args, **kwargs)


class DimensionField(models.CharField):
    """
    CharField for specifying image dimensions, i.e. width or height. Currently,
    this needs to be an integer > 0, but since it is a CharField, it might also
    contain units such as "px" or "%" in the future.
    """
    def __init__(self, verbose_name=None, name=None, **kwargs):
        if not 'max_length' in kwargs:
            kwargs['max_length'] = 8
        super(DimensionField, self).__init__(verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'regex': '^[1-9][0-9]*$',
                    'form_class': forms.RegexField}
        defaults.update(kwargs)
        return models.Field.formfield(self, **defaults)
