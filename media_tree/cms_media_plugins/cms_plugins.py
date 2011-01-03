from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from media_tree.models import FileNode
from media_tree.cms_media_plugins.helpers import PluginLink, FolderLinkBase
from media_tree.cms_media_plugins.models import MediaTreeImage, MediaTreeList, MediaTreeListItem, MediaTreeSlideshow, MediaTreeSlideshowItem, MediaTreeGallery, MediaTreeGalleryItem
from media_tree import media_types
from django.conf import settings
from media_tree.cms_media_plugins.forms import MediaTreeImagePluginForm, MediaTreeListPluginForm, MediaTreeSlideshowPluginForm, MediaTreeGalleryPluginForm, MediaTreeSlideshowItemInlineForm, MediaTreeGalleryItemInlineForm, MediaTreeListItemInline, MediaTreeSlideshowItemInline, MediaTreeGalleryItemInline
from django.core.urlresolvers import reverse
from django import forms
from media_tree import app_settings
from django.utils.safestring import mark_safe
from media_tree.utils import widthratio
from django.db import models
from django.core.urlresolvers import NoReverseMatch
import os

MEDIA_SUBDIR = app_settings.get('MEDIA_TREE_MEDIA_SUBDIR')

# TODO: Disentangle settings
# TODO: Solve image_detail with get_absolute_url()?
# TODO: Rework gallery plugin

class MediaTreeImagePlugin(CMSPluginBase):

    model = MediaTreeImage
    name = _("Image")
    admin_preview = False
    render_template = 'cms/plugins/mediatreeimage.html'
    text_enabled = True
    form = MediaTreeImagePluginForm

    fieldsets = [
        (_('Image'), {
            'fields': ['node'],
        }), 
        (_('Settings'), {
            'fields': ['width', 'height'],
            'classes': ['collapse'],
        }), 
        (_('Link'), {
            'fields': ['link_type', 'link_url', 'link_page', 'link_target'],
            'classes': ['collapse'],
        }),
    ]
    exclude = ('body', 'render_template')

    def render(self, context, instance, placeholder):
        instance.node.link = PluginLink.create_from(instance)
        context.update({
            'image_node': instance.node,
        })
        if instance.width or instance.height:
            w = instance.width or widthratio(instance.height, instance.node.height, instance.node.width)
            h = instance.height or widthratio(instance.width, instance.node.width, instance.node.height)
            context.update({'thumbnail_size': (w, h)})

        return context


    def icon_src(self, instance):
        from sorl.thumbnail.main import DjangoThumbnail
        thumb = DjangoThumbnail(instance.node.file.name, (200, 200), ['sharpen'])
        return thumb.absolute_url

    def icon_alt(self, instance):
        return instance.node.alt


