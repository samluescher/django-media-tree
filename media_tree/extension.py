from media_tree.models import FileNode
from django.db.models import fields
from django.db.models import signals 
from types import FunctionType

class MediaTreeExtender:

    @classmethod
    def contribute(extender):
        raise NotImplementedError('Class `%s` has not implemented a `contribute()` method.' % extender)


class ModelExtender(MediaTreeExtender):

    SIGNAL_NAMES = ('pre_save', 'post_save', 'pre_delete', 'post_delete')

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


def register(extender):
    
    if not issubclass(extender, MediaTreeExtender):
        raise NotImplementedError('Class `%s` needs to be a subclass of `MediaTreeExtender`.' % extender)
    
    extender.contribute()
    
