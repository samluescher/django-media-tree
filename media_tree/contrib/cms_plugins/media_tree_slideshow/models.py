from media_tree.fields import DimensionField
from media_tree.contrib.cms_plugins.media_tree_slideshow import settings as app_settings
from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListingBase, MediaTreeListingItemBase
from media_tree.contrib.cms_plugins import settings as plugins_settings
from media_tree.fields import FileNodeForeignKey
from cms.models import Page
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MediaTreeImageListingBase(MediaTreeListingBase):
    timeout = models.IntegerField(_('pause between images'), default=4000, help_text=_('Milliseconds'))
    fx = models.CharField(_('transition'), max_length=32, default='fade', choices=app_settings.MEDIA_TREE_SLIDESHOW_TRANSITION_FX_CHOICES)
    speed = models.CharField(_('transition speed'), max_length=8, default='normal', choices=(('slow', _('slow')), ('normal', _('normal')), ('fast', _('fast'))))
    width = DimensionField(_('max. width'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image width.'))
    height = DimensionField(_('max. height'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image height.'))
    filter_supported = models.BooleanField(_('output supported media types only'), default=True)

    class Meta:
        abstract = True


class MediaTreeSlideshow(MediaTreeImageListingBase):
    pass


class MediaTreeImageItemBase(MediaTreeListingItemBase):
    link_type = models.CharField(_('link type'), max_length=1, blank=True, null=True, default=plugins_settings.MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_DEFAULT, choices=plugins_settings.MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_CHOICES, help_text=_('Makes the image a clickable link.'))
    link_page = models.ForeignKey(Page, verbose_name=_("page"), null=True, blank=True, help_text=_('For link to page. Select any page from the list.'))
    link_url = models.CharField(_("web address"), max_length=255, blank=True, null=True, help_text=_('For link to web address. Example: Enter "http://www.domain.com" to create an absolute link to an external site, or enter a relative URL like "/about/contact".'))
    link_target = models.CharField(_("link target"), max_length=64, blank=True, null=True, choices=(('', _('same window')), ('_blank', _('new window'))))

    class Meta:
        abstract = True


class MediaTreeSlideshowItem(MediaTreeImageItemBase):
    list_plugin = models.ForeignKey(MediaTreeSlideshow, related_name='media_items')
    node = FileNodeForeignKey(verbose_name=_('folder/file'))
