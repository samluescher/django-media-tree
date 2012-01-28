"""
The module ``media_tree.contrib.views`` contains class-based generic views that
enable you to access ``FileNode`` objects through public URLs. Please see below
for specific examples.

.. Note::
   As with any public views, you may want to restrict the objects that should be
   publicly visible by passing an appropriately filtered ``queryset`` when
   implementing a view. For instance, you may not want users to see the internal
   folder structure of your ``FileNode`` objects, hence using a ``FileNodeListingView``
   with a QuerySet such as ``FileNode.objects.all()`` would be a bad idea.
"""