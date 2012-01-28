from media_tree.utils.filenode import get_file_link
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.core.urlresolvers import NoReverseMatch


class PluginLink(object):
    
    LINK_PAGE = 'P'
    LINK_URL = 'U'
    LINK_IMAGE_DETAIL = 'I'
    LINK_URL_REVERSE = 'R'
    
    def __init__(self, type=LINK_URL, url=None, text='', obj=None, rel=None, target=None, querystring=''):
        self.type = type
        self.url = url
        self.obj = obj
        self.target = target
        self.querystring = querystring
        self.text = text
        if self.type == PluginLink.LINK_IMAGE_DETAIL:
            self.url = ['media_tree.contrib.cms_plugins.media_tree_image.ImagePluginDetailView', self.obj.pk]
            self.rel = 'image-detail'

    def href(self):
        href = None
        if self.type == PluginLink.LINK_URL:
            href = self.url
        if self.type in (PluginLink.LINK_URL_REVERSE, PluginLink.LINK_IMAGE_DETAIL):
            if isinstance(self.url, basestring):
                parts = self.url.split(' ')
            else:
                parts = self.url
            name = parts.pop(0)
            try:
                href = reverse(name, args=parts)
            except NoReverseMatch:
                raise
        if self.type == PluginLink.LINK_PAGE:
            href = self.obj.get_absolute_url()
        if href != None:
            href += self.querystring
        return href

    @staticmethod
    def create_from(instance):
        if not getattr(instance, 'link_type', None):
            return None
        querystring = ''
        if instance.link_type == PluginLink.LINK_PAGE:
            link_obj = instance.link_page
        elif instance.link_type == PluginLink.LINK_IMAGE_DETAIL:
            link_obj = instance.node
            if getattr(instance, 'page', None):
                querystring = '?return_url=%s' % instance.page.get_absolute_url()
        else:
            link_obj = None
        return PluginLink(instance.link_type, url=instance.link_url, obj=link_obj, target=instance.link_target, querystring=querystring)

