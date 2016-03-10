import os
import django
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.admin.templatetags.admin_static import static
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.html import escape
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from media_tree import settings as app_settings
from media_tree import media_types
from media_tree.media_backends import get_media_backend, ThumbnailError

THUMBNAIL_EXTENSIONS = app_settings.MEDIA_TREE_THUMBNAIL_EXTENSIONS
THUMBNAIL_SIZE = app_settings.MEDIA_TREE_THUMBNAIL_SIZES['large']
STATIC_SUBDIR = app_settings.MEDIA_TREE_STATIC_SUBDIR


class FileNodeForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    class Media:
        js = (
            os.path.join(STATIC_SUBDIR, 'js', 'filenode_foreignkeywidget.js').replace("\\","/"),
        )
        css = {
            'all': (
                os.path.join(STATIC_SUBDIR, 'css', 'filenode_preview.css').replace("\\","/"),
            )
        }

    # the actual input field should be hidden...
    input_type = 'hidden'

    # ...but for the field to show up amongst the form's visible fields, return
    # False here.
    @property
    def is_hidden(self):
        return False

    def render(self, name, value, attrs=None):
        # insert a placeholder for widget preview if value is None so that
        # the dismissRelatedLookupPopup hook in Javascript can populate it.
        output = super(FileNodeForeignKeyRawIdWidget, self).render(name, value, attrs)
        return output
        extra = ''
        if value:
            extra = '<a href="#" class="clear-widget"><img src="%s" width="11" height="11" alt="%s" /></a>' % (
                static('admin/img/icon-deletelink.svg' if django.VERSION >= (1.9) else 'admin/img/icon-deletelink.svg'), _('Clear'))
        return mark_safe('<span class="FileNodeForeignKeyRawIdWidget">%s%s%s</span>' %
            (output, self.label_for_value(None) if not value else '', extra))

    def label_for_value(self, value):
        # instead of just outputting the node's name, render the node (or None)
        # through widget_preview.html, which adds icons and thumbnails depending
        # on your configuration.
        key = self.rel.get_related_field().name
        try:
            if value:
                obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            else:
                obj = None
            preview = render_to_string('admin/media_tree/filenode/includes/widget_preview.html',
                {'node': obj, 'preview_file': obj.get_preview_file() if obj else None})

            return preview
        except (ValueError, self.rel.to.DoesNotExist):
            return ''


class AdminThumbWidget(AdminFileWidget):
    """
    An Image FileField Widget that shows a thumbnail if it has one.
    """
    def __init__(self, attrs={}):
        super(AdminThumbWidget, self).__init__(attrs)

    def get_media_backend(self, media_type):
        return get_media_backend(fail_silently=True, handles_media_types=(
            media_type,))

    def render(self, name, value, attrs=None):
        output = super(AdminThumbWidget, self).render(name, value, attrs)
        thumb = None

        if value and hasattr(value, "url"):
            media_backend = self.get_media_backend(media_types.SUPPORTED_IMAGE)
            if media_backend:
                try:
                    thumb = media_backend.get_thumbnail(value, {'size': THUMBNAIL_SIZE})
                except ThumbnailError:
                    pass
            if not thumb:
                media_backend = self.get_media_backend(media_types.VECTOR_IMAGE)
                if media_backend:
                    try:
                        thumb = media_backend.get_thumbnail(value, {'size': THUMBNAIL_SIZE})
                    except ThumbnailError:
                        pass
            if thumb:
                thumb_html = u'<img src="%s" alt="%s" width="%i" height="%i" />' % (thumb.url, os.path.basename(value.name), thumb.width, thumb.height)
                output = u'<div><p><span class="thumbnail">%s</span></p><p>%s</p></div>' % (thumb_html, output)

        return mark_safe(output)
