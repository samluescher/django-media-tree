from media_tree.extension.base_extenders import MediaTreeExtender
from media_tree.extension.base_extenders.admin_extender import AdminExtender
from media_tree.extension.base_extenders.form_extender import FormExtender
from media_tree.extension.base_extenders.model_extender import ModelExtender


def register(extender):
    """Registers the `extender` class and lets it contribute its attributes to 
    the respective extended classes during runtime.
    """ 
    if not issubclass(extender, MediaTreeExtender):
        raise NotImplementedError('Class `%s` needs to be a subclass of `MediaTreeExtender`.' % extender)
    extender.contribute()
    
