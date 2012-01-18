from media_tree import media_types
from media_tree.contrib.cms_plugins import settings as app_settings
from media_tree.models import FileNode
from media_tree.fields import FileNodeForeignKey
from cms.models import CMSPlugin
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MediaTreeListingBase(CMSPlugin):

    LIST_MERGED = 'M'
    LIST_NESTED = 'N'

    render_template = models.CharField(_('template'), max_length=100, choices=None, blank=True, null=True, help_text=_('Template used to render the plugin.'))
    filename_filter = models.CharField(_('filter file and folder names'), max_length=255, null=True, blank=True, help_text=_('Example: *.jpg; Documents.*;'), editable=False)
    include_descendants = models.BooleanField(_('include all subfolders'), default=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        # TODO return node list
        return ''


class MediaTreeListingItemBase(models.Model):
    position = models.IntegerField(_('position'), default=1)

    class Meta:
        abstract = True
        ordering = ['position', 'id']
        verbose_name = _('media object')
        verbose_name_plural = _('media objects')


class MediaTreeListing(MediaTreeListingBase):
    list_type = models.CharField(_('List type'), max_length=1, default=MediaTreeListingBase.LIST_NESTED, choices=((MediaTreeListingBase.LIST_MERGED, _('merged')), (MediaTreeListingBase.LIST_NESTED, _('nested'))))


class MediaTreeListingItem(MediaTreeListingItemBase):
    list_plugin = models.ForeignKey(MediaTreeListing, related_name='media_items')
    node = FileNodeForeignKey(verbose_name=_('folder/file'))
