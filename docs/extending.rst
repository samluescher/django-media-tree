.. _extending:

Extending Django Media Tree
***************************

There are several ways in which you may want to add functionality to Media Tree.
Suppose you need to add support for a specific image format, or you need custom 
maintenance actions in the admin, or you might need to add some Javascript or 
CSS code to the FileNode form. For each of these cases, there is a so-called 
**extender class**.

Overview
========

The extender base classes provided by Media Tree are ``ModelExtender``, 
``AdminExtender`` and ``FormExtender``, and by subclassing them you create your
custom extenders. The structure of extender classes is similar to that
of a regular Django ``Model``, ``ModelAdmin``, or ``Form`` class, respectively,  
meaning that you can define several attributes such as model Fields or form
Media, and they will be added to Media Tree during runtime. 

.. Note::
   You can :ref:`package and install <installing-extensions>` your extender classes as a regular Django 
   application module, and have Media Tree auto-discover installed extensions by 
   providing a ``media_extension.py`` module. An application containing one or 
   more extenders and a ``media_extension.py`` that registers them is what is 
   called a **Media Tree extension**. 

Media Tree already comes with some exemplary extensions in its 
``contrib.media_extensions`` module. You should inspect these examples in order 
to get an idea of how to build an extension. There is also a tutorial below that 
should help you with creating your own extension.


Extender bases
==============

An extender is created by subclassing one of the following base classes:

Extending the FileNode model
----------------------------

.. autoclass:: media_tree.extension.ModelExtender
   :members:

Extending the FileNode admin
----------------------------

.. autoclass:: media_tree.extension.AdminExtender
   :members:

Extending forms
---------------

.. autoclass:: media_tree.extension.FormExtender
   :members:

.. _installing-extensions:

Registering and installing Media Tree extensions 
================================================

Each extension module is a regular Django application that is installed by 
putting the application in the ``INSTALLED_APPS`` setting.

An extension needs to contain a ``media_extension.py`` module that registers all
extenders that the extension module contains:

Example of an ``extension.py`` file::

    from media_tree import extension
    
    class SomeModelExtender(extension.ModelExtender):
        """Example extender"""
        pass
        
    extension.register(SomeModelExtender)

Notice that on the last line the extender is registered by calling the 
function ``media_tree.extension.register()``.

.. automodule:: media_tree.extension
   :members: register
   

Tutorial extension: Geotagging Photos
=====================================

Assume you are using landscape photographs on your website, and in the FileNode
admin you would like to be able to enter the latitude and longitude of the place
where they were taken. This is called *geotagging*. 

Getting started
---------------

The first step is to create a Django application that serves as the container
for our new extender classes. You can do this as usual on the command line from
your project folder::

    $ django-admin startapp media_tree_geotagging
    $ cd media_tree_geotagging
    $ touch media_extension.py

Notice that on the last line we created a file called ``media_extension.py``. 
Media Tree will scan all ``INSTALLED_APPS`` for such a file, so that all 
installed extensions will be auto-disovered.

We can delete most of the other files that the ``startapp`` command created,
such as ``models.py``, as we are probably not going to need them.

Extending the Model
-------------------

Now you can create the model extender in the file ``media_extension.py``, 
subclassing the parent class provided by Media Tree::

    from media_tree import extension
    from django.db import models
    
    class GeotaggingModelExtender(extension.ModelExtender):
        lat = models.FloatField('latitude', null=True, blank=True)
        lng = models.FloatField('longitude', null=True, blank=True)
        
    extension.register(GeotaggingModelExtender)
    
This class looks similar to a regular Model, but it does not have its own 
database table -- instead, its fields are added to the ``FileNode`` class when
you restart the development server.

.. Note::
   This extension adds the fields ``lat`` and ``lng`` to
   the ``FileNode`` model. You are going to have to add these fields to 
   the database table yourself by modifying the ``media_tree_filenode`` table 
   with a database client, **unless you installed it before running** 
   ``syncdb``). 
        
Extending the form 
------------------

Of course we want to be able to edit our two new fields in the admin, so we need
to create a form extender and add a new fieldset. We do this by adding a new 
class to ``media_extension.py``::

    class GeotaggingFormExtender(extension.FormExtender):

        class Meta:
            fieldsets = [
                ('Geotagging', {
                    'fields': ['lat', 'lng'],
                    'classes': ['collapse']
                })
            ]

    extension.register(GeotaggingFormExtender)

