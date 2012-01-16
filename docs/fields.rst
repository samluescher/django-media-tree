Fields and forms
****************

There are a number of field classes for conveniently using ``FileNode`` objects
in your own Django applications. 

The following example model contains a ``ForeignKey`` field linking to a
``FileNode`` object that is associated to a document file. Note the special
parameters that specifying which media types will be validated, and which should
be visible in the widget::
    
    class MyModel(models.Model):
        document_node = FileNodeForeignKey(allowed_media_types=(media_types.DOCUMENT,), null=True,
                limit_choices_to={'media_type__in': (FileNode.FOLDER, media_types.DOCUMENT)})

The following example model will allow the user to select a ``FileNode`` object
associated to an image file::

    class MyModel(models.Model):
        image_node = ImageFileNodeForeignKey(null=True)

The following field classes are available:

.. automodule:: media_tree.fields
   :members:
   :inherited-members:
