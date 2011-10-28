from media_tree.contrib.cms_plugins.media_tree_gallery.models import MediaTreeGallery, MediaTreeGalleryItem
from media_tree.contrib.cms_plugins.media_tree_slideshow.cms_plugins import MediaTreeSlideshowPlugin
from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListing
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormBase
from media_tree.models import FileNode
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


class MediaTreeGalleryPluginForm(MediaTreePluginFormBase):
    class Meta:
        model = MediaTreeGallery


class MediaTreeGalleryItemInline(admin.StackedInline):
    model = MediaTreeGalleryItem
    extra = 1


# TODO count_descendants ONLY of same type
class MediaTreeGalleryPlugin(MediaTreeSlideshowPlugin):

    inlines = [MediaTreeGalleryItemInline]

    class PluginMedia:
        js = [
            'lib/jquery.cycle/jquery.cycle.all.js',
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

    def render(self, context, instance, placeholder):
        if instance.list_type == MediaTreeListing.LIST_NESTED:
            self.list_max_depth = 0
        context = super(MediaTreeGalleryPlugin, self).render(context, instance, placeholder)
        self.FolderLink.plugin_instance = instance
        self.FolderLink.filter_media_types = self.list_filter_media_types
        self.FolderLink.current_folder = self.current_folder
        if instance.include_descendants:
            self.FolderLink.filter_media_types += (FileNode.FOLDER,)

        context.update({
            'auto_play': instance.auto_play,
        })

        # Folder nav
        # TODO: Think of better-performing solution, using template tags
        # TODO: Selecting preview image for gallery items (or for folder?)
        if instance.list_type == MediaTreeListing.LIST_NESTED and (instance.include_descendants or not self.single_folder_selected):
            if instance.include_descendants:
                max_depth = None
            else:
                max_depth = 0
            if not self.single_folder_selected:
                top_nodes = self.selected_nodes
            else:
                top_nodes = self.selected_nodes[0].get_children()
            from django.db.models import Q

            # Only expand current selected branch
            if self.current_folder:
                ancestors = []
                for ancestor in self.current_folder.get_ancestors(ascending=True):
                    ancestors.append(ancestor)
                    if ancestor in self.selected_nodes:
                        break;
                ancestors.append(self.current_folder)
                filter = Q(parent__in=ancestors)
            else:
                filter = None
                max_depth = 1

            folders = FileNode.get_nested_list(top_nodes, filter_media_types=(FileNode.FOLDER,), filter=filter,
                max_depth=max_depth, processors=[self.FolderLink])
            if not self.single_folder_selected and self.current_folder and self.files_selected:
                folders = [self.FolderLink({'name': 'Back to top', 'pk': None}, count_descendants=False).__unicode__(),
                    folders]
            context.update({'folders': folders})

        return context


plugin_pool.register_plugin(MediaTreeGalleryPlugin)
