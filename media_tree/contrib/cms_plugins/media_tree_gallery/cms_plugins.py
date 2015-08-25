from media_tree.contrib.cms_plugins.media_tree_gallery.models import MediaTreeGallery, MediaTreeGalleryItem
from media_tree.contrib.cms_plugins.media_tree_slideshow.cms_plugins import MediaTreeSlideshowPlugin
from media_tree.contrib.views.listing import FileNodeListingMixin
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormInlinePositioningBase
from media_tree.models import FileNode
from media_tree import media_types
from media_tree.utils.filenode import get_nested_filenode_list
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.http import Http404


class MediaTreeGalleryPluginForm(MediaTreePluginFormInlinePositioningBase):
    class Meta:
        model = MediaTreeGallery
        fields = '__all__'


class MediaTreeGalleryItemInline(admin.StackedInline):
    model = MediaTreeGalleryItem
    extra = 0


# TODO The default output/template does not make much sense. Include: Previews, folder thumbnails, collapsible tree etc.
class MediaTreeGalleryPlugin(MediaTreeSlideshowPlugin, FileNodeListingMixin):
    model = MediaTreeGallery
    module = _('Media Tree')
    name = _('Gallery')
    admin_preview = False
    form = MediaTreeGalleryPluginForm
    fieldsets = [
        (_('Settings'), {
            'fields': form().fields.keys(),
            'classes': ['collapse']
        }),
    ]
    inlines = [MediaTreeGalleryItemInline]
    render_template = 'cms/plugins/media_tree_gallery.html'

    class PluginMedia:
        js = [
            'lib/jquery.cycle/jquery.cycle.all.min.js',
        ]

    filter_by_parent_folder = True
    list_filter_media_types = (media_types.SUPPORTED_IMAGE,)

    def render(self, context, instance, placeholder):
        context = super(MediaTreeGalleryPlugin, self).render(context, instance, placeholder)
        context.update({
            'auto_play': instance.auto_play,
        });

        return context


plugin_pool.register_plugin(MediaTreeGalleryPlugin)
