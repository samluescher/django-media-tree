from media_tree.extension.base_extenders import MediaDefiningExtender
from media_tree.admin.forms import FileForm


class FormExtender(MediaDefiningExtender):
    """
    In order to extend form classes, for instance to load additional form media, 
    you need to subclass the this class and define the appropriate attributes: 
    """

    Media = None
    """A Media class, defined exactly like the Media classes of a Form or
    a ModelAdmin. The Media definitions are merged into the extended class.
    """
    
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
