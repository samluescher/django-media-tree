Installing Media Tree 
*********************

This install guide assumes you are familiar with Python and Django.


Dependencies 
============

Make sure to install the following packages if you want to use Media Tree:

- `Django <http://www.djangoproject.com>`_ >= 1.5
- `South <http://south.aeracode.org/>`_ >= 0.8
- `django-mptt <https://github.com/django-mptt/django-mptt>`_ > 0.4.2 (see
  :ref:`install-mptt`)
- `Pillow <http://pillow.readthedocs.org/>`_ >= 2.3


.. Note::
   All required Python packages can easily be installed using `pip
   <http://pypi.python.org/pypi/pip>`_ (or, alternatively, easy_install). 


Getting the code 
================

For the latest stable version (recommended), use ``pip``::

    pip install django-media-tree

**or** download it from http://github.com/samluescher/django-media-tree and run the
installation script::

    python setup.py install


Demo project
============

A demo project is included for you to quickly test and evaluate Django Media 
Tree. It is recommended to use `virtualenv <http://www.virtualenv.org>`_ for 
trying it out, as you'll be able to install all dependencies in isolation.
Afer installing `virtualenv`, run the following commands to start the demo 
project::

    mkdir django-media-tree-test && cd django-media-tree-test
    virtualenv venv
    source venv/bin/activate
    curl -L https://github.com/samluescher/django-media-tree/archive/master.zip  \
      -o django-media-tree-master.zip && unzip django-media-tree-master
    cd django-media-tree-master/demo_project
    pip install -r requirements.txt
    python manage.py syncdb
    python manage.py loaddata fixtures/initial_data.json
    python manage.py runserver

Then open http://localhost:8000 in your web browser.


Basic setup
===========

Please follow these steps to use Media Tree with your own application.

- In your project settings, add ``mptt`` and ``media_tree`` to the
  ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ... your other apps here
        'mptt', 
        'media_tree',
    )

- Make sure your ``STATIC_URL``, ``STATIC_ROOT``, ``MEDIA_URL`` and ``STATIC_ROOT``
  are properly configured.

  .. Note::
     Please refer to the Django documentation on how to configure your Django project
     `to serve static files <https://docs.djangoproject.com/en/dev/howto/static-files/>`_ 
     if you have not done that yet.

- If you are using ``django.contrib.staticfiles`` (recommended), just run the
  usual command to collect static files::

    python manage.py collectstatic

  If you are **not** going to use the ``staticfiles`` app, you will have to copy
  the contents of the ``static`` folder to the location you are serving static
  files from.
  
- Create the database tables::

    python manage.py syncdb

  Alternatively, if you are using `South <http://south.aeracode.org/>`_ in your
  project, you'll have to use a slightly different command::

    python manage.py syncdb --all 
    python migrate media_tree --fake

.. _configuring-media-backends:

Configuring media backends (optional)
=====================================

- If you want thumbnails to be generated -- which will usually be the case -- you 
  need to install the appropriate media backend that takes care of this. 
  Currently, `easy-thumbnails <https://github.com/SmileyChris/easy-thumbnails>`_ is 
  the only recommended and officially supported 3rd-party application.

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

- **Optional**: Also add any Media Tree extensions that you are planning to use
  to your ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ... your other apps here
        'media_tree.contrib.media_extensions.images.focal_point',
        'media_tree.contrib.media_extensions.zipfiles',
    )

  .. Note::
     See :ref:`bundled-extensions` for a list of default extensions included in
     the project.


.. _install-mptt:


Note on django-mptt 
===================

A version of ``django-mptt`` **newer than 0.4.2** is required because there is
an issue with older versions not indenting the folder list correctly. **Either**
install a recent version::

    pip install django-mptt==0.5.1

**or**, if for some reason you can't install a recent version, you can resolve
the situation by putting ``legacy_mptt_support`` in your ``INSTALLED_APPS``
**before** ``mptt``. This will be deprecated in the future::

    INSTALLED_APPS = (
      # ... your other apps here
      'media_tree.contrib.legacy_mptt_support', 'mptt', 'media_tree',
    )


.. _install-icon-sets:

Installing icon sets (optional)
===============================

By default, Media Tree only comes with plain file and folder icons. If you would
like to use custom icon sets that are more appropriate for your specific media
types, you can install them like a Django application.

The following ready-to-use modules contain some nice icons:

- `Teambox Icons <https://github.com/samluescher/django-teambox-icons>`_

You will need to configure Media Tree to use an icon set as follows.

- In order to install an icon set, simply add the respective module to your
  ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ... your other apps here
        'my_custom_icon_set',
    )

- If you are using ``django.contrib.staticfiles`` (recommended), just run the
  usual command to collect static files::

    ./manage.py collectstatic

  If you are **not** using the ``staticfiles`` app, copy the contents of the
  ``static`` folder to the static root of your project.

- Define ``MEDIA_TREE_ICON_DIRS`` in your project settings, and add the static
  path containing the new icon files, e.g.::

    MEDIA_TREE_ICON_DIRS = (
        'my_custom_icons/64x64px', # the new folder under your static root
        'media_tree/img/icons/mimetypes', # default icon folder
    )

  .. Note::
     You can add several icon sets to this tuple, and for each media file the
     first appropriate icon that is encountered will be used. Please notice that
     on the last line we are specifying the default icon location, which will be
     used as a fallback in case no appropriate icon is found in one of the
     custom sets.
