from media_tree.contrib.views.base import PluginMixin
from django.views.generic.detail import DetailView
from media_tree.utils import widthratio


class ImageDetailView(DetailView):

    width = None
    height = None
    context_object_name = 'image_node'

    def get_context_data(self):
        context = super(ImageDetailView, self).get_context_data()

        if self.width or self.height:
            w = self.width or widthratio(self.height, self.object.height, self.object.width)
            h = self.height or widthratio(self.width, self.object.width, self.object.height)
            context.update({'thumbnail_size': (w, h)})

        return context


class ImageDetailMixin(PluginMixin):

    def get_detail_view(self, object, opts=None):
        """
        Instantiates and returns the view class that will generate the
        actual context for this plugin.
        """
        view = self.get_view(ImageDetailView, opts)
        view.object = object
        return view 
