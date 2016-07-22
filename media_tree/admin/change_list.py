import django
from media_tree.models import FileNode
from media_tree.admin.utils import get_current_request, is_search_request,  \
    set_request_attr, get_request_attr
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.http import Http404


class MediaTreeChangeList(ChangeList):

    def is_filtered(self, request):
        return is_search_request(request) or self.params

    def __init__(self, request, *args, **kwargs):
        super(MediaTreeChangeList, self).__init__(request, *args, **kwargs)
        # self.parent_folder is set in get_queryset()
        # REMOVED:
        # self.title = self.parent_folder.name if self.parent_folder else FileNode.get_top_node().name

    @staticmethod
    def init_request(request):
        if 'parent' in request.GET:
            mutable_get = request.GET.copy()
            try:
                parent_pk = int(mutable_get['parent'])
                parent = FileNode.objects.get(pk=parent_pk, node_type=FileNode.FOLDER)
            except (ValueError, FileNode.DoesNotExist):
                raise Http404
            del mutable_get['parent']
            request.GET = mutable_get
        else:
            parent = None
        set_request_attr(request, 'parent', parent)

    # TODO: Move filtering by open folders here
    def get_queryset(self, request=None):

        parent_folder = get_request_attr(request, 'parent')
        if parent_folder:
            self.root_queryset = parent_folder.get_descendants()

        qs = super(MediaTreeChangeList, self).get_queryset(request)

        # Pagination should be disabled by default, since it interferes
        # with expanded folders and might display them partially.
        # However, filtered results are presented as a flat list and
        # should be paginated.
        pagination_enabled = self.is_filtered(request)
        if not pagination_enabled:
            self.show_all = True

        # filter by currently expanded folders if list is not filtered by extension or media_type
        """
        # TODO:
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
        """

        """
        # TODO:
        if request is not None and self.is_filtered(request):
            return qs.order_by('name')
        else:
            # always order by (tree_id, left)
            tree_id = qs.model._mptt_meta.tree_id_attr
            left = qs.model._mptt_meta.left_attr
            return qs.order_by(tree_id, left)
        """

        return qs

    def get_results(self, request):
        """
        Temporarily decreases the `depth` attribute of all search results in
        order to prevent overly deep indendation when displaying them.
        """
        super(MediaTreeChangeList, self).get_results(request)
        try:
            decrease_depth = abs(int(get_request_attr(request, 'decrease_depth', 0)))
        except TypeError:
            decrease_depth = 0
        is_filtered = self.is_filtered(request)
        if is_filtered or decrease_depth:
            for item in self.result_list:
                item.prevent_save()
                item.actual_depth = item.depth
                if is_filtered:
                    item.decrease_depth = item.level
                    item.depth = 0
                else:
                    item.decrease_depth = decrease_depth
                    item.depth = max(0, item.depth - decrease_depth)
