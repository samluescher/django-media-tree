from media_tree.admin import FileNodeAdmin
from media_tree.extension.base_extenders import MediaDefiningExtender


class AdminExtender(MediaDefiningExtender):
    """
    Subclass this class to extends a ModelAdmin with the following elements:
    
        `class Media`
            Media definitions are merged just like when you inherit from a Form or
            ModelAdmin class.
            
        `actions`
            The ModelAdmin class will need a method `register_action(func, required_perms)`
            that takes care of adding the action. 
    """
    @classmethod
    def contribute(extender, extended_class=FileNodeAdmin):
        super(AdminExtender, extender).contribute(extended_class)
        if hasattr(extender, 'actions'):
            for action in extender.actions:
                if isinstance(action, tuple):
                    extended_class.register_action(*action)
                else:
                    extended_class.register_action(action)
