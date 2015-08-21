from media_tree.contrib.cms_plugins.media_tree_image.models import MediaTreeImage
from media_tree.contrib.cms_plugins.forms import MediaTreePluginFormBase
from media_tree.contrib.views.detail.image import ImageNodeDetailMixin
from media_tree import media_types
from media_tree.media_backends import get_media_backend
from media_tree.contrib.cms_plugins.helpers import PluginLink
from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _

# TODO: Solve image_detail with get_absolute_url()?


class MediaTreeImagePluginForm(MediaTreePluginFormBase):
    class Meta:
        model = MediaTreeImage
        fields = '__all__'


class MediaTreeImagePlugin(CMSPluginBase, ImageNodeDetailMixin):
    model = MediaTreeImage
    module = _('Media Tree')
    name = _("Image")
    admin_preview = False
    render_template = 'cms/plugins/media_tree_image.html'
    text_enabled = True
    form = MediaTreeImagePluginForm

    fieldsets = [
        (_('Image'), {
            'fields': ['node'],
        }),
        (_('Settings'), {
            'fields': ['width', 'height'],
            'classes': ['collapse'],
        }),
        (_('Link'), {
            'fields': ['link_type', 'link_url', 'link_page', 'link_target'],
            'classes': ['collapse'],
        }),
    ]
    exclude = ('body', 'render_template')

    def render(self, context, instance, placeholder):
        view = self.get_detail_view(context['request'], instance.node, opts=instance)
        context.update(view.get_context_data())
        if instance.link_type:
            context[view.context_object_name].link = PluginLink.create_from(instance)

        return context

    def icon_src(self, instance):
        media_backend = get_media_backend(fail_silently=False, handles_media_types=(
            media_types.SUPPORTED_IMAGE,))
        thumb = media_backend.get_thumbnail(instance.node.file, {'size': (200, 200)})
        return thumb.url

    def icon_alt(self, instance):
        return instance.node.alt


plugin_pool.register_plugin(MediaTreeImagePlugin)
