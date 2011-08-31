Installing Media Tree
*********************

TODO This howto does not cover... serving media files, django.contrib.staticfiles. 

- Download and put the ``media_tree`` module on your pythonpath, or install using
  pypi TODO

- Add ``media_tree`` to your ``INSTALLED_APPS`` setting::

    INSTALLED_APPS = (
        # ... your other apps here 
        'mptt',
        'media_tree',
    )

- If you are not using ``django.contrib.staticfiles``, copy the contents of the
  ``static`` folder to the static root of your project. If you are using the 
  ``staticfiles`` app, just run the usual command to collect static files::

    ./manage.py collectstatic

  Please refer to the Django documentation to learn about the ``staticfiles`` 
  app.
    
- Optional: If you want thumbnails to be generated, which will usually be the 
  case, you need to install the appropriate media backend that takes care of 
  this. Currently, ``easy_thumbnails`` is the recommended 3rd-party application. 

  After you've installed ``easy_thumbnails``, configure Media Tree to use it by
  defining ``MEDIA_TREE_MEDIA_BACKENDS`` in your project settings:
  
      MEDIA_TREE_MEDIA_BACKENDS = (
          'media_tree.contrib.media_backends.easy_thumbnails.EasyThumbnailsBackend',
      )

  .. Note::
  In principle, Media Tree can work together with any other thumbnail generating
  app, provided that you write the appropriate media backend class to support 
  it. Please have a look at one of the backends under 
  ``media_tree.media_backends`` if you are interested in using your own specific 
  3rd-party app. 

- Optional: Also add any Media Tree extensions that you are planning to use to 
  your ``INSTALLED_APPS``::

    INSTALLED_APPS = (
        # ... your other apps here 
        'media_tree.contrib.icon_sets.teambox_icons',
        'media_tree.contrib.media_extensions.images.focal_point',
        'media_tree.contrib.media_extensions.zipfiles',
    )

- Optional: If you are planning to use a Flash uploader such as ``SWFUpload``,
  add ``SessionPostMiddleware`` to your ``MIDDLEWARE_CLASSES``::

    MIDDLEWARE_CLASSES = (
        # ...
        'media_tree.middleware.SessionPostMiddleware',
        # Notice that ``SessionPostMiddleware`` goes before ``SessionMiddleware`` 
        'django.contrib.sessions.middleware.SessionMiddleware',
    )

- Install icon set: TODO