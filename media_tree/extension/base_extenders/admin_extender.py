from media_tree.admin import FileNodeAdmin
from media_tree.extension.base_extenders import MediaDefiningExtender


class AdminExtender(MediaDefiningExtender):
    """In order to extend the ModelAdmin, you need to subclass this class and
    define the appropriate attributes:
    """

    Media = None
    """A Media class, defined exactly like the Media classes of a Form or
    a ModelAdmin. The Media definitions are merged into the extended class.
    """
    
    actions = None
    """A list of admin actions that are added to the ModelAdmin calling its
    method `register_action(func, required_perms)`.
    Each item in this list can either be a callable or a tuple containing the
    callable and a list of permissions required to execute an action.
    
    For example:
    
    .. code-block:: python

        actions = [
            perform_some_action, 
            (perform_a_maintenance_action, ('media_tree.manage_filenode',))
        ]
        """ 
    
    @classmethod
    def contribute(extender, extended_class=FileNodeAdmin):
        super(AdminExtender, extender).contribute(extended_class)
        if extender.actions:
            for action in extender.actions:
                if isinstance(action, tuple):
                    extended_class.register_action(*action)
                else:
                    extended_class.register_action(action)
