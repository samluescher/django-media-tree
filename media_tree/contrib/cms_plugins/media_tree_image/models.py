from django.contrib.sites.models import Site
from media_tree import media_types
from media_tree.contrib.cms_plugins import settings as plugins_settings
from media_tree.fields import FileNodeForeignKey, DimensionField
from cms.models import CMSPlugin, Page
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MediaTreeImageSiteManager(models.Manager):
    def get_query_set(self):
        return super(MediaTreeImageSiteManager, self).get_query_set().filter(node__site=Site.objects.get_current())


class MediaTreeImage(CMSPlugin):
    node = FileNodeForeignKey(allowed_media_types=(media_types.SUPPORTED_IMAGE,), verbose_name=_('file'))
    link_type = models.CharField(_('link type'), max_length=1, blank=True, null=True, default=plugins_settings.MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_DEFAULT, choices=plugins_settings.MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_CHOICES, help_text=_('Makes the image a clickable link.'))
    link_page = models.ForeignKey(Page, verbose_name=_("page"), null=True, blank=True, help_text=_('For link to page. Select any page from the list.'))
    link_url = models.CharField(_("web address"), max_length=255, blank=True, null=True, help_text=_('For link to web address. Example: Enter "http://www.domain.com" to create an absolute link to an external site, or enter a relative URL like "/about/contact".'))
    link_target = models.CharField(_("link target"), max_length=64, blank=True, null=True, choices=(('', _('same window')), ('_blank', _('new window'))))
    width = DimensionField(_('max. width'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image width.'))
    height = DimensionField(_('max. height'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image height.'))
    render_template = models.CharField(_("template"), max_length=100, choices=None, blank=True, null=True, help_text=_('Template used to render the image.'))

    objects = MediaTreeImageSiteManager()

    def __unicode__(self):
        return self.node.__unicode__()
