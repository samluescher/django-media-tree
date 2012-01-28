from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _
 
class MediaTreeImagePluginApphook(CMSApp):
    name = _("Media Tree Image Detail")
    urls = ["media_tree.contrib.cms_plugins.media_tree_image.urls"]
 
apphook_pool.register(MediaTreeImagePluginApphook)
