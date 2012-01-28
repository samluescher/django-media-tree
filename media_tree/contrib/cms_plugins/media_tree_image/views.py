from media_tree.contrib.cms_plugins.media_tree_image.models import MediaTreeImage
from media_tree.contrib.cms_plugins.helpers import PluginLink
from media_tree.models import FileNode
from media_tree.contrib.views.detail.image import ImageNodeDetailView
from django.utils.translation import ugettext_lazy as _
from cms.utils.page_resolver import get_page_from_path
from django.http import Http404


class ImagePluginDetailView(ImageNodeDetailView):

    return_url = None

    def get_object(self, *args, **kwargs):
        obj = super(ImagePluginDetailView, self).get_object(*args, **kwargs)
        if obj:
            allowed = False
            # validate that the object is actually published using the plugin...
            for plugin in MediaTreeImage.objects.filter(node=obj):
                # ...and on a publicly accessible page.
                # TODO: Iterating all plugins and getting each page
                # is a bit inefficient.
                page = get_page_from_path(plugin.page.get_path())
                if page:
                    allowed = True
                    break
            if not allowed:
                raise Http404
        return obj

    def get_context_data(self, *args, **kwargs):
        context_data = super(ImagePluginDetailView, self).get_context_data(
            *args, **kwargs)

        if self.return_url:
            page = get_page_from_path(self.return_url.strip('/'))
            if page:
                context_data.update({
                    'link': PluginLink(url=page.get_absolute_url(),
                        text=_('Back to %s') % page.get_title())
                })

        return context_data

    def get(self, request, *args, **kwargs):
        self.return_url = request.GET.get('return_url', None)
        return super(ImagePluginDetailView, self).get(request, *args, **kwargs)