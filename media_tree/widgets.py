from media_tree import settings as app_settings
from django.contrib.admin.widgets import AdminFileWidget
from media_tree import media_types
from media_tree.media_backends import get_media_backend, ThumbnailError
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.html import escape
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
import os

THUMBNAIL_EXTENSIONS = app_settings.MEDIA_TREE_THUMBNAIL_EXTENSIONS
THUMBNAIL_SIZE = app_settings.MEDIA_TREE_THUMBNAIL_SIZES['large']


class FileNodeForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    # TODO: Bug: When popup is dismissed, label for value is currently not replaced with new label (although value is)

    input_type = 'hidden'

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            preview = render_to_string('media_tree/filenode/includes/preview.html', 
                {'node': obj, 'preview_file': obj.get_preview_file()})
            return '%s %s' % (preview, super(FileNodeForeignKeyRawIdWidget, self).label_for_value(value))
        except (ValueError, self.rel.to.DoesNotExist):
            return ''


class AdminThumbWidget(AdminFileWidget):
    """
    A Image FileField Widget that shows a thumbnail if it has one.
    """
    def __init__(self, attrs={}):
        super(AdminThumbWidget, self).__init__(attrs)
 
    def render(self, name, value, attrs=None):
        output = super(AdminThumbWidget, self).render(name, value, attrs)
        media_backend = get_media_backend(fail_silently=True, handles_media_types=(
            media_types.SUPPORTED_IMAGE,))
        if media_backend and value and hasattr(value, "url"):
            try:
                thumb_extension = os.path.splitext(value.name)[1].lstrip('.').lower()
                if not thumb_extension in THUMBNAIL_EXTENSIONS:
                    thumb_extension = None
                thumb = media_backend.get_thumbnail(value, {'size': THUMBNAIL_SIZE})
                if thumb:
                    thumb_html = u'<img src="%s" alt="%s" width="%i" height="%i" />' % (thumb.url, os.path.basename(value.name), thumb.width, thumb.height) 
                    output = u'<div><p><span class="thumbnail">%s</span></p><p>%s</p></div>' % (thumb_html, output)
            except ThumbnailError as inst:
                pass
        return mark_safe(output)
