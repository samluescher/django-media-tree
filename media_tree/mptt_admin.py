from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import actions

try:
    from functools import wraps
except ImportError:
    from django.utils.functional import wraps # Python 2.3, 2.4 fallback

"""
For this hack to work the django-mptt managers.py has to have been patched:
"""
def delete_selected_tree(modeladmin, request, queryset):
    # Wrap the queryset's delete method so that the model's delete() method
    # is called for each object being deleted. This is slower than a bulk delete,
    # but ensures that MPTT keeps the tree structure intact.
    def wrap_delete(delete):
        def _wrapped_delete():
            for obj in queryset:
                # Reload object because tree attributes may be out of date 
                obj = obj.__class__.objects.get(pk=obj.pk)
                # Then delete
                obj.delete()
        return wraps(delete)(_wrapped_delete)
    queryset.delete = wrap_delete(queryset.delete)
    return actions.delete_selected(modeladmin, request, queryset)
delete_selected_tree.short_description = _("Delete selected %(verbose_name_plural)s")


class MPTTModelAdmin(object):
    """
    Patches the delete action so that the tree is updated properly. 
    """
    def get_actions(self, request):
        actions = super(MPTTModelAdmin, self).get_actions(request)
        actions['delete_selected'] = (delete_selected_tree, 'delete_selected', delete_selected_tree.short_description) # replace the default delete action
        return actions
