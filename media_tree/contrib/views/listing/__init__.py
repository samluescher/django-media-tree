from media_tree.models import FileNode
from media_tree.contrib.views.base import PluginMixin
from media_tree.utils.filenode import get_file_link, get_merged_filenode_list, get_nested_filenode_list
from django.views.generic.list import ListView


LISTING_MERGED = 'M'
LISTING_NESTED = 'N'


class ListingView(ListView):

    selected_nodes = None
    list_type = LISTING_NESTED
    list_max_depth = None
    list_filter_media_types = None
    include_descendants = True

    def get_queryset(self):
        """
        Get the list of items for this view. This must be an interable, and may
        be a queryset (in which qs-specific behavior will be enabled).
        """
        if self.selected_nodes is not None:
        	return self.selected_nodes
        return super(ListingView, self).get_queryset()

    def init_nodes(self):
        self.current_folder = None
        self.parent_folder = None
        self.visible_nodes = [node for node in self.get_queryset()]

    def get_render_object_list(self, object_list):
        if self.list_max_depth is None:
            if not self.include_descendants:
                max_depth = 2
            else:
                max_depth = None
        else:
            max_depth = self.list_max_depth

        filter_media_types = self.list_filter_media_types

        if self.list_type == LISTING_MERGED:
            list_method = get_merged_filenode_list
            exclude_media_types = (FileNode.FOLDER,)
        else:
            list_method = get_nested_filenode_list
            exclude_media_types = None

        processors = None

        return list_method(self.visible_nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types,
            processors=processors, max_depth=max_depth, ordering=['position', 'name'])

    def get_context_data(self, **kwargs):
        if not 'object_list' in kwargs:
            kwargs['object_list'] = self.get_queryset()
        context = super(ListingView, self).get_context_data(**kwargs)
        self.init_nodes()
        context['object_list'] = self.get_render_object_list(context.pop('object_list'))
        return context


class ListingMixin(PluginMixin):

    def get_listing_view(self, selected_nodes, opts=None):
        """
        Instantiates and returns the view class that will generate the
        actual context for this plugin.
        """
        view = self.get_view(ListingView, opts)
        view.selected_nodes = selected_nodes
        return view 
