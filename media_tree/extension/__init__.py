from media_tree.extension.base_extenders import MediaTreeExtender
from media_tree.extension.base_extenders.admin_extender import AdminExtender
from media_tree.extension.base_extenders.form_extender import FormExtender
from media_tree.extension.base_extenders.model_extender import ModelExtender


def register(extender):
    if not issubclass(extender, MediaTreeExtender):
        raise NotImplementedError('Class `%s` needs to be a subclass of `MediaTreeExtender`.' % extender)
    extender.contribute()
    
