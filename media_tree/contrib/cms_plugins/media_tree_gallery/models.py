from django.contrib.sites.models import Site
from media_tree.contrib.cms_plugins.media_tree_listing.models import MediaTreeListingBase
from media_tree.contrib.cms_plugins.media_tree_slideshow.models import MediaTreeImageListingBase, MediaTreeImageItemBase
from media_tree.fields import FileNodeForeignKey
from media_tree.contrib.views.listing import LISTING_MERGED, LISTING_NESTED
from django.db import models
from django.utils.translation import ugettext_lazy as _


class MediaTreeGallery(MediaTreeImageListingBase):
    list_type = models.CharField(_('gallery type'), max_length=1, default=LISTING_MERGED, 
    	choices=((LISTING_MERGED, _('merged')), (LISTING_NESTED, _('nested'))),
    	help_text=_('A nested gallery includes a browseable folder list. A merged gallery displays media from all folders merged into a flat list.'))
    auto_play = models.BooleanField('auto play', default=False)


class MediaTreeGalleryItem(MediaTreeImageItemBase):
    list_plugin = models.ForeignKey(MediaTreeGallery, related_name='media_items')
    node = FileNodeForeignKey(verbose_name=_('folder/file'), limit_choices_to={"site": Site.objects.get_current})

    def copy_relations(self, oldinstance):
        self.list_plugin = oldinstance.list_plugin.all()
        self.node = oldinstance.node.all()