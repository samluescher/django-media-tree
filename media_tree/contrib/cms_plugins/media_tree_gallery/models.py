from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListingBase
from media_tree.contrib.cms_plugins.media_tree_slideshow.models import MediaTreeImageListingBase, MediaTreeImageItemBase
from media_tree.fields import FileNodeForeignKey
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MediaTreeGallery(MediaTreeImageListingBase):
    list_type = models.CharField(_('gallery type'), max_length=1, default=MediaTreeListingBase.LIST_MERGED, 
    	choices=((MediaTreeListingBase.LIST_MERGED, _('merged')), (MediaTreeListingBase.LIST_NESTED, _('nested'))),
    	help_text=_('A nested gallery includes a browseable folder list. A merged gallery displays media from all folders merged into a flat list.'))
    auto_play = models.BooleanField('auto play', default=False)


class MediaTreeGalleryItem(MediaTreeImageItemBase):
    list_plugin = models.ForeignKey(MediaTreeGallery, related_name='media_items')
    node = FileNodeForeignKey(verbose_name=_('folder/file'))
