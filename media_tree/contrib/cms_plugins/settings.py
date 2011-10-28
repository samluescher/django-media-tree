from media_tree.contrib.cms_plugins.helpers import PluginLink
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_CHOICES = (
    (PluginLink.LINK_PAGE, _('Link to page')),
    (PluginLink.LINK_URL, _('Link to web address')),
    (PluginLink.LINK_IMAGE_DETAIL, _('Link to full size image')),
    (PluginLink.LINK_URL_REVERSE, _('Link to URL pattern')),
)

MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_DEFAULT = PluginLink.LINK_IMAGE_DETAIL  \
    if getattr(settings, 'CMS_APPLICATIONS_URLS', {}).has_key('media_tree.urls') else None

