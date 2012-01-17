Installing Media Tree
*********************

This document assumes you are familiar with Python and Django.


Dependencies
============

Make sure to install these packages prior to installation:

- Django >= 1.2.5
- south >= 0.7.2
- django-mptt > 0.4.2 (see :ref:`install-mptt`)
- PIL >= 1.1


Getting the code
================

For the latest stable version (recommended), use ``pip`` or ``easy_install``::

    $ pip install django-media-tree  

**Alternatively**, if you would like to use the latest development version, 
you can also install it using ``pip``::

    $ pip install -e git://github.com/philomat/django-media-tree#egg=django-media-tree

**or** download it from http://github.com/philomat/django-media-tree and run the 
installation script::

    $ python setup.py install

.. Note::
   In case you get a permission error, you will probably have to run the above 
   commands with root permissions, i.e. enter ``sudo pip install …`` and 
   ``sudo python setup.py install``.


Basic setup
===========

- In your project settings, add ``mptt`` and ``media_tree`` to the
  ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ... your other apps here
        'mptt',
        'media_tree',
    )

- If you are using ``django.contrib.staticfiles`` (recommended), just run the
  usual command to collect static files::

    $ ./manage.py collectstatic

  .. Note::
     Please refer to the Django documentation on how to `set up the static files
     app <https://docs.djangoproject.com/en/dev/ref/contrib/staticfiles/>`_ if you 
     have not done that yet.   

  If you are **not** going to use the ``staticfiles`` app, copy the contents 
  of the ``static`` folder to the static root of your project.
  
- Create the database tables:

    $ python manage.py syncdb

  Notice that if you are using South, you'll have to use a slightly different command::

    $ python manage.py syncdb --all
    $ python migrate media_tree --fake

.. _configuring-media-backends:

- **Configuring media backends (optional)**: If you want thumbnails to be
  generated, which will usually be the case, you need to install the appropriate
  media backend that takes care of this. Currently, `easy-thumbnails
  <https://github.com/SmileyChris/easy-thumbnails>`_ is the only recommended and
  officially supported 3rd-party application.

  After you've installed the ``easy_thumbnails`` module, configure Media Tree to
  use it by defining ``MEDIA_TREE_MEDIA_BACKENDS`` in your project settings::
  
      MEDIA_TREE_MEDIA_BACKENDS = (
          'media_tree.contrib.media_backends.easy_thumbnails.EasyThumbnailsBackend',
      )

  .. Note::
     In principle, Media Tree can work together with any other thumbnail
     generating app, provided that you write the appropriate media backend class
     to support it. Please have a look at one of the backends under
     ``media_tree.contrib.media_backends`` if you are interested in using your
     own specific 3rd-party app. 

.. _install-swfupload:

- **Configuring the uploader (optional, recommended)**: If you are planning to use a Flash uploader such as
  ``SWFUpload``, add ``SessionPostMiddleware`` to your ``MIDDLEWARE_CLASSES``::

    MIDDLEWARE_CLASSES = (
        # ...
        'media_tree.middleware.SessionPostMiddleware',
        # Notice that ``SessionPostMiddleware`` goes before ``SessionMiddleware`` 
        'django.contrib.sessions.middleware.SessionMiddleware',
    )

- **Optional**: Also add any Media Tree extensions that you are planning to use
  to your ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ... your other apps here
        'media_tree.contrib.media_extensions.images.focal_point',
        'media_tree.contrib.media_extensions.zipfiles',
    )

  .. Note::
     See :ref:`bundled-extensions` for a list of default extensions included in the project.


.. _install-mptt:


Note on django-mptt
===================

A version of ``django-mptt`` **newer than 0.4.2** is required because there is
an issue with older versions not indenting the folder list correctly. **Either**
install a recent version::

    $ sudo pip install -e git://github.com/django-mptt/django-mptt.git@0.5.2#egg=django-mptt 

**or**, if for some reason you can't install a current version, you can resolve the 
situation by putting ``legacy_mptt_support`` in your ``INSTALLED_APPS`` **before** 
``mptt``. This will be deprecated in the future::

    INSTALLED_APPS = (
      # ... your other apps here
      'media_tree.contrib.legacy_mptt_support',
      'mptt',
      'media_tree',
    )


.. _install-icon-sets:

Installing icon sets
====================

By default, Media Tree only comes with plain file and folder icons. If you would
like to use custom icon sets that are more appropriate for your specific media
types, you can install them like a Django application, and configure Media Tree
to use them as follows.

- In order to install an icon set, simply add the respective module to your
  ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ... your other apps here 
        'my_custom_icon_set',
    )

- If you are using ``django.contrib.staticfiles`` (recommended), just run the
  usual command to collect static files::

    $ ./manage.py collectstatic

  If you are **not** using the ``staticfiles`` app, copy the contents of the
  ``static`` folder to the static root of your project.

- Define ``MEDIA_TREE_ICON_DIRS`` in your project settings, and add the static
  path containing the new icon files, e.g.::

    MEDIA_TREE_ICON_DIRS = (
        'my_custom_icons/64x64px',  # the new folder under your static root 
        'media_tree/img/icons/mimetypes',  # default icon folder
    )

  .. Note::
     You can add several icon sets to this tuple, and for each media file the
     first appropriate icon that is encountered will be used. Please notice
     that on the last line we are specifying the default icon location,
     which will be used as a fallback in case no appropriate icon is found in
     one of the custom sets.
