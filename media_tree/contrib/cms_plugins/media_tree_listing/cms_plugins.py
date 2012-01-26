from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListing, MediaTreeListingItem
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormBase
from media_tree.contrib.views.listing.base import ListingView
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from django.contrib import admin


class MediaTreeListingPluginForm(MediaTreePluginFormBase):
    class Meta:
        model = MediaTreeListing


class MediaTreeListingItemInline(admin.StackedInline):
    model = MediaTreeListingItem
    extra = 1


class MediaTreeListingPlugin(CMSPluginBase):
    module = _('Media Tree')
    model = MediaTreeListing
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

    def get_view(self, instance, opts=None, view_class=ListingView):
        if hasattr(instance, 'list_type'):
            list_type = instance.list_type
        else:
            list_type = self.list_type
        kwargs = {
            'list_type': list_type,
            'include_descendants': instance.include_descendants,
            'filename_filter': instance.filename_filter,
            'selected_nodes': [item.node for item in instance.media_items.all()]
        }
        view = view_class(**kwargs)
        return view 

    def render(self, context, instance, placeholder):
        view = self.get_view(instance)
        context.update(view.get_context_data(object_list=view.selected_nodes))
        return context


plugin_pool.register_plugin(MediaTreeListingPlugin)
