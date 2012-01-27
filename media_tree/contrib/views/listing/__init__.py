from media_tree.models import FileNode
from media_tree.contrib.views.base import PluginMixin
from media_tree.utils.filenode import get_file_link, get_merged_filenode_list, get_nested_filenode_list
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _


LISTING_MERGED = 'M'
LISTING_NESTED = 'N'


class ListingView(ListView):
    """
    View class for implementing views that render a file listing. This class is
    based on Django's generic ``ListView``. Please refer to the respective
    Django documentation on subclassing and customizing `Class-based generic
    views <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.

    The following example ``urls.py`` would implement a view listing a folder
    with the path ``some/folder`` and its immediate children, but not
    descendants deeper down the hierarchy:: 

        from media_tree.models import FileNode
        from media_tree.contrib.views.listing import ListingView
        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^listing/', ListingView.as_view(
                # notice that queryset can be any iterable, for instance a list:
                queryset=[FileNode.objects.get_by_path('some/folder')],
                include_descendants=False
            )),
        )
    """

    list_type = LISTING_NESTED
    list_max_depth = None
    list_filter_media_types = None
    include_descendants = True
    template_name = 'media_tree/filenode_list.html'

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

        if not 'title' in context:
            context['title'] = _('media objects')

        return context


class ListingMixin(PluginMixin):
    """
    A mixin that you can use as a superclass for your own custom plugins
    for interfacing with third-party applications, such as Django CMS. Please
    take a look at :ref:`custom-plugins` for more information.
    """

    view_class = ListingView
    """ The view class instantiated by ``get_listing_view()``. """

    def get_listing_view(self, queryset, opts=None):
        """
        Instantiates and returns the view class that will generate the
        actual context for this plugin.

        ``queryset`` can be an actual QuerySet or any iterable.
        """
        view = self.view_class(ListingView, opts)
        view.queryset = selected_nodes
        return view 
