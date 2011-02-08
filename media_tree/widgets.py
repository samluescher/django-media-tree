from media_tree import app_settings
from django.contrib.admin.widgets import AdminFileWidget
from media_tree.media_backends import get_media_backend, ThumbnailError
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.utils.html import escape
from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
import os

THUMBNAIL_EXTENSIONS = app_settings.get('MEDIA_TREE_THUMBNAIL_EXTENSIONS')


class FileNodeForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    # TODO: Bug: When popup is dismissed, label for value is currently not replaced with new label (although value is)

    input_type = 'hidden'

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            preview = render_to_string('html/media_tree/filenode/includes/preview.html', {'node': obj})
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
        if value and hasattr(value, "url"):
            try:
                thumb_extension = os.path.splitext(value.name)[1].lstrip('.').lower()
                if not thumb_extension in THUMBNAIL_EXTENSIONS:
                    thumb_extension = None
                thumb = get_media_backend().get_thumbnail(value, {'size': (300, 300), 'sharpen': True})
                thumb_html = u'<img src="%s" alt="%s" />' % (thumb.url, os.path.basename(value.name)) 
                output = u'<div><p><span class="thumbnail"><a href="%s">%s</a></span></p><p>%s</p></div>' % (value.url, thumb_html, output)
            except ThumbnailError as inst:
                pass
        return mark_safe(output)
