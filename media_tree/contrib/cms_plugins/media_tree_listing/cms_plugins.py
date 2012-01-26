from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListing, MediaTreeListingItem
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormInlinePositioningBase
from media_tree.contrib.views.detail import ListingMixin
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


class MediaTreeListingPlugin(CMSPluginBase, ListingMixin):
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

    def render(self, context, instance, placeholder):
        selected_nodes = [item.node for item in instance.media_items.all()]
        view = self.get_listing_view(selected_nodes, opts=instance)
        context.update(view.get_context_data())
        return context


plugin_pool.register_plugin(MediaTreeListingPlugin)
