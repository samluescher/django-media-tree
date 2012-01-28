from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListing, MediaTreeListingItem
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormInlinePositioningBase
from media_tree.contrib.views.listing import FileNodeListingFilteredByFolderMixin
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


class MediaTreeListingPluginForm(MediaTreePluginFormInlinePositioningBase):
    
    class Meta:
        model = MediaTreeListing
    

class MediaTreeListingItemInline(admin.StackedInline):
    model = MediaTreeListingItem
    extra = 0


class MediaTreeListingPlugin(CMSPluginBase, FileNodeListingFilteredByFolderMixin):
    model = MediaTreeListing
    module = _('Media Tree')
    name = _('File listing')
    admin_preview = False
    render_template = 'cms/plugins/media_tree_listing.html'
    form = MediaTreeListingPluginForm
    inlines = [MediaTreeListingItemInline]
    fieldsets = [
        (_('Settings'), {
            'fields': form().fields.keys(),
            'classes': ['collapse']
        }),
    ]

    filter_by_parent_folder = False

    def render(self, context, instance, placeholder):
        selected_nodes = [item.node for item in instance.media_items.all()]
        view = self.get_listing_view(context['request'], selected_nodes, opts=instance)
        view.folder_pk_param_name = 'folder-%i' % instance.pk
        context.update(view.get_context_data())
        return context


plugin_pool.register_plugin(MediaTreeListingPlugin)
