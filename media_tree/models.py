#encoding=utf-8

from media_tree import settings as app_settings, media_types
from media_tree.utils import multi_splitext, join_formatted
from media_tree.utils.staticfiles import get_icon_finders
from media_tree.utils import get_media_storage

try:
    from mptt.models import MPTTModel as ModelBase
except ImportError:
    # Legacy mptt support
    import mptt
    from django.db.models import Model as ModelBase

from mptt.models import TreeForeignKey

from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import dateformat
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.conf import settings
from django.utils.formats import get_format
from django.db import models
from PIL import Image
import os
import mimetypes
import uuid


MIMETYPE_CONTENT_TYPE_MAP = app_settings.MEDIA_TREE_MIMETYPE_CONTENT_TYPE_MAP
EXT_MIMETYPE_MAP = app_settings.MEDIA_TREE_EXT_MIMETYPE_MAP
STATIC_SUBDIR = app_settings.MEDIA_TREE_STATIC_SUBDIR

MEDIA_TYPE_NAMES = app_settings.MEDIA_TREE_CONTENT_TYPES
ICON_FINDERS = get_icon_finders(app_settings.MEDIA_TREE_ICON_FINDERS)


# http://adam.gomaa.us/blog/2008/aug/11/the-python-property-builtin/
def Property(func):
    return property(**func())


