Django Media Tree
=================

A Django app for managing your site media (images, audio, video, archives etc.) and organizing it in one central, tree-based location.

__Features__:

* Enables you to organize all of your site media in nested folders  
* Supports various media types (images, audio, video, archives etc.) 
* Multi-upload queue with progress indicators (using SWFUpload)
* Add metadata to all media for accessible web sites 
* Integration with [Django CMS](http://www.django-cms.org). Plugins include: Image, slideshow, gallery, download list – roll your own! 
* Plugin interface based on Django's admin actions, allowing you to write your own batch-processing actions 
* Extension interface for custom media types with extra fields, based on signals
* Uses mptt to efficiently model a file-and-folder system, allowing you to select whole folder trees with little database load 

Installation
------------

This document assumes that you are familiar with Python and Django.

1. Download and install [sorl.thumbnail](http://thumbnail.sorl.net/docs/).
1. [Download and unzip the current release](http://github.com/philomat/django-media-tree/downloads/), or install using `git` as shown below (the latter two commands are necessary to pull submodule dependencies):

	$ git clone git://github.com/philomat/django-media-tree.git

2. Make sure `media_tree` is on your `PYTHONPATH`.
3. Set up the database tables: 

	$ ./manage.py syncdb

3. Copy the directory `media_tree/media/media_tree` to your `MEDIA_ROOT`.
4. Create the media storage directory (called `upload` by default) under `MEDIA_ROOT`, and make sure it is writable by your Django project. You can rename that directory if necessary, see Configuration.
5. Set up the database tables using 

	$ manage.py syncdb 

6. Add `media_tree` to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'media_tree',
    )

7. TODO If you want to enable the multi-upload queue (highly recommended), you need to add the `...` middleware to your `MIDDLE...` setting.
Security concerns blah

Configuration
-------------

You can override any of the settings found in `media_tree/defaults.py` in your project's settings file. 

Optional requirements
---------------------

* The form_designer admin interface requires jQuery to make uploads more user-friendly. The Javascript file is bundled with form_designer. Optionally, if Django CMS is installed, the file bundled with that app will be used. If you want to use you own jquery.js instead because you're already including it anyway, define JQUERY_JS in your settings file. For instance:

	JQUERY_JS = 'jquery/jquery-latest.js'

Using media_tree FileNodes in your own app
------------------------------------------

Interesting model methods:
`get_nested_list()`
`get_merged_list()`

Forms and fields:
...

Template tags:

`thumbnail_size`

Extending media_tree
--------------------

Creating admin actions
Creating CMS plugins
Creating media type extenders

  MEDIA_TREE_MEDIA_TYPE_EXTENDERS:

  class ID3TagExtender(media_tree.models.MediaTypeExtender)

    class Meta:
         abstract = True
    
    extends_media_types = ()
    extends_file_extensions = ()

    # the fields defined in this class are added to FileNode
    artist = models.CharField(max_length=255, null=True, blank=True)
    album = models.CharField(max_length=255, null=True, blank=True)
    track_number = models.IntegerField(null=True, blank=True)
    # etc

    def before_save(filenode):
    etc.... these methods are registered as signals

from ID3 import *
	try:
	  id3_info = ID3(filenode.file.path)
          for key, value in id3_info.items():
            print k.toLowerCase() in fields... then set metadata


Using media_tree FileNodes in your own app
------------------------------------------
 
Missing features
----------------
