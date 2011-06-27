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

You can package your extenders as a regular Django application module, and have
Media Tree auto-discover installed extensions by providing a 
``media_extension.py`` module. Such an application is called a **Media Tree 
extension**. 

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


Registering and installing Media Tree extensions 
================================================

Each extension module is a Django application that is installed by putting the
application in the ``INSTALLED_APPS`` setting.

An extension needs to contain a `media_extension.py` module that registers all
extenders that the extension module contains:

Example of an ``extension.py`` file:

.. code-block:: python

    from media_tree import extension
    
    class SomeModelExtender(extension.ModelExtender):
        """Example extender"""
        pass
        
    extension.register(SomeModelExtender)

Notice that on the last line the extender is registered by calling the 
function ``media_tree.extension.register()``.

.. automodule:: media_tree.extension
   :members: register
   

Tutorial extension: geocoding photos
====================================

Assume you are using landscape photographs on your website, and you would like 
to be able to enter the latitude and longitude of where they were taken in the
FileNode admin. This is called *geocoding*. 

Getting started
---------------

The first step is to create a Django application that serves as the container of
our new extender classes. You can do this as usual on the command line: 

.. code-block:: none

    $ django-admin startapp media_tree_geocode
    $ cd media_tree_geocode
    $ touch media_extension.py

Notice that on the last line we created a file called ``media_extension.py``. 
Media Tree will scan all ``INSTALLED_APPS`` for such a file, so that all 
installed extensions will be auto-disovered.

We can delete most of the other files that the ``startapp`` command created,
such as ``models.py``, as we are probably not going to need them.

Extending the Model
-------------------

Now you can create the model extender in the file ``media_extension.py``, 
subclassing the parent class provided by Media Tree:

.. code-block:: python

    from media_tree import extension
    from django.db import models
    
    class GeocodeModelExtender(extension.ModelExtender):
        lat = models.FloatField('latitude', null=True, blank=True)
        lng = models.FloatField('latitude', null=True, blank=True)
        
    extension.register(GeocodeModelExtender)
    
This class looks just like a regular Model, but it does not have its own 
database table -- instead, its fields are added to the ``FileNode`` class when
you restart the development server.

.. note:: Database migration

    **Notice that you are going to have to add these two fields to the database table
    yourself** (using ``syncdb`` or modifying the ``media_tree_filenode`` table with
    a database client). 
        
Extending the form 
------------------

Of course we want to be able to edit our two new fields in the admin, so we need
to create a form extender and add a new fieldset. We do this by adding a new 
class to ``media_extension.py``:

.. code-block:: python

    class GeocodeFormExtender(extension.FormExtender):

        class Meta:
            fieldsets = [
                ('Geocoding', {
                    'fields': ['lat', 'lng'],
                    'classes': ['collapse']
                })
            ]

    extension.register(GeocodeFormExtender)

Installing the extension
------------------------

After you have created the database fields, you can install the extension by
adding it to the ``INSTALLED_APPS`` in your project's settings file:

.. code-block:: python

    INSTALLED_APPS = (
        # ... your apps here ...
        'media_tree',
        'media_tree_geocode'
    )

Adding an Admin Action
----------------------

Let's assume you have a content editor on staff, and this person's job is to 
check if photographs were geocoded, and notify the photographer of the ones
that aren't. We can simplify this task by adding an admin action to the 
FileNode admin.

With this extender, the editor will be able to check the checkboxes next to 
image files, have them checked automatically to see if they are not yet 
geocoded, and email the photographer the admin links to those FileNode objects.

As you may already be assuming, we create an admin extender in 
``media_extension.py``: 

.. code-block:: python

    class GeocodeAdminExtender(extension.AdminExtender):

        def notify_of_non_geocoded(modeladmin, request, queryset):
            non_geocoded_links = []
            for node in queryset:
                # Check if node is JPG and not geocoded:
                if node.extension == 'jpg':
                    if not node.lat or not node.lng:
                        non_geocoded_links.append(node.get_admin_url())
            # Send email with admin links for thise nodes, and message
            # current user about status of the action.
            if len(non_geocoded_links):
                message = '\n'.join(non_geocoded_links) + '\n\nThanks!'
                send_mail('Please geocode these files', message, 
                    'from@example.com', ['to@example.com'])
                modeladmin.message_user(request, 'Notification sent for'  \
                    + ' %i non-geocoded JPGs.' % len(non_geocoded_links))
            else:
                modeladmin.message_user(request, 'All selected images appear'  \
                    +' to be OK.')
        notify_of_non_geocoded.short_description =  \
            'Notify photographer if selected JPGs are not geocoded' 

        actions = [notify_of_non_geocoded]
    
This last example is a bit more verbose, but you will notice that it just 
contains one method with the exact same signature like a regular Django admin 
action, and on the last line we are specifying the list of actions that this 
extender will contribute to the FileNode admin. Also, we are giving the method a 
``short_description`` that will appear in the drop-down menu above the list 
displaying all of our FileNodes.

And that's it! We are now able to geocode images in the Django admin. Of course
it would be great if we had a map widget in the form where we can just drop a 
pin on the location of the photograph. Creating such a widget is beyond the 
scope of this tutorial, but adding the final Javascript file is done by simply
adding a ``Media`` class to our form extender:

.. code-block:: python

    class GeocodeFormExtender(extension.AdminExtender):

        class Media:
            js = (
                'map_widget.js',
            )

        # ...
    
Now this Media definition is merged with the default media loaded for the 
FileNode form, and we load any code or CSS files required by our hypothetical
map widget.

Using this extension system, you can change many aspects of how Media Tree 
behaves. There more attributes and signals that you can define in your extenders
than the ones described in this tutorial. Code away and, please, share your 
extensions with the Interested Public!
