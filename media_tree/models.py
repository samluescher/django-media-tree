#encoding=utf-8

from media_tree import settings as app_settings, media_types
from media_tree.utils import multi_splitext, join_formatted
from media_tree.utils.staticfiles import get_icon_finders
from media_tree.utils import get_media_storage
from media_tree.utils.filenode import get_file_link

try:
    from mptt.models import MPTTModel as ModelBase
except ImportError:
    # Legacy mptt support
    import mptt
    from django.db.models import Model as ModelBase

from mptt.models import TreeForeignKey
from mptt.managers import TreeManager

from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import dateformat
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.conf import settings
from django.utils.formats import get_format
from django.db import models
from django.core.exceptions import ValidationError
from django import forms

from PIL import Image
import os
import mimetypes
import uuid

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    add_introspection_rules = False

MIMETYPE_CONTENT_TYPE_MAP = app_settings.MEDIA_TREE_MIMETYPE_CONTENT_TYPE_MAP
EXT_MIMETYPE_MAP = app_settings.MEDIA_TREE_EXT_MIMETYPE_MAP
STATIC_SUBDIR = app_settings.MEDIA_TREE_STATIC_SUBDIR

MEDIA_TYPE_NAMES = app_settings.MEDIA_TREE_CONTENT_TYPES
ICON_FINDERS = get_icon_finders(app_settings.MEDIA_TREE_ICON_FINDERS)


# http://adam.gomaa.us/blog/2008/aug/11/the-python-property-builtin/
def Property(func):
    return property(**func())