Installing the extension
------------------------

After you have created the database fields, you can install the extension by
adding it to the ``INSTALLED_APPS`` in your project's settings file::

    INSTALLED_APPS = (
        # ... your apps here ...
        'media_tree',
        'media_tree_geotagging'
    )

Adding an Admin Action
----------------------

Let's assume you have a content editor on staff, and this person's job is to 
check if photographs were geotagged, and to notify the photographer of the ones
that aren't. We can simplify this task by adding an admin action to the 
FileNode admin.

With this extender, the editor will be able to check the checkboxes next to 
image files, have them checked automatically to see if they are not yet 
geotagged, and email the photographer the admin links to those FileNode objects.

As you may be assuming by now, we create an admin extender in 
``media_extension.py``:: 

    from django.core.mail import send_mail
    
    class GeotaggingAdminExtender(extension.AdminExtender):

        def notify_of_non_geotagged(modeladmin, request, queryset):
            non_geotagged_links = []
            for node in queryset:
                # Check if node is JPG and not geotagged:
                if node.extension == 'jpg':
                    if not node.lat or not node.lng:
                        non_geotagged_links.append(node.get_admin_url())
            # Send email with admin links for these nodes, and message
            # current user about status of the action.
            if len(non_geotagged_links):
                message = '\n'.join(non_geotagged_links) + '\n\nThanks!'
                send_mail('Please geotag these files', message, 
                    'from@example.com', ['to@example.com'])
                modeladmin.message_user(request, 'Notification sent for'  \
                    + ' %i non-geotagged JPGs.' % len(non_geotagged_links))
            else:
                modeladmin.message_user(request, 'All selected images appear'  \
                    +' to be OK.')
        notify_of_non_geotagged.short_description =  \
            'Notify photographer if selected JPGs are not geotagged' 

        actions = [notify_of_non_geotagged]
    
This last example is a bit more verbose, but you will notice that it just 
contains one method with the exact same signature like a regular Django admin 
action, and on the last line we are specifying the list of actions that this 
extender will contribute to the FileNode admin. Also, we are giving the method a 
``short_description`` that will appear in the drop-down menu above the list 
displaying all of our FileNodes.

And that's it! We are now able to geotag images in the Django admin. 

Adding Form Media
-----------------

Of course it would be great if we had a map widget in the form where we can just 
drop a pin on the location of the photograph. Creating such a widget is beyond 
the scope of this tutorial, but if we had created a Javascript containing the 
code that implements such a widget, we could easily add this file by adding a 
``Media`` class to our form extender::

    class GeotaggingFormExtender(extension.AdminExtender):

        class Media:
            js = (
                'map_widget.js',
            )

        # ...
    
This Media definition is merged with the default media loaded for the FileNode
form, and we can use it to load any code or CSS files required by our 
hypothetical map widget.

Conclusion
----------

Using this extension system, you can change many aspects of how Media Tree 
behaves. There are more attributes and also **signals** that you can define in 
your extenders than the ones described in this tutorial. Code away and, please, 
share your extensions with the Interested Public!


Tutorial extension: Creating an icon set
========================================

Icon sets are also packaged as Django applications, and creating a custom set
is rather easy. Basically, an icon set is a Python module containing nothing
but an empty ``__init__.py`` and a ``static`` folder with the respective image
files. Here's an example of how that could look like::

    my_custom_audio_icon_set
        __init__.py
        static
            audio_icons
                audio.png
                ogg.png
                mp3.png

Note that this package contains three icons: One for generic audio files and
one for either ``OGG`` or ``MP3`` files.

.. Note::
   When displaying a file icon, Media Tree will scan all installed icon sets for
   an icon that is named like the media file's extension (e.g. ``mp3.png``),
   then for one named like its mimetype (e.g. ``audio/x-mpeg.png``), then for
   the mime supertype (e.g. ``audio.png``). Icon discovery is handled by a class
   called ``MimetypeStaticIconFileFinder``, which by default only finds ``PNG``
   files.

To install this icon set, simply add ``my_custom_audio_icon_set`` to your
``INSTALLED_APPS``, collect its static files, and configure the new icon folder
using the ``MEDIA_TREE_ICON_DIRS`` setting. See :ref:`install-icon-sets`
for more detailed instructions.

