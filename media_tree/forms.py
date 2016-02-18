from media_tree import settings as app_settings
from django import forms
from django.forms import ModelChoiceField
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_unicode

LEVEL_INDICATOR = app_settings.MEDIA_TREE_LEVEL_INDICATOR


class FileNodeChoiceField(ModelChoiceField):
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
        self.level_indicator = level_indicator
        super(FileNodeChoiceField, self).__init__(*args, **kwargs)

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
        return u'%s %s %i' % (self.level_indicator * (getattr(obj, 'depth') - 1), smart_unicode(obj), obj.depth)
