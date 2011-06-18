from media_tree.extension.base_extenders import MediaDefiningExtender
from media_tree.forms import FileForm


class FormExtender(MediaDefiningExtender):
    
    @classmethod
    def contribute(extender, extended_class=FileForm):
        super(FormExtender, extender).contribute(extended_class)
        
        # TODO: what about the `extend` property? Media extender should
        # be able to override media instead of extending.

        # Extends fieldsets with extender fieldsets
        if hasattr(extender.Meta, 'fieldsets'):
            if not getattr(extended_class.Meta, 'fieldsets', None):
                extended_class.Meta.fieldsets = []
            extended_class.Meta.fieldsets.extend(extender.Meta.fieldsets)