class FileNodeManager(models.Manager):
    """ 
    A special manager that enables you to pass a ``path`` argument to 
    :func:`get`, :func:`filter`, and :func:`exclude`, allowing you to 
    retrieve ``FileNode`` objects by their full node path, 
    which consists of the names of its parents and itself,
    e.g. ``"path/to/folder/readme.txt"``.
    """

    def __init__(self, filter_args={}):
        super(FileNodeManager, self).__init__()
        self.filter_args = filter_args

    def get_query_set(self):
        return super(FileNodeManager, self).get_query_set().filter(**self.filter_args)

    def get_filter_args_with_path(self, for_self, **kwargs):
        names = kwargs['path'].strip('/').split('/')
        names.reverse()
        parent_arg = '%s'
        new_kwargs = {}
        for index, name in enumerate(names):
            if not for_self or index > 0:
                parent_arg = 'parent__%s' % parent_arg
            new_kwargs[parent_arg % 'name'] = name
        new_kwargs[parent_arg % 'level'] = 0
        new_kwargs.update(kwargs)
        new_kwargs.pop('path')
        return new_kwargs

    def filter(self, *args, **kwargs):
        """
        Works just like the default Manager's :func:`filter` method, but
        you can pass an additional keyword argument named ``path`` specifying
        the full **path of the folder whose immediate child objects** you 
        want to retrieve, e.g. ``"path/to/folder"``. 
        """
        if 'path' in kwargs:
            kwargs = self.get_filter_args_with_path(False, **kwargs)
        return super(FileNodeManager, self).filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        """
        Works just like the default Manager's :func:`exclude` method, but
        you can pass an additional keyword argument named ``path`` specifying
        the full **path of the folder whose immediate child objects** you 
        want to exclude, e.g. ``"path/to/folder"``. 
        """
        if 'path' in kwargs:
            kwargs = self.get_filter_args_with_path(False, **kwargs)
        return super(FileNodeManager, self).exclude(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        Works just like the default Manager's :func:`get` method, but
        you can pass an additional keyword argument named ``path`` specifying
        the full path of the object you want to retrieve, e.g.
        ``"path/to/folder/readme.txt"``. 
        """
        if 'path' in kwargs:
            kwargs = self.get_filter_args_with_path(True, **kwargs)
        return super(FileNodeManager, self).get(
            *args, **kwargs)


class MultipleChoiceCommaSeparatedIntegerField(models.Field):
    u'''
    Save a list of integers in a MultipleChoiceCommaSeparatedIntegerField.

    In the django model object the column is a list of strings.
    '''
    __metaclass__=models.SubfieldBase
    SPLIT_CHAR=u','
    def __init__(self, *args, **kwargs):
        self.internal_type=kwargs.pop('internal_type', 'CharField') # or TextField
        super(MultipleChoiceCommaSeparatedIntegerField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None   \
            or not len(value):
                return []
        if not isinstance(value, list):
            value = value.split(self.SPLIT_CHAR)
        return [int(v) for v in value]

    def get_internal_type(self):
        return self.internal_type

    def get_db_prep_lookup(self, lookup_type, value):
        # SQL WHERE
        raise NotImplementedError()

    def get_db_prep_save(self, value, *args, **kwargs):
        return self.SPLIT_CHAR.join(['%i' % v for v in value])

    def formfield(self, **kwargs):
        assert not kwargs, kwargs
        return forms.MultipleChoiceField(choices=self.choices, widget=forms.CheckboxSelectMultiple  \
            , required=False)

    def validate(self, value, model_instance):
        """
        Validates value and throws ValidationError. Subclasses should override
        this to provide validation logic.
        """
        if not self.editable:
            # Skip validation for non-editable fields.
            return
        if self._choices and value:
            print value
            l = value
            if type(value) != list:
                l = [ value ]
            for v in value:
                for option_key, option_value in self.choices:
                    if isinstance(option_value, (list, tuple)):
                        # This is an optgroup, so look inside the group for options.
                        for optgroup_key, optgroup_value in option_value:
                            if v == optgroup_key:
                                return
                    elif v == option_key:
                        return
                raise ValidationError(self.error_messages['invalid_choice'] % {'value': value})

        if value is None and not self.null:
            raise ValidationError(self.error_messages['null'])

        if not self.blank and value in validators.EMPTY_VALUES:
            raise ValidationError(self.error_messages['blank'])

        return super(MultipleChoiceCommaSeparatedIntegerField, self).validate(value, model_instance)

if add_introspection_rules:
    add_introspection_rules([], ["^media_tree\.models\.MultipleChoiceCommaSeparatedIntegerField"])


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

    You can access the actual media associated to a ``FileNode`` model instance 
    using the following fields:

    .. role:: descname(literal)
       :class: descname 

    :descname:`file`
        The actual media file

    :descname:`preview_file`
        An optional image file that will be used for previews. This is useful 
        for visual media that PIL cannot read, such as video files.

    These fields are of the class ``FileField``. Please see :ref:`configuration`
    for information on how to configure storage and media backend classes. By
    default, media files are stored in a subfolder ``uploads`` under your media
    root.
    """

    FOLDER = media_types.FOLDER
    """ The constant denoting a folder node, used for the :attr:`node_type` attribute. """

    FILE = media_types.FILE
    """ The constant denoting a file node, used for the :attr:`node_type` attribute. """

    STORAGE = get_media_storage()

    tree = TreeManager()
    """ MPTT tree manager """

    objects = FileNodeManager()
    """ 
    An instance of the :class:`FileNodeManager` class, providing methods for retrieving ``FileNode`` objects by their full node path.
    """

    published_objects = FileNodeManager({'published': True})
    """ 
    A special manager with the same features as :attr:`objects`, but only displaying currently
    published objects.
    """

    folders = FileNodeManager({'node_type': FOLDER})
    """ 
    A special manager with the same features as :attr:`objects`, but only displaying folder nodes.
    """

    files = FileNodeManager({'node_type': FILE})
    """ 
    A special manager with the same features as :attr:`objects`, but only displaying file nodes,
    no folder nodes.
    """

    # FileFields -- have no docstring since Sphinx cannot access these attributes
    file = models.FileField(_('file'), upload_to=app_settings.MEDIA_TREE_UPLOAD_SUBDIR, null=True, storage=STORAGE)
    # The actual media file 
    preview_file = models.ImageField(_('preview'), upload_to=app_settings.MEDIA_TREE_PREVIEW_SUBDIR, blank=True, null=True, help_text=_('Use this field to upload a preview image for video or similar media types.'), storage=STORAGE)
    # An optional image file that will be used for previews. This is useful for video files. 

    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('folder'), limit_choices_to={'node_type': FOLDER})
    """ The parent (folder) object of the node. """
    
    node_type = models.IntegerField(_('node type'), choices = ((FOLDER, 'Folder'), (FILE, 'File')), editable=False, blank=False, null=False)
    """ Type of the node (:attr:`FileNode.FILE` or :attr:`FileNode.FOLDER`) """
    media_type = models.IntegerField(_('media type'), choices = app_settings.MEDIA_TREE_CONTENT_TYPE_CHOICES, blank=True, null=True, editable=False)
    """ Media type, i.e. broad category of the kind of media """
    allowed_child_node_types = MultipleChoiceCommaSeparatedIntegerField(_('allowed '), choices = ((FILE, _('file')), (FOLDER, _('folder'))), blank=True, null=True, max_length=64, help_text=_('If none selected, all are allowed.'))
    """ Media type, i.e. broad category of the kind of media """
    published = models.BooleanField(_('is published'), blank=True, default=True)
    """ Publish date and time """
    mimetype = models.CharField(_('mimetype'), max_length=64, null=True, editable=False)
    """ The mime type of the media file """
    name = models.CharField(_('name'), max_length=255, null=True)
    """ Name of the file or folder """
    title = models.CharField(_('title'), max_length=255, default='', null=True, blank=True)
    """ Title for the file """
    description = models.TextField(_('description'), default='', null=True, blank=True)
    """ Description for the file """
    author = models.CharField(_('author'), max_length=255, default='', null=True, blank=True)
    """ Author name of the file """
    publish_author = models.BooleanField(_('publish author'), default=False)
    """ Flag to toggle whether the author name should be displayed """
    copyright = models.CharField(_('copyright'), max_length=255, default='', null=True, blank=True)
    """ Copyright information for the file """
    publish_copyright = models.BooleanField(_('publish copyright'), default=False)
    """ Flag to toggle whether copyright information should be displayed """
    date_time = models.DateTimeField(_('date/time'), null=True, blank=True)
    """ Date and time information for the file (authoring or publishing date) """
    publish_date_time = models.BooleanField(_('publish date/time'), default=False)
    """ Flag to toggle whether date and time information should be displayed """
    keywords = models.CharField(_('keywords'), max_length=255, null=True, blank=True)
    """ Keywords for the file """
    override_alt = models.CharField(_('alternative text'), max_length=255, default='', null=True, blank=True, help_text=_('If you leave this blank, the alternative text will be compiled automatically from the available metadata.'))
    """ Alt text override. If empty, the alt text will be compiled from the all metadata that is available and flagged to be displayed. """
    override_caption = models.CharField(_('caption'), max_length=255, default='', null=True, blank=True, help_text=_('If you leave this blank, the caption will be compiled automatically from the available metadata.'))
    """ Caption override. If empty, the caption will be compiled from the all metadata that is available and flagged to be displayed. """

    has_metadata = models.BooleanField(_('metadata entered'), editable=False)
    """ Flag specifying whether the absolute minimal metadata was entered """

    extension = models.CharField(_('type'), default='', max_length=10, null=True, editable=False)
    """ File extension, lowercase """
    size = models.IntegerField(_('size'), null=True, editable=False)
    """ File size in bytes """
    # TODO: Refactor PIL stuff, width|height as extension?
    width = models.IntegerField(_('width'), null=True, blank=True, help_text=_('Detected automatically for supported images'))
    """ For images: width in pixels """
    height = models.IntegerField(_('height'), null=True, blank=True, help_text=_('Detected automatically for supported images'))
    """ For images: height in pixels """

    slug = models.CharField(_('slug'), max_length=255, null=True, editable=False)
    """ Slug for the object """
    is_default = models.BooleanField(_('use as default object for folder'), blank=True, default=False, help_text=_('The default object of a folder can be used for folder previews etc.'))
    """ Flag whether the file is the default file in its parent folder """

    created = models.DateTimeField(_('created'), auto_now_add=True, editable=False)
    """ Date and time when object was created """
    modified = models.DateTimeField(_('modified'), auto_now=True, editable=False)
    """ Date and time when object was last modified """

    created_by = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='created_by', verbose_name = _('created by'), editable=False)
    """ User that created the object """
    modified_by = models.ForeignKey(get_user_model(), null=True, blank=True, related_name='modified_by', verbose_name = _('modified by'), editable=False)
    """ User that last modified the object """

    position = models.IntegerField(_('position'), default=0, blank=True)
    """ Position of the file among its siblings, for manual ordering """

    extra_metadata = models.TextField(_('extra metadata'), editable=None)
    """ Extra metadata """


    is_ancestor_being_updated = False


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
        elif self.is_web_image():
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

    def get_path(self):
        path = ''
        for name in [node.name for node in self.get_ancestors()]:
            path = '%s%s/' % (path, name) 
        return '%s%s' % (path, self.name)

    def get_admin_url(self, query_params=None, use_path=False):
        """Returns the URL for viewing a FileNode in the admin."""

        if not query_params:
            query_params = {}

        url = ''
        if self.is_top_node():
            url = reverse('admin:media_tree_filenode_changelist');
        elif use_path and (self.is_folder() or self.pk):
            url = reverse('admin:media_tree_filenode_open_path', args=(self.get_path(),));
        elif self.is_folder():
            url = reverse('admin:media_tree_filenode_changelist');
            query_params['folder_id'] = self.pk
        elif self.pk:
            return reverse('admin:media_tree_filenode_change', args=(self.pk,));

        if len(query_params):
            params = ['%s=%s' % (key, value) for key, value in query_params.items()]
            url = '%s?%s' % (url, "&".join(params))

        return url

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
                    self.media_type = None
                    self.pre_save_image()
                except IOError:
                    pass
                if not self.media_type:
                    self.media_type = FileNode.mimetype_to_media_type(self.name)

        self.slug = slugify(self.name)
        self.has_metadata = self.check_minimal_metadata()

        super(FileNode, self).save(*args, **kwargs)

    # TODO: Move to extension
    def pre_save_image(self):
        if self.extension in app_settings.MEDIA_TREE_VECTOR_EXTENSIONS:
            self.media_type = media_types.VECTOR_IMAGE
        else:
            self.saved_image = Image.open(self.file)
            self.media_type = media_types.SUPPORTED_IMAGE
            self.width, self.height = self.saved_image.size

    def file_path(self):
        return self.file.path if self.file else ''

    def is_folder(self):
        return self.node_type == FileNode.FOLDER

    def is_file(self):
        return self.node_type == FileNode.FILE

    def is_image(self):
        return self.media_type == media_types.SUPPORTED_IMAGE

    def is_web_image(self):
        return self.media_type in (media_types.SUPPORTED_IMAGE, media_types.VECTOR_IMAGE)

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
        i.e. the original field values may contain tags.
        """
        return self.get_metadata_display(escape=False)
    get_metadata_display_unescaped.allow_tags = True

    def get_caption_formatted(self, field_formats = app_settings.MEDIA_TREE_METADATA_FORMATS, escape=True):
        """Returns object metadata that has been selected to be displayed to
        users, compiled as a string including default formatting, for example
        bold titles.

        You can use this method in templates where you want to output image
        captions.
        """
        if self.override_caption != '':
            return self.override_caption
        else:
            return mark_safe(self.get_metadata_display(field_formats, escape=escape))
    get_caption_formatted.allow_tags = True
    get_caption_formatted.short_description = _('displayed metadata')

    def get_caption_formatted_unescaped(self):
        """Returns object metadata that has been selected to be displayed to
        users, compiled as a string with the original field values left unescaped,
        i.e. the original field values may contain tags.
        """
        return self.get_caption_formatted(escape=False)
    get_caption_formatted_unescaped.allow_tags = True
    get_caption_formatted_unescaped.short_description = _('displayed metadata')

    @property
    def alt(self):
        """Returns object metadata suitable for use as the HTML ``alt``
        attribute. You can use this method in templates::

            <img src="{{ node.file.url }}" alt="{{ node.alt }}" />

        """
        if self.override_alt != '' and self.override_alt is not None:
            return self.override_alt
        elif self.override_caption != '' and self.override_caption is not None:
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
