from media_tree.extension.base_extenders import MediaTreeExtender
from media_tree.models import FileNode
from django.db.models import fields
from django.db.models import signals 
from types import FunctionType


class ModelExtender(MediaTreeExtender):
    """In many cases, extensions need to store additional data and add custom 
    fields to the extended model class. This is achieved by defining model 
    Fields in a ``ModelExtender`` subclass, just like they are defined in a 
    Model class:

    .. code-block:: python

        class MyModelExtender(extension.ModelExtender):
            some_field = models.CharField('a new field', max_length=10)

    All fields defined like this will be added to to the extended model class
    during runtime.  

    .. note:: 
       If your extender defines model Fields, you are going to have to add these
       to the database table yourself, since Media Tree does not make changes to
       the table. However, using ``syncdb`` after installing an extension will
       create the table including any new fields defined by extensions.
    """

    SIGNAL_NAMES = ('pre_save', 'post_save', 'pre_delete', 'post_delete')
    """To perform custom processing and data manipulations when a Model instance
    is changed, you can use signals.
    
    For each signal name listed in this attribute, you can define an 
    extender method that will be receiving the respective signal. By default,
    the allowed signals are: 
    ``'pre_save', 'post_save', 'pre_delete', 'post_delete'``.
    
    For instance, if the extender should set a specific model Field before the
    model instance is saved, define the ``pre_save`` receiver:
    
    .. code-block:: python

        class MyModelExtender(extension.ModelExtender):

            SIGNAL_NAMES = ('pre_save',)

            @staticmethod
            def pre_save(sender, **kwargs):
                sender.some_field = 'some_value'
    
    **Notice that if the signal receiver is a class member it needs to be a 
    static method**, as it won't be passed an instance of the class it belongs 
    to. Also, the function takes a ``sender`` argument, along with wildcard 
    keyword arguments (``**kwargs``), as explained in the `Django Signals 
    documentation <https://docs.djangoproject.com/en/dev/topics/signals/>`_.
    """
    
    @classmethod
    def contribute(extender, extended_class=FileNode):
        for attr_name, attr in vars(extender).items():
            if issubclass(attr.__class__, fields.Field):
                # Add all fields defined in extender to models
                attr.contribute_to_class(extended_class, attr_name)
            elif issubclass(attr.__class__, FunctionType):
                if attr_name in extender.SIGNAL_NAMES:
                    # Connect signals defined in extender.
                    # Note that if the extender is a class, the receiver methods must be static,
                    # so you should use the @staticmethod decorator
                    sender = getattr(signals, attr_name)
                    receiver = getattr(extender, attr_name)
                    sender.connect(receiver, sender=extended_class)
                else:
                    # Add all other functions to model
                    setattr(extended_class, attr_name, attr)
