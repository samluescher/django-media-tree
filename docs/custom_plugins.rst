.. _custom-plugins:

Creating custom plugins for use with 3rd-party applications
***********************************************************

Introduction
============

Django Media Tree comes with some generic view classes and mixins that make it
relatively easy to use ``FileNode`` objects with your own applications.

The following pseudo code should give you an idea of how to implement your own
custom plugin that will render a file listing and work together with the
3rd-party application of your choice. It loosely looks like a Django CMS plugin.
Please notice that the ``render()`` method is passed an
``options_model_instance``, which can be a dictionary or an object with
attributes to initialize the generic view class we are using, which is
``ListingView`` in this case. See :ref:`generic-views` for more
information on the view classes themselves::


    from media_tree.contrib.views.listing import ListingMixin
    from third_party_app import YourPluginSuperclass
    from django.shortcuts import render_to_response
    
    # Notice we are subclassing our third-party plugin class,
    # as well as the ListingMixin
    
    class CustomFileNodeListingPlugin(YourPluginSuperclass, ListingMixin):
    
        # Assuming render() is a standard method of YourPluginSuperclass
        def render(self, context, options_model_instance):
    
            # Get the generic view class using the Mixin
            # Notice that get_detail_view() is inherited from the ListingMixin.
            # We are also passing our options model instance for configuring
            # the view instance.
            view = self.get_detail_view(options_model_instance.selected_folders,
                opts=options_model_instance)
      
            # Get the template context as returned by the view class
            context_data = view.get_context_data()
      
            # Render with custom template
            return render_to_response('listing.html', context_data)

This is what our model classes (namely the class of the ``options_model_instance`` above)
might look like::

    from django.db import Models
    from media_tree.fields import FileNodeForeignKey

    class PluginOptions(models.Model):
        # These field names are derived from
        # media_tree.contrib.views.list.ListingView.
        max_depth = models.IntegerField()
        include_descendants = models.BooleanField()
        
    class SelectedFolder(models.Model):
        plugin = models.ForeignKey(PluginOptions)
        folder = FileNodeForeignKey()

The first class contains our plugin option fields. Notice that when calling the
``get_detail_view()`` or ``get_view()`` methods provided by the
``ListingMixin`` and passing it an instance of this model, any fields that
match attributes of the view object returned will be used to initialized the
view object.

The second class creates a relationship between the options model and the
``FileNode`` model, i.e. you will be able to link ``FileNode`` objects to
plugins.


View Mixins
===========

View Mixins are classes that add methods useful for interfacing with Django
Media Tree's generic view classes to your custom plugin classes, as demonstrated
in the above example.

.. autoclass:: media_tree.contrib.views.listing.ListingMixin
   :members:
   :inherited-members:
   :exclude-members: get_view

.. autoclass:: media_tree.contrib.views.detail.FileNodeDetailMixin
   :members:
   :inherited-members:
   :exclude-members: get_view

.. autoclass:: media_tree.contrib.views.detail.image.ImageDetailMixin
   :members:
   :inherited-members:
   :exclude-members: get_view

