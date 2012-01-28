from media_tree.models import FileNode
from media_tree.contrib.views.mixin_base import PluginMixin
from media_tree.contrib.views.helpers import FolderLinkBase
from media_tree.utils.filenode import get_file_link, get_merged_filenode_list, get_nested_filenode_list
from django.views.generic.list import ListView
from django.utils.translation import ugettext_lazy as _
from django.http import Http404
from django.core.exceptions import PermissionDenied


LISTING_MERGED = 'M'
LISTING_NESTED = 'N'


class FileNodeListingView(ListView):
    """
    View class for implementing views that render a file listing. This class is
    based on Django's generic ``ListView``. Please refer to the respective
    Django documentation on subclassing and customizing `Class-based generic
    views <https://docs.djangoproject.com/en/dev/topics/class-based-views/>`_.

    The following example ``urls.py`` would implement a view listing a folder
    with the path ``some/folder`` and its immediate children, but not
    descendants deeper down the hierarchy::

        from media_tree.models import FileNode
        from media_tree.contrib.views.listing import FileNodeListingView
        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^listing/$', FileNodeListingView.as_view(
                # notice that queryset can be any iterable, for instance a list:
                queryset=[FileNode.objects.get_by_path('some/folder')],
                max_depth=2
            )),
        )

    The folder tree that is rendered does not have to be identical to the actual
    tree in your media library. Instead, you can group arbitrary nodes, or
    output a merged (flat) list. The following example would display all
    descendants of two folders in a merged, one-dimensional list, as if they
    were all in the same folder::

        from media_tree.models import FileNode
        from media_tree.contrib.views.listing import FileNodeListingView, LISTING_MERGED
        from django.conf.urls.defaults import *

        urlpatterns = patterns('',
            (r'^listing/$', FileNodeListingView.as_view(
                # notice that queryset can be any iterable, for instance a list:
                queryset=FileNode.objects.filter(pk__in=(1, 2)),
                list_type=LISTING_MERGED
            )),
        )

    """

    list_type = LISTING_NESTED
    """ Type of the listing, either :attr:`LISTING_NESTED` or :attr:`LISTING_MERGED`. """

    list_max_depth = None
    """ Max depth of the tree for descendants to be included. """

    list_filter_media_types = None
    """ An iterable containing media types to filter for. """

    include_descendants = True
    """ 
    Toggles the inclusion of all descendants of objects in :attr:`queryset`. Note that
    this is ``True`` by default, meaning a full nested folder and file tree will be 
    rendered.
    """

    template_name = 'media_tree/filenode_list.html'
    """ Name of the template. """

    context_object_name = 'node_list'
    """ Designates the name of the variable to use in the context. """

    def get_render_object_list(self, object_list, folder_list=False, processors=None, exclude_media_types=None, max_depth=None):
        if max_depth is None:
            if self.list_max_depth is None:
                if not self.include_descendants:
                    max_depth = 1
                else:
                    max_depth = None
            else:
                max_depth = self.list_max_depth

        if not folder_list:
            filter_media_types = self.list_filter_media_types
        else:
            filter_media_types = (FileNode.FOLDER,)

        if not folder_list and self.list_type == LISTING_MERGED:
            list_method = get_merged_filenode_list
            if not exclude_media_types:
                exclude_media_types = ()
            exclude_media_types += (FileNode.FOLDER,)
        else:
            list_method = get_nested_filenode_list

        return list_method(object_list, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types,
            processors=processors, max_depth=max_depth, ordering=['position', 'name'])

    def get_context_data(self, **kwargs):
        if not 'object_list' in kwargs:
            kwargs['object_list'] = self.get_queryset()
        context = super(FileNodeListingView, self).get_context_data(**kwargs)
        context[self.context_object_name] = self.get_render_object_list(context.pop(self.context_object_name))
        
        if not 'title' in context:
            context['title'] = _('Media objects')

        return context


