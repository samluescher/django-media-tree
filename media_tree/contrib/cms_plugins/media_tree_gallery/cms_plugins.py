from media_tree.contrib.cms_plugins.media_tree_gallery.models import MediaTreeGallery, MediaTreeGalleryItem
from media_tree.contrib.cms_plugins.media_tree_slideshow.cms_plugins import MediaTreeSlideshowPlugin
from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListing
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormBase
from media_tree.models import FileNode
from media_tree import media_types
from media_tree.utils.filenode import get_nested_filenode_list
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin
from django.http import Http404


class MediaTreeGalleryPluginForm(MediaTreePluginFormBase):
    class Meta:
        model = MediaTreeGallery


class MediaTreeGalleryItemInline(admin.StackedInline):
    model = MediaTreeGalleryItem
    extra = 1


# TODO The default output/template does not make much sense. Include: Previews, folder thumbnails, collapsible tree etc.
class MediaTreeGalleryPlugin(MediaTreeSlideshowPlugin):

    inlines = [MediaTreeGalleryItemInline]

    class PluginMedia:
        js = [
            'lib/jquery.cycle/jquery.cycle.all.min.js',
        ]

    module = _('Media Tree')
    model = MediaTreeGallery
    form = MediaTreeGalleryPluginForm
    fieldsets = [
        (_('Settings'), {
            'fields': form().fields.keys(),
            'classes': ['collapse']
        }),
    ]
    name = _('Gallery')
    admin_preview = False
    render_template = 'cms/plugins/mediatreegallery.html'

    def init_nodes(self, context, instance):
        super(MediaTreeGalleryPlugin, self).init_nodes(context, instance)

        if instance.list_type == MediaTreeListing.LIST_NESTED or instance.include_descendants:
            filter = None
            if not instance.include_descendants:
                max_depth = 1
            else:
                max_depth = None

            self.folder_list = get_nested_filenode_list(self.selected_nodes, filter_media_types=(FileNode.FOLDER,), filter=filter,
                max_depth=max_depth, processors=[self.FolderLink])
        else:
            self.folder_list = ()

        # fetch and validate parent folder:
        if instance.list_type == MediaTreeListing.LIST_NESTED:
            folder_id = context['request'].GET.get(self.FolderLink.folder_param_name(instance), None)
            if folder_id:
                try:
                    self.current_folder = FileNode.objects.get(pk=folder_id)
                    top_node_pks = [node.pk for node in self.selected_nodes]
                    if not self.current_folder.pk in top_node_pks:
                        if not instance.include_descendants or self.current_folder.get_ancestors().filter(pk__in=top_node_pks).count() == 0:
                            raise FileNode.DoesNotExist()
                except FileNode.DoesNotExist:
                    raise Http404()
                self.visible_nodes = self.current_folder.get_children()

    def render(self, context, instance, placeholder):
        if instance.list_type == MediaTreeListing.LIST_NESTED:
            self.list_max_depth = 1
        context = super(MediaTreeGalleryPlugin, self).render(context, instance, placeholder)
        self.FolderLink.plugin_instance = instance
        self.FolderLink.filter_media_types = self.list_filter_media_types
        self.FolderLink.current_folder = self.current_folder
        # counting folders as items may be confusing to user, hence disabled.
        #if instance.include_descendants:
            #self.FolderLink.filter_media_types += (FileNode.FOLDER,)

        context.update({
            'auto_play': instance.auto_play,
            'folders': self.folder_list
        });

        return context


plugin_pool.register_plugin(MediaTreeGalleryPlugin)