class FileNode(ModelBase):
    """
    Each ``FileNode`` instance represents a node in the media object tree, that
    is to say a “file” or “folder”. Accordingly, their ``node_type`` attribute
    can either be ``FileNode.FOLDER``, meaning that they may have child nodes,
    or ``FileNode.FILE``, meaning that they are associated to media files in
    storage and are storing metadata about those files.

    .. Note::
       Since ``FileNode`` is a child class of ``MPTTModel``, it inherits many
       methods that facilitate queries and data manipulation when working with
       trees.
    """

    FOLDER = media_types.FOLDER
    """The constant denoting a folder node, used for the :attr:`node_type` attribute."""

    FILE = media_types.FILE
    """The constant denoting a file node, used for the :attr:`node_type` attribute."""

    STORAGE = get_media_storage()

    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('folder'), limit_choices_to={'node_type': FOLDER})
    
    node_type = models.IntegerField(_('node type'), choices = ((FOLDER, 'Folder'), (FILE, 'File')), editable=False, blank=False, null=False)
    media_type = models.IntegerField(_('media type'), choices = app_settings.MEDIA_TREE_CONTENT_TYPE_CHOICES, blank=True, null=True, editable=False)
    file = models.FileField(_('file'), upload_to=app_settings.MEDIA_TREE_UPLOAD_SUBDIR, null=True, storage=STORAGE)
    preview_file = models.ImageField(_('preview'), upload_to=app_settings.MEDIA_TREE_PREVIEW_SUBDIR, blank=True, null=True, help_text=_('Use this field to upload a preview image for video or similar media types.'), storage=STORAGE)
    published = models.BooleanField(_('is published'), blank=True, default=True, editable=False)
    mimetype = models.CharField(_('mimetype'), max_length=64, null=True, editable=False)

    name = models.CharField(_('name'), max_length=255, null=True)
    title = models.CharField(_('title'), max_length=255, default='', null=True, blank=True)
    description = models.TextField(_('description'), default='', null=True, blank=True)
    author = models.CharField(_('author'), max_length=255, default='', null=True, blank=True)
    publish_author = models.BooleanField(_('publish author'), default=False)
    copyright = models.CharField(_('copyright'), max_length=255, default='', null=True, blank=True)
    publish_copyright = models.BooleanField(_('publish copyright'), default=False)
    date_time = models.DateTimeField(_('date/time'), null=True, blank=True)
    publish_date_time = models.BooleanField(_('publish date/time'), default=False)
    keywords = models.CharField(_('keywords'), max_length=255, null=True, blank=True)
    override_alt = models.CharField(_('alternative text'), max_length=255, default='', null=True, blank=True, help_text=_('If you leave this blank, the alternative text will be compiled automatically from the available metadata.'))
    override_caption = models.CharField(_('caption'), max_length=255, default='', null=True, blank=True, help_text=_('If you leave this blank, the caption will be compiled automatically from the available metadata.'))

    has_metadata = models.BooleanField(_('metadata entered'), editable=False)

    extension = models.CharField(_('type'), default='', max_length=10, null=True, editable=False)
    size = models.IntegerField(_('size'), null=True, editable=False)
    # TODO: Refactor PIL stuff, width|height as extension?
    width = models.IntegerField(_('width'), null=True, blank=True, help_text=_('Detected automatically for supported images'))
    height = models.IntegerField(_('height'), null=True, blank=True, help_text=_('Detected automatically for supported images'))
    created = models.DateTimeField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateTimeField(_('modified'), auto_now=True, editable=False)

    slug = models.CharField(_('slug'), max_length=255, null=True, editable=False)
    is_default = models.BooleanField(_('use as default object for folder'), blank=True, default=False, help_text=_('The default object of a folder can be used for folder previews etc.'))

    created_by = models.ForeignKey(User, null=True, blank=True, related_name='created_by', verbose_name = _('created by'), editable=False)
    modified_by = models.ForeignKey(User, null=True, blank=True, related_name='modified_by', verbose_name = _('modified by'), editable=False)
    position = models.IntegerField(_('position'), default=0)

    is_ancestor_being_updated = False

    # TODO: PickledField for media extenders
    extra_metadata = models.TextField(_('extra metadata'), editable=None)

    class Meta:
        ordering = ['tree_id', 'lft']
        verbose_name = _('media object')
        verbose_name_plural = _('media objects')
        permissions = (
            ("manage_filenode", "Can perform management tasks"),
        )

    class MPTTMeta:
        order_insertion_by = ['name']

    @staticmethod
    def get_top_node():
        """Returns a symbolic node representing the root of all nodes. This node
        is not actually stored in the database, but used in the admin to link to
        the change list.
        """
        return FileNode(name=('Media objects'), level=-1)

    def is_top_node(self):
        """Returns True if the model instance is the top node."""
        return self.level == -1

    # Workaround for http://code.djangoproject.com/ticket/11058
    def admin_preview(self):
        pass

    # TODO: What's this for again?
    @Property
    def link():

        def fget(self):
            return getattr(self, 'link_obj', None)

        def fset(self, link_obj):
            self.link_obj = link_obj

        def fdel(self):
            del self.link_obj

        return locals()

    # TODO this should be called from FileNode.save(), not from admin (since there is no request on CopyFileNodesForm.save())
    # -- look into threadlocals
    def attach_user(self, user, change):
        if not change:
            self.created_by = user
        self.modified_by = user

    def get_node_path(self):
        nodes = []
        for node in self.get_ancestors():
            nodes.append(node)
        if (self.level != -1):
            nodes.insert(0, FileNode.get_top_node())
        nodes.append(self)
        return nodes

    def get_folder_tree(self):
        return self._tree_manager.all().filter(node_type=FileNode.FOLDER)

    def get_default_file(self, media_types=None):
        if self.node_type == FileNode.FOLDER:
            if not media_types:
                files = self.get_children().filter(node_type=FileNode.FILE)
            else:
                files = self.get_children().filter(media_type__in=media_types)
            # TODO the two counts are due to the fact that, at this time, it seems
            # not possible to order the QuerySet returned by get_children() by is_default
            if files.count() > 0:
                default = files.filter(is_default=True)
                if default.count() > 0:
                    return default[0]
                else:
                    return files[0]
            else:
                return None
        else:
            return self

    def get_qualified_file_url(self, field_name='file'):
        """Returns a fully qualified URL for the :attr:`file` field, including
        protocol, domain and port. In most cases, you can just use ``file.url``
        instead, which (depending on your ``MEDIA_URL``) may or may not contain
        the domain. In some cases however, you always need a fully qualified
        URL. This includes, for instance, embedding a flash video player from a
        remote domain and passing it a video URL.
        """
        url = getattr(self, field_name).url
        if '://' in url:
            # `MEDIA_URL` already contains domain
            return url
        protocol = getattr(settings, 'PROTOCOL', 'http')
        domain = Site.objects.get_current().domain
        port = getattr(settings, 'PORT', '')
        return '%(protocol)s://%(domain)s%(port)s%(url)s' % {
            'protocol': 'http',
            'domain': domain.rstrip('/'),
            'port': ':'+port if port else '',
            'url': url,
    }

    def get_qualified_preview_url(self):
        """Similar to :func:`get_qualified_file_url`, but returns the URL for
        the :attr:`preview_file` field, which can be used to associate image
        previews with video files.
        """
        return self.get_qualified_file_url('preview_file')

    def get_preview_file(self, default_name=None):
        if self.preview_file:
            return self.preview_file
        elif self.is_image():
            return self.file
        else:
            return self.get_icon_file(default_name=default_name)

    def get_icon_file(self, default_name=None):
        if not default_name:
            default_name = '_blank' if not self.is_folder() else '_folder'
        for finder in ICON_FINDERS:
            icon_file = finder.find(self, default_name=default_name)
            if icon_file:
                return icon_file

    def get_media_type_name(self):
        return MEDIA_TYPE_NAMES[self.media_type]

    def is_descendant_of(self, ancestor_nodes):
        if issubclass(ancestor_nodes.__class__, FileNode):
            ancestor_nodes = (ancestor_nodes,)
        # Check whether requested folder is in selected nodes
        is_descendant = self in ancestor_nodes
        if not is_descendant:
            # Check whether requested folder is a subfolder of selected nodes
            ancestors = self.get_ancestors(ascending=True)
            if ancestors:
                self.parent_folder = ancestors[0]
                for ancestor in ancestors:
                    if ancestor in ancestor_nodes:
                        is_descendant = True
                        break
        return is_descendant

    def get_descendant_count_display(self):
        if self.node_type == FileNode.FOLDER:
            return self.get_descendant_count()
        else:
            return ''
    get_descendant_count_display.short_description = _('Items')

    def has_metadata_including_descendants(self):
        if self.node_type == FileNode.FOLDER:
            count = self.get_descendants().filter(has_metadata=False).count()
            return count == 0
        else:
            return self.has_metadata
    has_metadata_including_descendants.short_description = _('Metadata')
    has_metadata_including_descendants.boolean = True

    def get_admin_url(self):
        """Returns the URL for viewing a FileNode in the admin."""

        if self.is_top_node():
            return reverse('admin:media_tree_filenode_changelist');
        if self.is_folder():
            return reverse('admin:media_tree_filenode_folder', args=(self.pk,));
        if self.pk:
            return reverse('admin:media_tree_filenode_change', args=(self.pk,));
        return ''
        # ID Path no longer necessary
        #url = reverse('admin:media_tree_filenode_changelist');
        #for node in self.get_node_path():
        #    if node.level >= 0:
        #        url += str(node.pk)+'/'
        #return url

    def get_admin_link(self):
        return force_unicode(mark_safe(u'%s: <a href="%s">%s</a>' %
            (capfirst(self._meta.verbose_name), self.get_admin_url(), self.__unicode__())))

    @staticmethod
    def get_mimetype(filename, fallback_type='application/x-unknown'):
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        if ext in EXT_MIMETYPE_MAP:
            return EXT_MIMETYPE_MAP[ext]
        else:
            mimetype, encoding = mimetypes.guess_type(filename, strict=False)
            if mimetype:
                return mimetype
            else:
                return fallback_type

    @property
    def mime_supertype(self):
        if self.mimetype:
            return self.mimetype.split('/')[0]

    @property
    def mime_subtype(self):
        if self.mimetype:
            return self.mimetype.split('/')[1]

    @staticmethod
    def mimetype_to_media_type(filename):
        mimetype = FileNode.get_mimetype(filename)
        if mimetype:
            if MIMETYPE_CONTENT_TYPE_MAP.has_key(mimetype):
                return MIMETYPE_CONTENT_TYPE_MAP[mimetype]
            else:
                type, subtype = mimetype.split('/')
                if MIMETYPE_CONTENT_TYPE_MAP.has_key(type):
                    return MIMETYPE_CONTENT_TYPE_MAP[type]
        return media_types.FILE

    # TODO: Move to extension
    def resolution_formatted(self):
        if self.width and self.height:
            return _(u'%(width)i×%(height)i') % {'width': self.width, 'height': self.height}
        else:
            return ''
    resolution_formatted.short_description = _('Resolution')
    resolution_formatted.admin_order_field = 'width'

    def make_name_unique_numbered(self, name, ext=''):
        # If file with same name exists in folder:
        qs = FileNode.objects.filter(parent=self.parent)
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        number = 1
        while qs.filter(name__exact=self.name).count() > 0:
            number += 1
            # rename using a number
            self.name = app_settings.MEDIA_TREE_NAME_UNIQUE_NUMBERED_FORMAT % {'name': name, 'number': number, 'ext': ext}

    def prevent_save(self):
        self.save_prevented = True

    def save(self, *args, **kwargs):

        if getattr(self, 'save_prevented', False):
            from django.core.exceptions import ValidationError
            raise ValidationError('Saving was presented for this FileNode object.')

        if self.node_type == FileNode.FOLDER:
            self.media_type = FileNode.FOLDER
            # Admin asserts that folder name is unique under parent. For other inserts:
            self.make_name_unique_numbered(self.name)
        else:
            # TODO: If file was not changed, this field will nevertheless be changed to
            # the name of the renamed file on disk. Do not do this unless a new file is being saved.
            file_changed = True
            if self.pk:
                try:
                    saved_instance = FileNode.objects.get(pk=self.pk)
                    if saved_instance.file == self.file:
                        file_changed = False
                except FileNode.DoesNotExist:
                    pass
            if file_changed:
                self.name = os.path.basename(self.file.name)
                # using os.path.splitext(), foo.tar.gz would become foo.tar_2.gz instead of foo_2.tar.gz
                split = multi_splitext(self.name)
                self.make_name_unique_numbered(split[0], split[1])

                # Determine various file parameters
                self.size = self.file.size
                self.extension = split[2].lstrip('.').lower()
                self.width, self.height = (None, None)

                self.file.name = self.name
                # TODO: A hash (created by storage class!) would be great because it would obscure file
                # names, but it would be inconvenient for downloadable files
                # self.file.name = str(uuid.uuid4()) + '.' + self.extension

                # Determine whether file is a supported image:
                try:
                    self.pre_save_image()
                except IOError:
                    self.media_type = FileNode.mimetype_to_media_type(self.name)

        self.slug = slugify(self.name)
        self.has_metadata = self.check_minimal_metadata()

        super(FileNode, self).save(*args, **kwargs)

    # TODO: Move to extension
    def pre_save_image(self):
        self.saved_image = Image.open(self.file)
        self.media_type = media_types.SUPPORTED_IMAGE
        self.width, self.height = self.saved_image.size

    def path(self):
        return self.file.path if self.file else ''

    def is_folder(self):
        return self.node_type == FileNode.FOLDER

    def is_file(self):
        return self.node_type == FileNode.FILE

    def is_image(self):
        return self.media_type == media_types.SUPPORTED_IMAGE

    def __unicode__(self):
        return self.name

    def check_minimal_metadata(self):
        result = (self.media_type in app_settings.MEDIA_TREE_METADATA_LESS_MEDIA_TYPES  \
            and self.name != '') or  \
            (self.title != '' or self.description != '' or  \
            self.override_alt != '' or self.override_caption != '')
        if result and self.node_type == FileNode.FOLDER and self.pk:
            result = self.has_metadata_including_descendants()
        return result

    def get_metadata_display(self, field_formats = {}, escape=True):
        """Returns object metadata that has been selected to be displayed to
        users, compiled as a string.
        """
        def field_format(field):
            if field in field_formats:
                return field_formats[field]
            return u'%s'
        t = join_formatted('', self.title, format=field_format('title'), escape=escape)
        t = join_formatted(t, self.description, u'%s: %s', escape=escape)
        if self.publish_author:
            t = join_formatted(t, self.author, u'%s' + u' – ' + u'Author: %s', u'%s' + u'Author: %s', escape=escape)
        if self.publish_copyright:
            t = join_formatted(t, self.copyright, u'%s, %s', escape=escape)
        if self.publish_date_time and self.date_time:
            date_time_formatted = dateformat.format(self.date_time, get_format('DATE_FORMAT'))
            t = join_formatted(t, date_time_formatted, u'%s (%s)', '%s%s', escape=escape)
        return t
    get_metadata_display.allow_tags = True

    def get_metadata_display_unescaped(self):
        """Returns object metadata that has been selected to be displayed to
        users, compiled as a string with the original field values left unescaped,
        i.e. they may contain tags.
        """
        return self.get_metadata_display(escape=False)
    get_metadata_display_unescaped.allow_tags = True

    def get_caption_formatted(self, field_formats = app_settings.MEDIA_TREE_METADATA_FORMATS):
        """Returns object metadata that has been selected to be displayed to
        users, compiled as a string including default formatting, for example
        bold titles.

        You can use this method in templates where you want to output image
        captions.
        """
        if self.override_caption != '':
            return self.override_caption
        else:
            return mark_safe(self.get_metadata_display(field_formats))
    get_caption_formatted.allow_tags = True
    get_caption_formatted.short_description = _('displayed metadata')

    @property
    def alt(self):
        """Returns object metadata suitable for use as the HTML ``alt``
        attribute. You can use this method in templates::

            <img src="{{ node.file.url }}" alt="{{ node.alt }}" />

        """
        if self.override_alt != '':
            return self.override_alt
        elif self.override_caption != '':
            return self.override_caption
        else:
            return self.get_metadata_display()

# Legacy mptt support
if ModelBase == models.Model:
    FileNode._mptt_meta = FileNode._meta
    try:
        mptt.register(FileNode,
            order_insertion_by=FileNode.MPTTMeta.order_insertion_by)
    except mptt.AlreadyRegistered:
        pass

from media_tree.utils import autodiscover_media_extensions
autodiscover_media_extensions()