class FileNodeListingFilteredByFolderView(FileNodeListingView):
    """
    Extended listing View class for implementing a file listing that can be 
    filtered by parent folder and render a folder tree next to the list of
    files in the currently selected folder. 
    """

    filter_by_parent_folder = True

    parent_folder = None

    folder_queryset = None

    folder_pk_param_name = 'folder'
    """ 
    Name of the parameter added to the query string for the folder filter. 
    """

    auto_merge_single_folder = True
    """ 
    Specifies whether the folder list should be suppressed and the list merged
    if there is only one level of hierarchy in ``queryset``. 
    """

    def init_parent_folder(self):
        if self.request:
            GET = self.request.GET
        else:
            GET = {}
        pk = self.kwargs.get('pk', None) or GET.get(self.folder_pk_param_name)
        path = self.kwargs.get('path', None)        
        folder_lookup = None
        if pk is not None and len(pk):
            folder_lookup = {'pk': pk} 
        elif path is not None and len(path):
            folder_lookup = {'path': path} 
        if not folder_lookup is None:
            try:
                self.parent_folder = FileNode.folders.get(**folder_lookup)
            except FileNode.DoesNotExist:
                raise Http404()

    def validate_parent_folder(self):
        top_node_pks = [node.pk for node in self.queryset]
        if not self.parent_folder.pk in top_node_pks:
            selected_node = self.parent_folder.get_ancestors().get(pk__in=top_node_pks)                        
            if not self.include_descendants or  \
                (self.list_max_depth > 0 and  \
                self.parent_folder.level - selected_node.level >= self.list_max_depth - 1):
                    raise PermissionDenied

    def can_filter_by_parent_folder(self):
        return self.list_type == LISTING_NESTED and self.filter_by_parent_folder

    def get_queryset(self, *args, **kwargs):
        queryset = super(FileNodeListingFilteredByFolderView, self).get_queryset(*args, **kwargs)
        if self.can_filter_by_parent_folder():
            if not self.auto_merge_single_folder or  \
                (len(queryset) == 1 and queryset[0].is_folder()):
                    self.init_parent_folder()
                    self.folder_queryset = queryset
                    if self.parent_folder:
                        try:
                            self.validate_parent_folder()
                        except (PermissionDenied, FileNode.DoesNotExist):
                            raise Http404('Invalid parent folder')
                        return self.parent_folder.get_children()
            else:
                self.list_type = LISTING_MERGED

        return queryset

    def get_render_object_list(self, object_list, folder_list=False, processors=None, exclude_media_types=None, max_depth=None):
        if not folder_list and self.folder_queryset:
            max_depth = 1
            if not exclude_media_types:
                exclude_media_types = ()
            exclude_media_types += (FileNode.FOLDER,)

        return super(FileNodeListingFilteredByFolderView, self).get_render_object_list(
            object_list, folder_list, processors, exclude_media_types, max_depth)

    def get_context_data(self, **kwargs):
        context = super(FileNodeListingFilteredByFolderView, self).get_context_data(**kwargs)
        
        if self.folder_queryset:
            class FolderLink(FolderLinkBase):
                selected_folder = self.parent_folder
                folder_param_name = self.folder_pk_param_name
                count_children = True
                filter_media_types = self.list_filter_media_types
            folder_list = self.get_render_object_list(self.folder_queryset, folder_list=True,
                processors=(FolderLink,))
            if len(folder_list) > 0:
                context['folder_list'] = folder_list

        return context


class FileNodeListingMixin(PluginMixin):

    view_class = FileNodeListingView
    """ The view class instantiated by ``get_listing_view()``. """

    def get_listing_view(self, request, queryset, opts=None):
        """
        Instantiates and returns the view class that will generate the
        actual context for this plugin.

        ``queryset`` can be an actual QuerySet or any iterable.
        """
        view = self.get_view(request, self.view_class, opts)
        view.queryset = queryset
        return view


class FileNodeListingFilteredByFolderMixin(FileNodeListingMixin):

    view_class = FileNodeListingFilteredByFolderView
    """ The view class instantiated by ``get_listing_view()``. """
