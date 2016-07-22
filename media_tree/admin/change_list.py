import django
from media_tree.models import FileNode
from media_tree.admin.utils import get_current_request, is_search_request,  \
    set_special_request_attr, get_special_request_attr
from django.contrib.admin.views.main import ChangeList
from django.db import models
from django.http import Http404


class MediaTreeChangeList(ChangeList):

    def is_filtered(self, request):
        return is_search_request(request) or self.params

    def __init__(self, request, *args, **kwargs):
        super(MediaTreeChangeList, self).__init__(request, *args, **kwargs)
        """
        # TODO: display folder name in title
        self.title = self.parent_folder.name if self.parent_folder else FileNode.get_top_node().name
        """

    @staticmethod
    def init_request(request):
        """
        Initializes the request object with special attributes required for
        tree change lists:

        * The GET parameters may contain a `parent` ID if the response should
          only include descendants of that node. This is used when loading
          subtrees via XHR.
        * If not specified otherwise, the range of depth of the change list's
          results will be set to 1, i.e. only one relative level of depth will
          be displayed for the request, since additional levels should be
          expanded and loaded via XHR.
        """
        # When filtering by `parent`, we replace the request's GET dictionary
        # with a copy that does not contain said parameter so as not to confuse
        # Django admin's regular filter mechanism.
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
        # Store the retrieved parent node as special request attribute
        set_special_request_attr(request, 'parent', parent)

        # If depth limiting was not already specified, set it to 1 to only
        # include one level of depth in the change list's queryset.
        # To disable depth filtering, the request object can be modified by
        # setting the special request attribute `max_depth` to 0 beforehand.
        if get_special_request_attr(request, 'max_depth', None) is None:
            set_special_request_attr(request, 'max_depth', 1)

    def get_queryset(self, request=None):

        # filter by parent folder is defined by the special request attribute
        parent_folder = get_special_request_attr(request, 'parent')
        if parent_folder:
            self.root_queryset = parent_folder.get_descendants()

        qs = super(MediaTreeChangeList, self).get_queryset(request)

        # filter by maximum relative depth as defined by the special request
        # attribute
        max_depth = get_special_request_attr(request, 'max_depth')
        if max_depth:
            if parent_folder:
                qs = qs.filter(depth=parent_folder.depth + max_depth)
            else:
                qs = qs.filter(depth=max_depth)

        # Pagination should be disabled by default, since it interferes
        # with expanded folders and might display them partially.
        # However, filtered results are presented as a flat list and
        # should be paginated.
        pagination_enabled = self.is_filtered(request)
        if not pagination_enabled:
            self.show_all = True

        # filter by currently expanded folders if list is not filtered by extension or media_type
        """
        # TODO: filtering by expanded folders as stored in session
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
        super(MediaTreeChangeList, self).get_results(request)

        # Temporarily decreases the `depth` attribute of all search results in
        # order to prevent overly deep indendation when displaying them.
        try:
            decrease_depth = abs(int(get_special_request_attr(request, 'decrease_depth', 0)))
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
