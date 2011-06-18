from media_tree.admin import FileNodeAdmin
from media_tree.extension.base_extenders import MediaDefiningExtender


class AdminExtender(MediaDefiningExtender):

    # TODO test, and register actions
    @classmethod
    def contribute(extender, extended_class=FileNodeAdmin):
        super(AdminExtender, extender).contribute(extended_class)
