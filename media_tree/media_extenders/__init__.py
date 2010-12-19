from media_tree.models import FileNode
from django.db.models import fields
from django.db.models import signals 

SIGNAL_NAMES = ('pre_save', 'post_save', 'pre_delete', 'post_delete')

class MediaExtender(object):
    pass

def register(extender, extended_class=FileNode):
    # Add all fields defined in extender
    for key, attr in vars(extender).items():
        if issubclass(attr.__class__, fields.Field):
            attr.contribute_to_class(extended_class, key)
    # Connect signals defined in extender.
    # Note that if the extender is a class, the receiver methods must be static,
    # so you should use the @staticmethod decorator
    for signal_name in SIGNAL_NAMES:
        if hasattr(extender, signal_name):
            sender = getattr(signals, signal_name)
            receiver = getattr(extender, signal_name)
            sender.connect(receiver, sender=extended_class)
