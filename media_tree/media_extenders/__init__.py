from media_tree.models import FileNode
from django.db.models import fields
from django.db.models import signals 
from types import FunctionType

SIGNAL_NAMES = ('pre_save', 'post_save', 'pre_delete', 'post_delete')

class MediaExtender(object):
    pass

def register(extender, extended_class=FileNode):
    for attr_name, attr in vars(extender).items():
        if issubclass(attr.__class__, fields.Field):
            # Add all fields defined in extender to models
            attr.contribute_to_class(extended_class, attr_name)
        elif issubclass(attr.__class__, FunctionType):
            if attr_name in SIGNAL_NAMES:
                # Connect signals defined in extender.
                # Note that if the extender is a class, the receiver methods must be static,
                # so you should use the @staticmethod decorator
                sender = getattr(signals, attr_name)
                receiver = getattr(extender, attr_name)
                sender.connect(receiver, sender=extended_class)
            else:
                # Add all other functions to model
                setattr(extended_class, attr_name, attr)
        
