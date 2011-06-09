#encoding=utf-8
from django.db import models
import mptt
from PIL import Image
import os
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django.template.defaultfilters import slugify
from django.utils import dateformat
from media_tree import app_settings, media_types
from media_tree.utils import multi_splitext, IconFile
import mimetypes
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from media_tree.templatetags.filesize import filesize as format_filesize
from django.conf import settings
from django.utils.formats import get_format
from copy import copy
import uuid

MIMETYPE_CONTENT_TYPE_MAP = app_settings.get('MEDIA_TREE_MIMETYPE_CONTENT_TYPE_MAP')
EXT_MIMETYPE_MAP = app_settings.get('MEDIA_TREE_EXT_MIMETYPE_MAP')
FILE_ICONS = app_settings.get('MEDIA_TREE_FILE_ICONS')
MEDIA_SUBDIR = app_settings.get('MEDIA_TREE_MEDIA_SUBDIR')
ICONS_DIR = app_settings.get('MEDIA_TREE_ICONS_DIR')
MEDIA_TYPE_NAMES = app_settings.get('MEDIA_TREE_CONTENT_TYPES')

def join_phrases(text, new_text, prepend=', ', append='', compare_text=None, else_prepend='', else_append='', if_empty=False):
    if new_text != '' or if_empty:
        if compare_text == None:
            compare_text = text
        if compare_text != '':
            text += prepend
        else:
            text += else_prepend
        text += new_text
        if compare_text != '':
            text += append
        else:
            text += else_append
    return text


# http://adam.gomaa.us/blog/2008/aug/11/the-python-property-builtin/
def Property(func):
    return property(**func())


