.. _custom-plugins:

Implementing custom plugins
***************************

Django Media Tree comes with some generic view classes and mixins that make it
relatively easy to use ``FileNode`` objects with your own applications.

The following pseudo code should give you an idea of how to implement your own
custom plugin that will render a file listing and work together with some
3rd-party application. It loosely looks like a Django CMS plugin. Please notice
that the ``render()`` method is passed an ``options_model_instance``, which
can be a dictionary or an object with attributes to initialize the generic
view class we are using, ``ListingView``) (TODO REF to generic views)::

    from media_tree.contrib.views.listing import ListingMixin
    from 3rd_party_app import YourPluginSuperclass
    
    class CustomFileNodeListingPlugin(YourPluginSuperclass, ListingMixin):
    
        def render(self, context, options_model_instance):
            view = self.get_detail_view(instance.node, opts=options_model_instance)
            context.update(view.get_context_data())
            return render_to_response('listing.html', context)


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

