Fields and forms
****************

There are a number of field classes for conveniently using ``FileNode`` objects
in your own Django applications. 

The following example model contains a ``ForeignKey`` field linking to a
``FileNode`` object that is associated to a document file. Notice the parameters
specifying which media types will be validated, and which should be visible in
the widget::
    
    from media_tree.fields import FileNodeForeignKey
    from media_tree import media_types
    from media_tree.models import FileNode
    from django.db import models

    class MyModel(models.Model):
        document_node = FileNodeForeignKey(allowed_media_types=(media_types.DOCUMENT,), null=True,
                limit_choices_to={'media_type__in': (FileNode.FOLDER, media_types.DOCUMENT)})

The following example model will allow the user to select a ``FileNode`` object
associated to an image file::

    from media_tree.fields import ImageFileNodeForeignKey
    from django.db import models

    class MyModel(models.Model):
        image_node = ImageFileNodeForeignKey(null=True)

The following example form will allow the user to select files that are under a specific parent 
folder named “Projects”::

    from media_tree.models import FileNode
    from media_tree.fields import FileNodeChoiceField
    from django import forms

    class MyForm(forms.Form):
        node = FileNodeChoiceField(queryset=FileNode.objects.get(
            name="Projects", node_type=FileNode.FOLDER).get_descendants())

For your own applications, the following field classes are available:

.. automodule:: media_tree.fields
   :members:
