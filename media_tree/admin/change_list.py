import django
from media_tree.models import FileNode
from media_tree.admin.utils import get_current_request, is_search_request,  \
    get_request_attr
    
try:
    from mptt.admin import MPTTChangeList
except ImportError:
    # Legacy mptt support
    from media_tree.contrib.legacy_mptt_support.admin import MPTTChangeList

from django.db import models

    
class MediaTreeChangeList(MPTTChangeList):

    def is_filtered(self, request):
        return is_search_request(request) or self.params

    def __init__(self, request, *args, **kwargs):
        super(MediaTreeChangeList, self).__init__(request, *args, **kwargs)
        # self.parent_folder is set in get_query_set()
        self.title = self.parent_folder.name if self.parent_folder else FileNode.get_top_node().name

    # TODO: Move filtering by open folders here
    def get_query_set(self, request=None):

        # request arg was added in django r16144 (after 1.3)
        if request is not None and django.VERSION >= (1, 4):
            qs = super(MPTTChangeList, self).get_query_set(request)
        else:
            qs = super(MPTTChangeList, self).get_query_set()
            request = get_current_request()

        # Pagination should be disabled by default, since it interferes
        # with expanded folders and might display them partially.
        # However, filtered results are presented as a flat list and 
        # should be paginated.
        pagination_enabled = self.is_filtered(request)
        if not pagination_enabled:
            self.show_all = True

        # filter by currently expanded folders if list is not filtered by extension or media_type
        self.parent_folder = self.model_admin.get_parent_folder(request)
        if self.parent_folder and not pagination_enabled:
            if self.parent_folder.is_top_node():
                expanded_folders_pk = self.model_admin.get_expanded_folders_pk(request)
                if expanded_folders_pk:
                    qs = qs.filter(models.Q(parent=None) | models.Q(parent__pk__in=expanded_folders_pk))
                else:
                    qs = qs.filter(parent=None)
            else:
                qs = qs.filter(parent=self.parent_folder)

        if request is not None and self.is_filtered(request):
            return qs.order_by('name')
        else:
            # always order by (tree_id, left)
            tree_id = qs.model._mptt_meta.tree_id_attr
            left = qs.model._mptt_meta.left_attr
            return qs.order_by(tree_id, left)

    def get_results(self, request):
        """
        Temporarily decreases the `level` attribute of all search results in
        order to prevent indendation when displaying them.
        """
        super(MediaTreeChangeList, self).get_results(request)
        try:
            reduce_levels = abs(int(get_request_attr(request, 'reduce_levels', 0)))
        except TypeError:
            reduce_levels = 0
        is_filtered = self.is_filtered(request)
        if is_filtered or reduce_levels:
            for item in self.result_list:
                item.prevent_save()
                item.actual_level = item.level
                if is_filtered:
                    item.reduce_levels = item.level
                    item.level = 0
                else:
                    item.reduce_levels = reduce_levels
                    item.level = max(0, item.level - reduce_levels)
        

