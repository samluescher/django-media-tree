from django.db import models
from cms.models import CMSPlugin, Page
from media_tree.fields import FileNodeForeignKey
from media_tree import media_types, app_settings
from media_tree.models import FileNode
from django.utils.translation import ugettext_lazy as _
from django import forms

class DimensionField(models.CharField):
    """
    CharField for image dimensions. Currently, this needs to be an integer > 0, but since it
    is a CharField, it might also contain units such as "px" or "%" in the future. 
    """
    def __init__(self, verbose_name=None, name=None, **kwargs):
        if not 'max_length' in kwargs:
            kwargs['max_length'] = 8
        super(DimensionField, self).__init__(verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'regex': '^[1-9][0-9]*$',
                    'form_class': forms.RegexField}
        defaults.update(kwargs)
        return models.Field.formfield(self, **defaults)

class MediaTreeImage(CMSPlugin):
    node = FileNodeForeignKey(allowed_media_types=(media_types.SUPPORTED_IMAGE,), verbose_name=_('file'))
    link_type = models.CharField(_('link type'), max_length=1, blank=True, null=True, default=app_settings.get('MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_DEFAULT'), choices=app_settings.get('MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_CHOICES'), help_text=_('Makes the image a clickable link.'))
    link_page = models.ForeignKey(Page, verbose_name=_("page"), null=True, blank=True, help_text=_('For link to page. Select any page from the list.'))
    link_url = models.CharField(_("web address"), max_length=255, blank=True, null=True, help_text=_('For link to web address. Example: Enter "http://www.domain.com" to create an absolute link to an external site, or enter a relative URL like "/about/contact".'))
    link_target = models.CharField(_("link target"), max_length=64, blank=True, null=True, choices=(('', _('same window')), ('_blank', _('new window'))))
    width = DimensionField(_('max. width'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image width.'))
    height = DimensionField(_('max. height'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image height.'))
    render_template = models.CharField(_("template"), max_length=100, choices=None, blank=True, null=True, help_text=_('Template used to render the image.'))

    def __unicode__(self):
        return self.node.__unicode__()

class AbstractMediaTreeList(CMSPlugin):
    
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

class MediaTreeList(AbstractMediaTreeList):
    list_type = models.CharField(_('List type'), max_length=1, default=AbstractMediaTreeList.LIST_NESTED, choices=((AbstractMediaTreeList.LIST_MERGED, _('merged')), (AbstractMediaTreeList.LIST_NESTED, _('nested'))))
    
class AbstractMediaTreeSlideshow(AbstractMediaTreeList):
    timeout = models.IntegerField(_('pause between images'), default=4000, help_text=_('Milliseconds'))
    fx = models.CharField(_('transition'), max_length=32, default='fade', choices=app_settings.get('MEDIA_TREE_SLIDESHOW_TRANSITION_FX_CHOICES'))
    speed = models.CharField(_('transition speed'), max_length=8, default='normal', choices=(('slow', _('slow')), ('normal', _('normal')), ('fast', _('fast')))) 
    width = DimensionField(_('max. width'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image width.'))
    height = DimensionField(_('max. height'), null=True, blank=True, help_text=_('You can leave this empty to use an automatically determined image height.'))
    filter_supported = models.BooleanField(_('output supported media types only'), default=True)

    class Meta:
        abstract = True

class MediaTreeSlideshow(AbstractMediaTreeSlideshow):
    pass

class MediaTreeGallery(AbstractMediaTreeSlideshow):
    list_type = models.CharField(_('gallery type'), max_length=1, default=AbstractMediaTreeList.LIST_NESTED, choices=((AbstractMediaTreeList.LIST_MERGED, _('merged')), (AbstractMediaTreeList.LIST_NESTED, _('nested'))))
    auto_play = models.BooleanField('auto play', default=False)

class AbstractMediaTreeListItem(models.Model):
    position = models.IntegerField(_('position'), default=1)
    class Meta:
        abstract = True
        ordering = ['position', 'id']
        verbose_name = _('media object')
        verbose_name_plural = _('media objects')

class MediaTreeListItem(AbstractMediaTreeListItem):
    list_plugin = models.ForeignKey(MediaTreeList, related_name='media_items')
    node = FileNodeForeignKey(verbose_name=_('folder/file'))

class AbstractMediaTreeImageItem(AbstractMediaTreeListItem):
    node = FileNodeForeignKey(verbose_name=_('folder/image'), allowed_media_types=(FileNode.FOLDER, media_types.SUPPORTED_IMAGE,))
    link_type = models.CharField(_('link type'), max_length=1, blank=True, null=True, default=app_settings.get('MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_DEFAULT'), choices=app_settings.get('MEDIA_TREE_CMS_PLUGIN_LINK_TYPE_CHOICES'), help_text=_('Makes the image a clickable link.'))
    link_page = models.ForeignKey(Page, verbose_name=_("page"), null=True, blank=True, help_text=_('For link to page. Select any page from the list.'))
    link_url = models.CharField(_("web address"), max_length=255, blank=True, null=True, help_text=_('For link to web address. Example: Enter "http://www.domain.com" to create an absolute link to an external site, or enter a relative URL like "/about/contact".'))
    link_target = models.CharField(_("link target"), max_length=64, blank=True, null=True, choices=(('', _('same window')), ('_blank', _('new window'))))
    
    class Meta:
        abstract = True

class MediaTreeSlideshowItem(AbstractMediaTreeImageItem):
    list_plugin = models.ForeignKey(MediaTreeSlideshow, related_name='media_items')
    
class MediaTreeGalleryItem(AbstractMediaTreeImageItem):
    list_plugin = models.ForeignKey(MediaTreeGallery, related_name='media_items')
