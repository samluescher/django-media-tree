.. _configuration:

Configuring Media Tree
**********************

The following settings can be specified in your Django project's settings
module.


``MEDIA_TREE_MEDIA_BACKENDS``
    A tuple of media backends for thumbnail generation and other media-related
    tasks, i.e. a list of wrappers for the third-party applications that take
    care of this.

    .. Note::
       Please refer to the :ref:`installation instructions
       <configuring-media-backends>` for information on how to configure
       supported media backends.
    
    For general information on media backends, see :ref:`media-backends` for
    more information.


``MEDIA_TREE_LIST_DISPLAY``
    A tuple containing the columns that should be displayed in the
    ``FileNodeAdmin``. Note that the ``browse_controls`` column is necessary for
    the admin to function properly.


``MEDIA_TREE_LIST_FILTER``
    A tuple containing the fields that nodes can be filtered by in the
    ``FileNodeAdmin``.


``MEDIA_TREE_SEARCH_FIELDS``
    A tuple containing the fields that nodes can be searched by in the
    ``FileNodeAdmin``.


``MEDIA_TREE_UPLOAD_SUBDIR``
    Default: ``'upload'``

    The name of the folder under your ``MEDIA_ROOT`` where media files are stored.


``MEDIA_TREE_PREVIEW_SUBDIR``
    Default: ``'upload/_preview'``
    
    The name of the folder under your ``MEDIA_ROOT`` where cached versions of
    media files, e.g. thumbnails, are stored.


``MEDIA_TREE_ICON_DIRS``
    Default::
    
        (
            'media_tree/img/icons/mimetypes',
        )    

    A tuple containing all icon directories. See :ref:`install-icon-sets`
    for more information.


``MEDIA_TREE_THUMBNAIL_SIZES``
    A dictionary of default thumbnail sizes. You can pass the dictionary key to
    the ``thumbnail`` templatetag instead of a numeric size.

    Default::
    
        {
            'small': (80, 80),
            'default': (100, 100),
            'medium': (250, 250),
            'large': (400, 400),
            'full': None, # None means: use original size
        }


``MEDIA_TREE_ALLOWED_FILE_TYPES``
    A whitelist of file extensions that can be uploaded. By default, this is a
    comprehensive list of many common media file extensions that generally
    shouldn't pose a security risk.
    
    .. Warning::
       Just because a file extension may be considered “safe”, there is
       absolutely no guarantee that a skilled attacker couldn't find an exploit.
       Only allow people you trust to upload files to your webserver.
       Be careful when adding potentially unsafe file extensions to this
       setting, such as executables or scripts, as this possibly opens a door to
       attackers. 


``MEDIA_TREE_THUMBNAIL_EXTENSIONS``
    Default: ``('jpg', 'png')``

    A tuple of image extensions used for thumbnail files. Note that ``png`` is
    in there since you might typically want to preserve the file type of PNG
    images instead of converting them to JPG.


``MEDIA_TREE_FILE_SIZE_LIMIT``
    Default: ``1000000000 # 1 GB``

    Maximum file size for uploaded files.


``MEDIA_TREE_SWFUPLOAD``
    Default: ``True``
    
    Toggles support for SWFUpload on or off. See
    :ref:`Installing SWFUpload <install-swfupload>` for more information.


``MEDIA_TREE_GLOBAL_THUMBNAIL_OPTIONS``
    A dictionary of options that should be applied by default when generating
    thumbnails. You might use this, for instance, to sharpen all thumbnails.
