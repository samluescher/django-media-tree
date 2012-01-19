from media_tree.models import FileNode
from media_tree.contrib.cms_plugins.helpers import PluginLink, FolderLinkBase
from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListing, MediaTreeListingItem
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormBase
from media_tree import media_types
from media_tree.media_backends import get_media_backend
from media_tree import settings as media_tree_settings
from media_tree.utils import widthratio
from media_tree.utils.filenode import get_file_link, get_merged_filenode_list, get_nested_filenode_list
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse
from django import forms
from django.utils.safestring import mark_safe
from django.db import models
from django.core.urlresolvers import NoReverseMatch
from django.contrib import admin
import os


class MediaTreeListingPluginForm(MediaTreePluginFormBase):
    class Meta:
        model = MediaTreeListing


class MediaTreeListingItemInline(admin.StackedInline):
    model = MediaTreeListingItem
    extra = 1


class MediaTreeListingPlugin(CMSPluginBase):
    inlines = [MediaTreeListingItemInline]
    module = _('Media Tree')
    model = MediaTreeListing
    name = _('File listing')
    admin_preview = False
    render_template = 'cms/plugins/media_tree_listing.html'
    list_type = MediaTreeListing.LIST_NESTED
    form = MediaTreeListingPluginForm
    fieldsets = [
        (_('Settings'), {
            'fields': form().fields.keys(),
            'classes': ['collapse']
        }),
    ]

    def init_nodes(self, context, instance):
        self.current_folder = None
        self.parent_folder = None
        self.selected_nodes = []
        self.files_selected = False
        self.selected_nodes = [item.node for item in instance.media_items.all()]
        self.visible_nodes = [node for node in self.selected_nodes]

    #def formfield_for_manytomany(self, db_field, request, **kwargs):
    #    if db_field.attname != 'cmsplugin_ptr_id':
    #        raise Exception(db_field.attname)
        #field = super(MediaTreeListPlugin, self)

    @staticmethod
    def list_str_callback(node):
        return get_file_link(node, use_metadata=True, include_size=True, include_extension=True, include_icon=True)

    list_max_depth = None
    list_filter_media_types = None
    files_selected = False

    class FolderLink(FolderLinkBase):
        pass

    def get_render_nodes(self, context, instance):
        if self.list_max_depth is None:
            if not instance.include_descendants:
                max_depth = 2
            else:
                max_depth = None
        else:
            max_depth = self.list_max_depth

        if hasattr(instance, 'list_type'):
            self.list_type = instance.list_type

        if self.list_type == MediaTreeListing.LIST_MERGED:
            list_method = get_merged_filenode_list
            exclude_media_types = (FileNode.FOLDER,)
        else:
            list_method = get_nested_filenode_list
            exclude_media_types = None

        if self.list_str_callback:
            processors = [self.list_str_callback]
        else:
            processors = None

        if getattr(instance, 'filter_supported', None):
            filter_media_types = self.list_filter_media_types
        else:
            filter_media_types = None

        return list_method(self.visible_nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types,
            processors=processors, max_depth=max_depth, ordering=['position', 'name'])

    def render(self, context, instance, placeholder):
        self.init_nodes(context, instance)
        context.update({
            'nodes': self.get_render_nodes(context, instance),
        })
        return context


plugin_pool.register_plugin(MediaTreeListingPlugin)
