from cms.app_base import CMSApp
from cms.apphook_pool import apphook_pool
from django.utils.translation import ugettext_lazy as _
 
class MediaTreeApphook(CMSApp):
    name = _("Media Tree")
    urls = ["media_tree.urls"]
 
apphook_pool.register(MediaTreeApphook)
