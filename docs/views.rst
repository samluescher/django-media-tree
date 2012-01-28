.. _generic-views:

Class-based generic views
*************************

.. automodule:: media_tree.contrib.views
   :members:

List Views
==========

.. autoclass:: media_tree.contrib.views.listing.FileNodeListingView
   :members:
   :inherited-members:

.. autoclass:: media_tree.contrib.views.listing.FileNodeListingFilteredByFolderView
   :members:
   :inherited-members:

Detail Views
============

.. autoclass:: media_tree.contrib.views.detail.FileNodeDetailView
   :members:
   :inherited-members:
   :exclude-members: get_slug_field

.. autoclass:: media_tree.contrib.views.detail.image.ImageNodeDetailView
   :members:
   :inherited-members:
   :exclude-members: get_slug_field

