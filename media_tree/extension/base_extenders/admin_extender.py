from media_tree.admin import FileNodeAdmin
from media_tree.extension.base_extenders import MediaDefiningExtender


class AdminExtender(MediaDefiningExtender):

    # TODO test, and register actions
    @classmethod
    def contribute(extender, extended_class=FileNodeAdmin):
        super(AdminExtender, extender).contribute(extended_class)
        if hasattr(extender, 'actions'):
            for action in extender.actions:
                if isinstance(action, tuple):
                    extended_class.register_action(*action)
                else:
                    extended_class.register_action(action)