from django.db.models import permalink
class FileNode(models.Model):

    FOLDER = media_types.FOLDER
    FILE = media_types.FILE

    node_type = models.IntegerField(_('node type'), choices = ((FOLDER, 'Folder'), (FILE, 'File')), editable=False)
    media_type = models.IntegerField(_('media type'), choices = app_settings.get('MEDIA_TREE_CONTENT_TYPE_CHOICES'), blank=True, null=True, editable=False)
    file = models.FileField(_('file'), upload_to=app_settings.get('MEDIA_TREE_UPLOAD_SUBDIR'), null=True)
    preview_file = models.ImageField(_('preview'), upload_to=app_settings.get('MEDIA_TREE_PREVIEW_SUBDIR'), blank=True, null=True, help_text=_('Use this field to upload a preview image for video or similar media types.'))
    published = models.BooleanField(_('is published'), blank=True, default=True, editable=False)

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
    width = models.IntegerField(_('width'), null=True, blank=True, help_text=_('Detected automatically for supported images'))
    height = models.IntegerField(_('height'), null=True, blank=True, help_text=_('Detected automatically for supported images'))
    created = models.DateTimeField(_('created'), auto_now_add=True, editable=False)
    modified = models.DateTimeField(_('modified'), auto_now=True, editable=False)

    parent = models.ForeignKey('self', null=True, blank=True, related_name='children_set', verbose_name = _('Folder'), editable=False)
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
        
    @staticmethod
    def get_top_node():
        return FileNode(name=_('Media Objects'), level=-1)

    def is_top_node(self):
        return self.level == -1

    # Workaround for http://code.djangoproject.com/ticket/11058
    def admin_preview(self):
        pass

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
            # not possible to order the queryset returned by get_children() by is_default
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
        """
        Returns a fully qualified URL for a file field, including protocol, domain and port.
        In most cases, you can just use `file_field.url` instead, which (depending on your 
        `MEDIA_URL`) may or may not contain the domain. In some cases however, you always
        need a fully qualified URL. This includes, for instance, embedding a flash video
        player from a remote domain and passing it a video URL.
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
        return self.get_qualified_file_url('preview_file')

    def get_preview_file(self):
        if self.preview_file:
            return self.preview_file
        elif self.is_image():
            return self.file
        else:
            return self.get_icon_file()

    def get_icon_file(self):
        if self.extension in FILE_ICONS:
            basename = FILE_ICONS[self.extension]
        else:
            basename = FILE_ICONS[self.media_type]
        return IconFile(self, os.path.join(ICONS_DIR, basename))

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

    @staticmethod
    def __get_list(nodes, filter_media_types=None, exclude_media_types=None, filter=None, ordering=None, processors=None, list_method='append', max_depth=None, max_nodes=None, _depth=1, _node_count=0):

        if isinstance(nodes, models.query.QuerySet):
            # pre-filter() and exclude() on queryset for fewer iterations  
            if filter_media_types:
                nodes = nodes.filter(media_type__in=tuple(filter_media_types)+(FileNode.FOLDER,))
            if exclude_media_types:
                for exclude_media_type in exclude_media_types:
                    if exclude_media_type != FileNode.FOLDER:
                        nodes = nodes.exclude(media_type__exact=exclude_media_type)
            if filter:
                nodes = nodes.filter(**filter)
            if ordering:
                nodes = nodes.order_by(*ordering)

        result_list = []
        if max_depth is None or _depth <= max_depth: 
            for node in nodes:
                if max_nodes and _node_count > max_nodes:
                    break
                # recursively get child nodes
                if node.node_type == FileNode.FOLDER and node.get_descendant_count() > 0:
                    child_nodes = FileNode.__get_list(node.get_children().all(), filter_media_types=filter_media_types, exclude_media_types=exclude_media_types, 
                        filter=filter, processors=processors, list_method=list_method, max_depth=max_depth, max_nodes=max_nodes, 
                        _depth=_depth + 1, _node_count=_node_count)
                    child_count = len(child_nodes)
                else:
                    child_count = 0
                # add node itself if it matches the filter criteria, or, if result is a nested list
                # (`list_method == 'append'`), it must include folders in order to make sense,
                # but folders will only be added if they have any descendants matching the filter criteria
                if ((not filter_media_types or node.media_type in filter_media_types) \
                    and (not exclude_media_types or not node.media_type in exclude_media_types)) \
                    or (child_count > 0 and list_method == 'append' and (max_depth is None or _depth < max_depth)):
                        _node_count += 1
                        if processors:
                            node_copy = copy(node)
                            for processor in processors:
                                node_copy = processor(node_copy)
                            if node_copy != None:
                                result_list.append(node_copy)
                        else:
                            result_list.append(node)
                # add child nodes using appropriate list method. `append` will result in a nested list,
                # while `extend` produces a merged (flat) list.
                if child_count > 0:
                    _node_count += child_count
                    method = getattr(result_list, list_method)
                    method(child_nodes)
        return result_list

    @staticmethod
    def get_merged_list(nodes, filter_media_types=None, exclude_media_types=None, filter=None, ordering=None, processors=None, max_depth=None, max_nodes=None):
        """
        Returns a nested list of nodes, applying optional filters and processors to each node.
        Nested means that the resulting list will be multi-dimensional, i.e. each item in the list
        that is a folder containing child nodes will be followed by a sub-list containing those
        child nodes.
        
        Example:
            
            [
                <FileNode: Empty folder>, 
                <FileNode: Photo folder>, 
                    [<FileNode: photo1.jpg>, <FileNode: photo2.jpg>],
                <FileNode: file.txt>
            ]
        
        :param nodes: A queryset or list of FileNode objects
        :filter_media_types: A list of media types to include in the resulting list, e.g. [FileNode.DOCUMENT] 
        :exclude_media_types: A list of media types to exclude from the resulting list
        :filter: A dictionary of kwargs for the filter() method if `nodes` is a queryset
        :processors: A list of callables to be applied to each node, e.g. [force_unicode] if you want the list to contain strings instead of FileNode objects
        :max_depth: Can be used to limit the recursion depth (unlimited by default)
        :max_nodes: Can be used to limit the number of items in the list (unlimited by default)
        """
        return FileNode.__get_list(nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types, 
            filter=filter, ordering=ordering, processors=processors, list_method='extend', max_depth=max_depth, max_nodes=max_nodes)

    @staticmethod
    def get_nested_list(nodes, filter_media_types=None, exclude_media_types=None, filter=None, ordering=None, processors=None, max_depth=None, max_nodes=None):
        """
        Almost the same as `get_merged_list`, but returns a flat or one-dimensional list.
        Using the same queryset as in the example for `get_merged_list`, this method would return:
        
            [
                <FileNode: Empty folder>, 
                <FileNode: Photo folder>, 
                <FileNode: photo1.jpg>,
                <FileNode: photo2.jpg>,
                <FileNode: file.txt>
            ]
        """
        return FileNode.__get_list(nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types, 
            filter=filter, ordering=ordering, processors=processors, list_method='append', max_depth=max_depth, max_nodes=max_nodes)
                            
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
    has_metadata_including_descendants.short_description = _('Ready')
    has_metadata_including_descendants.boolean = True

    def get_admin_url(self):
        return reverse('admin:media_tree_filenode_change', args=(self.pk,));
        
        # ID Path no longer necessary 
        #url = reverse('admin:media_tree_filenode_changelist');
        #for node in self.get_node_path():
        #    if node.level >= 0:
        #        url += str(node.pk)+'/'
        #return url

    def get_admin_link(self):
        return force_unicode(mark_safe(u'%s: <a href="%s">%s</a>' % 
            (capfirst(self._meta.verbose_name), self.get_admin_url(), self.__unicode__())))

    def get_file_link(node, use_metadata=False, include_size=False, include_extension=False):
        link_text = None
        if use_metadata:
            link_text = node.get_metadata()
        if not link_text:
            link_text = node.__unicode__()
        if node.node_type == FileNode.FOLDER:
            return mark_safe(u'<span class="folder">%s</span>' % link_text)
        else:
            extra = ''
            if include_extension:
                extra = '<span class="file-extension">%s</span>' % node.extension.upper()
            if include_size:
                if extra != '':
                    extra += ', '
                extra += '<span class="file-size">%s</span>' % format_filesize(node.size)
            if extra:
                extra = ' (%s)' % extra
            return force_unicode(mark_safe(u'<a class="file '+node.extension+'" href="%s">%s</a>%s' % 
                (node.file.url, link_text, extra)))

    @staticmethod
    def get_mimetype(filename):
        ext = os.path.splitext(filename)[1].lstrip('.').lower()
        if ext in EXT_MIMETYPE_MAP:
            return EXT_MIMETYPE_MAP[ext]
        else:
            type, encoding = mimetypes.guess_type(filename, strict=False)
            return type
    
    def mimetype(self):
        return FileNode.get_mimetype(self.name)
    
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
            self.name = app_settings.get('MEDIA_TREE_NAME_UNIQUE_NUMBERED_FORMAT') % {'name': name, 'number': number, 'ext': ext}

    def prevent_save(self):
        self.save_prevented = True

    def save(self, *args, **kwargs):
        
        if getattr(self, 'save_prevented', False):
            from django.core.exceptions import ValidationError
            raise ValidationError('Saving was presented for this FileNode object.')
        
        if not self.node_type:
            from django.core.exceptions import ValidationError
            raise ValidationError('node_type needs to be set before saving FileNode.')

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
                # TODO: A hash would be great, but would be inconvenient for downloadable files
                #self.file.name = str(uuid.uuid4()) + '.' + self.extension

                # Determine whether file is a supported image:
                try:
                    self.pre_save_image()
                except IOError:
                    self.media_type = FileNode.mimetype_to_media_type(self.name)

        self.slug = slugify(self.name)
        self.has_metadata = self.check_minimal_metadata()
        
        super(FileNode, self).save(*args, **kwargs)

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
        result = (self.node_type == FileNode.FOLDER and self.name != '') or (self.title != '' or self.description != '' or self.override_alt != '')
        if result and self.node_type == FileNode.FOLDER and self.pk:
            result = self.has_metadata_including_descendants()
        return result

    def get_metadata(self, title_prepend='', title_append=''):
        t = join_phrases('', self.title, else_prepend=title_prepend, else_append=title_append);
        t = join_phrases(t, self.description, ugettext(': '))
        if self.publish_author:
            t = join_phrases(t, '', ugettext(u' – ')+ugettext('Author: %s') % self.author, compare_text=self.author, if_empty=True)
        if self.publish_copyright:
            t = join_phrases(t, self.copyright, ugettext(', '), compare_text=self.author, else_prepend=' ')
        if self.publish_date_time and self.date_time:
            date_time_formatted = dateformat.format(self.date_time, get_format('DATE_FORMAT'))
            t = join_phrases(t, date_time_formatted, ' (', ')');
        return t

    # TODO Problem: If rendered |safe, all illegal tags in title / description will be output – clean tags on clean()?
    def caption(self):
        if self.override_caption != '':
            return self.override_caption
        else:
            return self.get_metadata('<strong>', '</strong>')
    caption.allow_tags = True
    caption.short_description = _('displayed metadata')

    @property
    def alt(self):
        if self.override_alt != '':
            return self.override_alt
        else:
            return self.get_metadata()

try:
    # TODO If file name changes, order is not updated. See http://code.google.com/p/django-mptt/issues/detail?id=41
    mptt.register(FileNode, order_insertion_by=['name'])
except mptt.AlreadyRegistered:
    pass


from media_tree.utils import autodiscover_media_extensions
autodiscover_media_extensions()



MEDIA_EXTENDERS = None
#MEDIA_EXTENDERS = app_settings.get('MEDIA_TREE_MEDIA_EXTENDERS')
if MEDIA_EXTENDERS:
    from media_tree.utils import import_extender
    from media_tree import media_extenders
    for path in MEDIA_EXTENDERS:
        media_extenders.register(import_extender(path))