class MediaTreeListPlugin(CMSPluginBase):
    inlines = [MediaTreeListItemInline]
    model = MediaTreeList
    name = _('File list')
    admin_preview = False
    render_template = 'cms/plugins/mediatreelist.html'
    list_type = MediaTreeList.LIST_NESTED
    form = MediaTreeListPluginForm
    fieldsets = [
        (_('Settings'), {
            'fields': form().fields.keys(),
            'classes': ['collapse']
        }),
    ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.attname != 'cmsplugin_ptr_id':
            raise Exception(db_field.attname)
        #field = super(MediaTreeListPlugin, self)
    
    @staticmethod
    def list_str_callback(node):
        return FileNode.get_file_link(node, use_metadata=True, include_size=True, include_extension=True)

    list_max_depth = None
    list_filter_media_types = None
    single_folder_selected = False
    files_selected = False

    class FolderLink(FolderLinkBase):
        pass

    def get_render_nodes(self, context, instance):
        if self.list_max_depth is None:
            if not instance.include_descendants:
                if self.single_folder_selected:
                    max_depth = 0
                else:
                    max_depth = 1
            else:
                max_depth = None
        else:
            max_depth = self.list_max_depth

        if hasattr(instance, 'list_type'):
            self.list_type = instance.list_type
        
        if self.list_type == MediaTreeList.LIST_MERGED:
            list_method = getattr(FileNode, 'get_merged_list')
            exclude_media_types = (FileNode.FOLDER,)
        else:
            list_method = getattr(FileNode, 'get_nested_list')
            exclude_media_types = None

        if self.list_str_callback:
            processors = [self.list_str_callback]
        else:
            processors = None
        
        if instance.filter_supported:
            filter_media_types = self.list_filter_media_types
        else:
            filter_media_types = None
            
        return list_method(self.visible_nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types, 
            processors=processors, max_depth=max_depth, ordering=['position', 'name'])

    def init_folder(self, context, instance):
        folder_id = context['request'].GET.get(self.FolderLink.folder_param_name(instance), None)

        self.current_folder = None
        self.parent_folder = None
        self.selected_nodes = []
        self.files_selected = False
        for item in instance.media_items.all():
            item.node.link = PluginLink.create_from(item)
            self.selected_nodes.append(item.node)
            if item.node.node_type != FileNode.FOLDER:
                self.files_selected = True

        if folder_id:
            # try to open folder according to query argument, and validate that it's a subfolder of selected folders
            # from django.core.exceptions import PermissionDenied
            try:
                requested_folder = FileNode.objects.get(pk=folder_id, node_type=FileNode.FOLDER)
                is_child_of_selected = requested_folder in self.selected_nodes
                if is_child_of_selected or (instance.include_descendants and requested_folder.is_descendant_of(self.selected_nodes)):
                    self.current_folder = requested_folder
                    self.visible_nodes = self.current_folder.get_children()
                    if not is_child_of_selected:
                        self.parent_folder = self.current_folder.parent
                else:
                    # folder query argument will be ignored
                    pass
                    # raise PermissionDenied('Requested folder "%s" is not in selected items' % repr(requested_folder))
            except FileNode.DoesNotExist:
                # folder query argument will be ignored
                pass

        if not self.current_folder:
            self.single_folder_selected = len(self.selected_nodes) == 1 and self.selected_nodes[0].node_type == FileNode.FOLDER
            if not self.single_folder_selected:
                self.visible_nodes = self.selected_nodes
            else:
                self.visible_nodes = self.selected_nodes[0].get_children()

    def render(self, context, instance, placeholder):
        self.init_folder(context, instance)
        context.update({ 
            'nodes': self.get_render_nodes(context, instance),
        })
        return context


class MediaTreeSlideshowPlugin(MediaTreeListPlugin):

    inlines = [MediaTreeSlideshowItemInline]
    list_type = MediaTreeList.LIST_MERGED
    list_str_callback = None
    list_filter_media_types = (media_types.SUPPORTED_IMAGE,)

    class PluginMedia:
        js = [
            os.path.join(MEDIA_SUBDIR, 'lib/jquery.cycle/jquery.cycle.all.js'),
        ]
        
    model = MediaTreeSlideshow
    form = MediaTreeSlideshowPluginForm
    fieldsets = [
        (_('Settings'), {
            'fields': form().fields.keys(),
            'classes': ['collapse']
        }),
    ]
    name = _('Slideshow')
    admin_preview = False
    render_template = 'cms/plugins/mediatreeslideshow.html'
    
    def render(self, context, instance, placeholder):
        context = super(MediaTreeSlideshowPlugin, self).render(context, instance, placeholder)
        context.update({ 
            'timeout': instance.timeout,
            'fx': instance.fx,
            'speed': instance.speed,
        })
        if instance.width or instance.height:
            w = instance.width or instance.height
            h = instance.height or instance.width
            context.update({'thumbnail_size': (w, h)})

        return context


# TODO count_descendants ONLY of same type 
class MediaTreeGalleryPlugin(MediaTreeSlideshowPlugin):

    inlines = [MediaTreeGalleryItemInline]

    class PluginMedia:
        js = [
            os.path.join(MEDIA_SUBDIR, 'lib/jquery.cycle/jquery.cycle.all.js'),
        ]

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
        if instance.list_type == MediaTreeList.LIST_NESTED:
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
        if instance.list_type == MediaTreeList.LIST_NESTED and (instance.include_descendants or not self.single_folder_selected):
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


plugin_pool.register_plugin(MediaTreeImagePlugin)
plugin_pool.register_plugin(MediaTreeListPlugin)
plugin_pool.register_plugin(MediaTreeSlideshowPlugin)
plugin_pool.register_plugin(MediaTreeGalleryPlugin)
