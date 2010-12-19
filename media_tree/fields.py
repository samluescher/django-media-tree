from django.db import models
from django import forms
from media_tree.models import FileNode
from mptt.forms import TreeNodeChoiceField
from django.utils.translation import ugettext as _
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.encoding import smart_unicode
from media_tree import app_settings
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django import template
import os

THUMBNAIL_EXTENSIONS = app_settings.get('MEDIA_TREE_THUMBNAIL_EXTENSIONS')

class AdminThumbWidget(forms.FileInput):
    """
    A Image FileField Widget that shows a thumbnail if it has one.
    """
    def __init__(self, attrs={}):
        super(AdminThumbWidget, self).__init__(attrs)
 
    def render(self, name, value, attrs=None):
        output = []
        if value and hasattr(value, "url"):
            try:
                thumb_extension = os.path.splitext(value.name)[1].lstrip('.').lower()
                if not thumb_extension in THUMBNAIL_EXTENSIONS:
                    thumb_extension = None
                from sorl.thumbnail.main import DjangoThumbnail
                thumb = '<img src="%s" alt="%s" />' % (DjangoThumbnail(value.name, (300, 300), ['sharpen'], extension=thumb_extension).absolute_url, os.path.basename(value.name)) 
            except:
                # just act like a normal file
                output.append('<p><a target="_blank" href="%s">%s</a></p><label>%s</label> ' %
                    (value.url, os.path.basename(value.path), _('Change:')))
            else:
                output.append('<p class="thumbnail"><a target="_blank" href="%s">%s</a></p><p><a target="_blank" href="%s">%s</a></p><label>%s</label> ' %
                    (value.url, thumb, value.url, os.path.basename(value.path), _('Change:')))

        output.append(super(AdminThumbWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))


LEVEL_INDICATOR = app_settings.get('MEDIA_TREE_LEVEL_INDICATOR')

# TODO this is not implemented and doesn't really work. Requirements: Being able to select one node in change list (according to allowed_node_types and allowed_media_types). Also, multiple choice would be nice.
class FileNodePopupWidget(ForeignKeyRawIdWidget):
    input_type = 'hidden'

    """
    choices = None
    input_type = 'hidden'
    is_hidden = True
    def render(self, name, value, attrs=None):
        obj = self.obj_for_value(value)
        css_id = attrs.get('id', 'id_image_x')
        css_id_thumbnail_img = "%s_thumbnail_img" % css_id
        css_id_description_txt = "%s_description_txt" % css_id
        if attrs is None:
            attrs = {}
        related_url = reverse('admin:image_filer-directory_listing-root')
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField' # The JavaScript looks for this hook.
        output = []
        if obj:
            try:
                output.append(u'<img id="%s" src="%s" alt="%s" /> ' % (css_id_thumbnail_img, obj.thumbnails['admin_tiny_icon'], obj.label) )
            except ThumbnailException:
                pass
            output.append(u'&nbsp;<strong id="%s">%s</strong>' % (css_id_description_txt, obj) )
        else:
            output.append(u'<img id="%s" src="" class="quiet" alt="no image selected">' % css_id_thumbnail_img)
            output.append(u'&nbsp;<strong id="%s">%s</strong>' % (css_id_description_txt, '') )
        # TODO: "id_" is hard-coded here. This should instead use the correct
        # API to determine the ID dynamically.
        output.append('<a href="%s%s" class="related-lookup" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);"> ' % \
            (related_url, url, name))
        output.append('<img src="%simg/admin/selector-search.gif" width="16" height="16" alt="%s" /></a>' % (settings.ADMIN_MEDIA_PREFIX, _('Lookup')))
        output.append('</br>')
        super_attrs = attrs.copy()
        output.append( super(ForeignKeyRawIdWidget, self).render(name, value, super_attrs) )
        return mark_safe(u''.join(output))
    def label_for_value(self, value):
        obj = self.obj_for_value(value)
        return '&nbsp;<strong>%s</strong>' % truncate_words(obj, 14)
    def obj_for_value(self, value):
        try:
            key = self.rel.get_related_field().name
            obj = self.rel.to._default_manager.get(**{key: value})
        except:
            obj = None
        return obj
    
    class Media:
        js = (context_processors.media(None)['IMAGE_FILER_MEDIA_URL']+'js/image_widget_thumbnail.js',
              context_processors.media(None)['IMAGE_FILER_MEDIA_URL']+'js/popup_handling.js',)
    """

class FileNodeWidget(forms.Select):
    pass

class FileNodeChoiceField(TreeNodeChoiceField):

    widget = FileNodeWidget

    def __init__(self, allowed_node_types=None, allowed_media_types=None, allowed_extensions=None, level_indicator=LEVEL_INDICATOR, *args, **kwargs):
        self.allowed_node_types = allowed_node_types
        self.allowed_media_types = allowed_media_types
        self.allowed_extensions = allowed_extensions
        kwargs['level_indicator'] = level_indicator;
        if not kwargs.has_key('widget'):
            kwargs['widget'] = self.widget()
        super(FileNodeChoiceField, self).__init__(*args, **kwargs)
        # TODO there should nonetheless be an "empty item", also if not required
        if not self.required:
            self.empty_label = FileNode.get_root_node().name
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

class FileNodeChoicePopupField(FileNodeChoiceField):
    widget = FileNodePopupWidget
    def __init__(self, rel, *args, **kwargs):
        kwargs['widget'] = self.widget(rel)
        super(FileNodeChoicePopupField, self).__init__(*args, **kwargs)

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
            'allowed_node_types': self.allowed_node_types,
            'allowed_media_types': self.allowed_media_types,
            'allowed_extensions': self.allowed_extensions,
            'empty_label': '',
        }
        defaults.update(kwargs)
        return super(FileNodeForeignKey, self).formfield(**defaults)

class FileNodePopupForeignKey(FileNodeForeignKey):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': FileNodeChoicePopupField,
            'rel': self.rel,
        }
        defaults.update(kwargs)
        return super(FileNodePopupForeignKey, self).formfield(**defaults)
