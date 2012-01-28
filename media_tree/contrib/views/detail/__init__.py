from media_tree.models import FileNode
from media_tree.contrib.views.mixin_base import PluginMixin
from django.views.generic.detail import DetailView
from django.http import Http404
from django.utils.translation import ugettext_lazy as _


class FileNodeDetailView(DetailView):
    """
    View class for implementing detail views for ``FileNode`` objects. This
    class is based on Django's generic ``DetailView``. Please refer to the
    respective Django documentation on subclassing and customizing `Class-based
    generic views
    <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.

    The following example ``urls.py`` would implement a detail view capable of
    displaying all files with the extension ``.txt``, with URLs containing the
    full path of the ``FileNode`` object, for instance
    ``http://yourdomain.com/files/some/folder/ReadMe.txt``:: 

        from media_tree.models import FileNode
        from media_tree.contrib.views.detail import FileNodeDetailView
        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^files/(?P<path>.+)/$', FileNodeDetailView.as_view(
                queryset=FileNode.objects.filter(extension='txt')
            )),
        )
    """

    model = FileNode

    filter_media_types = None
    """ An iterable containing media types to filter for. """

    filter_node_types = (FileNode.FILE,)
    """ 
    An iterable containing node types to filter for. By default this is
    ``(FileNode.FILE,)``
    """

    context_object_name = 'object'
    """
    The context_object_name attribute on a generic view specifies the 
    context variable to use.
    """

    template_name = "media_tree/filenode_detail.html"
    """
    Name of the template.
    """

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `path` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        path = self.kwargs.get('path', None)

        # Next, try looking up by path.
        if path is not None:
            queryset = queryset.filter(**FileNode.objects.get_filter_args_with_path(
                for_self=True, path=path))
            try:
                obj = queryset.get()
            except FileNode.DoesNotExist:
                raise Http404(_(u"No %(verbose_name)s found matching the query") %
                              {'verbose_name': queryset.model._meta.verbose_name})
            return obj

        return super(FileNodeDetailView, self).get_object(queryset)

    def get_queryset(self, *args, **kwargs):
        queryset = super(FileNodeDetailView, self).get_queryset(*args, **kwargs)
        kwargs = {}
        if self.filter_node_types:
            kwargs['node_type__in'] = self.filter_node_types
        if self.filter_media_types:
            kwargs['media_type__in'] = self.filter_media_types
        return queryset.filter(**kwargs)

    def get_context_data(self, **kwargs):
        context = super(FileNodeDetailView, self).get_context_data(**kwargs)
        if not 'title' in context:
            context['title'] = context[self.context_object_name].title or context[self.context_object_name].name 
        return context


class FileNodeDetailMixin(PluginMixin):
    
    view_class = FileNodeDetailView
    """ The view class instantiated by ``get_detail_view()``. """

    def get_detail_view(self, request, object, opts=None):
        """
        Instantiates and returns the view class that will generate the actual
        context for this plugin.
        """
        view = self.get_view(request, self.view_class, opts)
        view.object = object
        return view 
