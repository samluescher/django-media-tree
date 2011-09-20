"""
focal_point
===========

The *focal_point* extension allows you to drag a marker on image thumbnails 
while editing, thus specifying the most relevant portion of the image. You can
then use these coordinates in templates for image cropping. 

- To install it, add the extension module to your ``INSTALLED_APPS`` setting::   

    INSTALLED_APPS = (
        # ... your apps here ...
        'media_tree.contrib.media_extensions.images.focal_point'
    )
    
- If you are not using ``django.contrib.staticfiles``, copy the contents of the
  ``static`` folder to the static root of your project. If you are using the 
  ``staticfiles`` app, just run the usual command to collect static files::

    $ ./manage.py collectstatic

.. Note::
   This extension adds the fields ``focal_x`` and ``focal_y`` to
   the ``FileNode`` model. You are going to have to add these fields to 
   the database table yourself by modifying the ``media_tree_filenode`` table 
   with a database client, **unless you installed it before running** 
   ``syncdb``). 

"""
