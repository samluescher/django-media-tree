from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from media_tree import media_types


MEDIA_TREE_MEDIA_BACKENDS = getattr(settings, 'MEDIA_TREE_MEDIA_BACKENDS', ())
"""
A tuple of media backends for thumbnail generation and other media-related
tasks.

Currently, the only supported backend is
``media_tree.contrib.media_backends.easy_thumbnails.EasyThumbnailsBackend``,
which depends on ``easy_thumbnails`` to be installed. Please refer to
:ref:`media-backends` for more information.
"""

MEDIA_TREE_LIST_DISPLAY = ('browse_controls', 'size_formatted', 'extension', 'resolution_formatted', 'get_descendant_count_display', 'modified', 'modified_by', 'metadata_check', 'position', 'node_tools')
"""
A tuple containing the columns that should be displayed in the ``FileNodeAdmin``.
Note that the ``browse_controls`` column is necessary for the admin to function
properly.
"""

MEDIA_TREE_LIST_FILTER = ('media_type', 'extension', 'has_metadata')
"""
A tuple containing the fields that nodes can be filtered by in the
``FileNodeAdmin``.
"""

#MEDIA_TREE_LIST_DISPLAY_LINKS = ('name',)

MEDIA_TREE_SEARCH_FIELDS = ('name', 'title', 'description', 'author', 'copyright', 
    'override_caption', 'override_alt')
"""
A tuple containing the fields that nodes can be searched by in the
``FileNodeAdmin``.
"""

MEDIA_TREE_UPLOAD_SUBDIR = 'upload'
"""
The name of the folder under your ``MEDIA_ROOT`` where media files are stored.
"""

MEDIA_TREE_PREVIEW_SUBDIR = 'upload/_preview'
"""
The name of the folder under your ``MEDIA_ROOT`` where cached versions of media
files, e.g. thumbnails, are stored.
"""

MEDIA_TREE_STATIC_SUBDIR = 'media_tree'

MEDIA_TREE_ICON_DIRS = (
    'media_tree/img/icons/mimetypes',
)    
"""
A tuple containing all icon directories. See :ref:`install-icon-sets`
for more information.
"""

MEDIA_TREE_ICON_FINDERS = (
    'media_tree.utils.staticfiles.MimetypeStaticIconFileFinder',
)

MEDIA_TREE_THUMBNAIL_SIZES = {
    'small': (80, 80),
    'default': (100, 100),
    'medium': (250, 250),
    'large': (400, 400),
    'full': None, # None means: use original size
}
"""
A dictionary of default thumbnail sizes. You can pass the dictionary key to the
``thumbnail`` templatetag instead of a numeric size.

Default::

    {
        'small': (80, 80),
        'default': (100, 100),
        'medium': (250, 250),
        'large': (400, 400),
        'full': None, # None means: use original size
    }

"""

MEDIA_TREE_ALLOWED_FILE_TYPES = (
    'aac', 'ace', 'ai', 'aiff', 'avi', 'bmp', 'dir', 'doc', 'docx', 'dmg', 'eps', 'fla', 'flv', 
    'gif', 'gz', 'hqx', 'htm', 'html', 'ico', 'indd', 'inx', 'jpg', 'jar', 'jpeg', 'md', 'mov', 
    'mp3', 'mp4', 'mpc', 'mkv', 'mpg', 'mpeg', 'ogg', 'odg', 'odf', 'odp', 'ods', 'odt', 'otf', 
    'pdf', 'png', 'pps', 'ppsx', 'ps', 'psd', 'rar', 'rm', 'rtf', 'sit', 'swf', 'tar', 'tga', 
    'tif', 'tiff', 'ttf', 'txt', 'wav', 'wma', 'wmv', 'xls', 'xlsx', 'xml', 'zip'
)
"""
A whitelist of file extensions that can be uploaded. By default, this is a
comprehensive list of many common media file extensions that shouldn't pose a
security risk.

.. Warning::
   Be careful when adding potentially unsafe file extensions to this setting,
   such as executables or scripts, as this possibly opens a door to attackers.
"""

MEDIA_TREE_THUMBNAIL_EXTENSIONS = ('jpg', 'png')
"""
Default: ``('jpg', 'png')``

A tuple of image extensions used for thumbnail files. Note that ``png`` is in
there since you might typically want to preserve the file type of PNG images
instead of converting them to JPG.
"""

MEDIA_TREE_FILE_SIZE_LIMIT = 1000000000 # 1 GB
"""
Default: 1 GB

Maximum file size for uploaded files.
"""

MEDIA_TREE_SWFUPLOAD = True
"""
Toggles support for SWFUpload on or off. See :ref:`install-swfupload` for more
information.
"""

MEDIA_TREE_GLOBAL_THUMBNAIL_OPTIONS = {
    'sharpen': None, # None means enabled 
}
"""
A dictionary of options that should be applied by default when generating
thumbnails. You might use this, for instance, to sharpen all thumbnails.
"""

MEDIA_TREE_METADATA_FORMATS = {
    'title': '<strong>%s</strong>'
}

MEDIA_TREE_ORDERING_DEFAULT = ['name']

"""
List of mimetypes not convered by the `mimetypes` Python module (for instance, .flv is not guessed
by `guess_mimetype`.)
"""
MEDIA_TREE_EXT_MIMETYPE_MAP = {
    'flv': 'video/x-flv',
}

MEDIA_TREE_MPTT_ADMIN_LEVEL_INDENT = getattr(settings, 'MEDIA_TREE_MPTT_ADMIN_LEVEL_INDENT', 25)

MEDIA_TREE_MIMETYPE_CONTENT_TYPE_MAP = {
    'application/octet-stream': media_types.FILE,
    'application/zip': media_types.ARCHIVE,
    'application/x-rar-compressed': media_types.ARCHIVE,
    'application/x-tar': media_types.ARCHIVE,
    'application/x-ace-compressed': media_types.ARCHIVE,
    'application': media_types.DOCUMENT,
    'audio': media_types.AUDIO,
    'image': media_types.IMAGE,
    'text': media_types.TEXT,
    'video': media_types.VIDEO,
}

MEDIA_TREE_CONTENT_TYPE_CHOICES = (
    (media_types.FOLDER, _('folder')),
    (media_types.ARCHIVE, _('archive')),
    (media_types.AUDIO, _('audio')),
    (media_types.DOCUMENT, _('document')),
    (media_types.IMAGE, _('image')),
    (media_types.SUPPORTED_IMAGE, _('web image')),
    (media_types.TEXT, _('text')),
    (media_types.VIDEO, _('video')),
    (media_types.FILE, _('other')),
)

MEDIA_TREE_CONTENT_TYPES = dict(MEDIA_TREE_CONTENT_TYPE_CHOICES)

MEDIA_TREE_LEVEL_INDICATOR = unichr(0x00A0) * 3;

MEDIA_TREE_NAME_UNIQUE_NUMBERED_FORMAT = '%(name)s_%(number)i%(ext)s'
