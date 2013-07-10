from django.contrib.sites.models import Site
from media_tree import media_types
from media_tree.contrib.cms_plugins import settings as app_settings
from media_tree.fields import FileNodeForeignKey
from cms.models import CMSPlugin
from django.db import models
from django.utils.translation import ugettext_lazy as _
from media_tree.contrib.views.listing import LISTING_MERGED, LISTING_NESTED


class MediaTreeListingBase(CMSPlugin):

    render_template = models.CharField(_('template'), max_length=100, choices=None, blank=True, null=True, help_text=_('Template used to render the plugin.'))
    filename_filter = models.CharField(_('filter file and folder names'), max_length=255, null=True, blank=True, help_text=_('Example: *.jpg; Documents.*;'), editable=False)
    include_descendants = models.BooleanField(_('include all subfolders'), default=True)

    def copy_relations(self, oldinstance):
        for media_item in oldinstance.media_items.all():
            media_item.pk = None
            media_item.list_plugin = self
            media_item.save()

    class Meta:
        abstract = True

    def __unicode__(self):
        # TODO return node list
        return ''


class MediaTreeListingItemBase(models.Model):
    position = models.IntegerField(_('position'), blank=True)

    class Meta:
        abstract = True
        ordering = ['position', 'id']
        verbose_name = _('media object')
        verbose_name_plural = _('media objects')

    def save(self, *args, **kwargs):
        if self.position == None:
            self.position = 0
        super(MediaTreeListingItemBase, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.node.name


class MediaTreeListing(MediaTreeListingBase):
    list_type = models.CharField(_('List type'), max_length=1, default=LISTING_NESTED, choices=((LISTING_MERGED, _('merged')), (LISTING_NESTED, _('nested'))))


class MediaTreeListingItem(MediaTreeListingItemBase):
    list_plugin = models.ForeignKey(MediaTreeListing, related_name='media_items')
    node = FileNodeForeignKey(verbose_name=_('folder/file'), limit_choices_to={"site": Site.objects.get_current})

    def copy_relations(self, oldinstance):
        self.list_plugin = oldinstance.list_plugin.all()
        self.node = oldinstance.node.all()