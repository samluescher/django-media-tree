from media_tree.contrib.views.detail import FileNodeDetailView, FileNodeDetailMixin
from media_tree.utils import widthratio
from media_tree import media_types


class ImageNodeDetailView(FileNodeDetailView):
    """
    View class for implementing image detail views for ``FileNode`` objects.
    This class is based on Django's generic ``DetailView``. Please refer to the
    respective Django documentation on subclassing and customizing `Class-based
    generic views
    <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.

    The following example ``urls.py`` would implement a detail view capable of
    displaying all image files under a folder node with the path
    ``some/folder``:: 

        from media_tree.models import FileNode
        from media_tree.contrib.views.detail.image import ImageNodeDetailView
        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^images/(?P<pk>\d+)/$', ImageNodeDetailView.as_view(
                queryset=FileNode.objects.get(path='some/folder').get_descendants()
            )),
        )
    """

    width = None
    """ Maximum width of the thumbnail. If not set, default values will be used. """

    height = None
    """ Maximum height of the thumbnail. If not set, default values will be used. """

    context_object_name = 'image_node'
    """ Designates the name of the variable to use in the context. """

    template_name = "media_tree/image_detail.html"
    """ Name of the template. """

    filter_media_types = (media_types.SUPPORTED_IMAGE,)


    def get_context_data(self, **kwargs):
        context = super(ImageNodeDetailView, self).get_context_data(**kwargs)

        if self.width or self.height:
            w = self.width or widthratio(self.height, self.object.height, self.object.width)
            h = self.height or widthratio(self.width, self.object.width, self.object.height)
            context.update({'thumbnail_size': (w, h)})

        return context


class ImageNodeDetailMixin(FileNodeDetailMixin):
    """
    A mixin that you can use as a superclass for your own custom plugins
    for interfacing with third-party applications, such as Django CMS. Please
    take a look at :ref:`custom-plugins-howto` for more information.
    """
    
    view_class = ImageNodeDetailView
    """ The view class instantiated by ``get_detail_view()``. """

