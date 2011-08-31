from media_tree.admin.utils import get_current_request, is_search_request,  \
    get_request_attr
    
try:
    from mptt.admin import MPTTChangeList
except ImportError:
    # Legacy mptt support
    from media_tree.contrib.legacy_mptt_support.admin import MPTTChangeList
    
class MediaTreeChangeList(MPTTChangeList):

    def is_filtered(self, request):
        return is_search_request(request) or self.params

    # TODO: Move filtering by open folders here
    def get_query_set(self, request=None):
        # request arg was added in django r16144 (after 1.3)
        if request is not None and django.VERSION >= (1, 4):
            qs = super(MPTTChangeList, self).get_query_set(request)
        else:
            qs = super(MPTTChangeList, self).get_query_set()
            request = get_current_request()

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
        reduce_levels = get_request_attr(request, 'parent_level', 0)
        is_filtered = self.is_filtered(request)
        if is_filtered or reduce_levels:
            for item in self.result_list:
                item.prevent_save()
                item.actual_level = item.level
                if is_filtered:
                    item.level = 0
                else:
                    item.level = max(0, item.level - reduce_levels)
        

