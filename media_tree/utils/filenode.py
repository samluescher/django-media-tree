from media_tree import media_types
from django.template.defaultfilters import filesizeformat
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.db import models
from copy import copy

# TODO: There may be some benefits in this function returning a lazily evaluated object, like QuerySets:
#    https://docs.djangoproject.com/en/dev/ref/models/querysets/#when-querysets-are-evaluated

def __get_filenode_list(nodes, filter_media_types=None, exclude_media_types=None, filter=None, ordering=None, processors=None, list_method='append', max_depth=None, max_nodes=None, _depth=1, _node_count=0):

    if isinstance(nodes, models.query.QuerySet):
        # pre-filter() and exclude() on QuerySet for fewer iterations
        if filter_media_types:
            nodes = nodes.filter(media_type__in=tuple(filter_media_types)+(media_types.FOLDER,))
        if exclude_media_types:
            for exclude_media_type in exclude_media_types:
                if exclude_media_type != media_types.FOLDER:
                    nodes = nodes.exclude(media_type__exact=exclude_media_type)
        if filter:
            nodes = nodes.filter(**filter)
        if ordering:
            nodes = nodes.order_by(*ordering)

    result_list = []
    if max_depth is None or _depth <= max_depth:
        for node in nodes:
            if max_nodes and _node_count > max_nodes:
                break
            # recursively get child nodes
            if node.node_type == media_types.FOLDER and node.get_descendant_count() > 0:
                child_nodes = __get_filenode_list(node.get_children().all(), filter_media_types=filter_media_types, exclude_media_types=exclude_media_types,
                    filter=filter, ordering=ordering, processors=processors, list_method=list_method, max_depth=max_depth, max_nodes=max_nodes,
                    _depth=_depth + 1, _node_count=_node_count)
                child_count = len(child_nodes)
            else:
                child_count = 0
            # add node itself if it matches the filter criteria, or, if result is a nested list
            # (`list_method == 'append'`), it must include folders in order to make sense,
            # but folders will only be added if they have any descendants matching the filter criteria
            if ((not filter_media_types or node.media_type in filter_media_types) \
                and (not exclude_media_types or not node.media_type in exclude_media_types)) \
                or (child_count > 0 and list_method == 'append' and (max_depth is None or _depth < max_depth)):
                    _node_count += 1
                    if processors:
                        node_copy = copy(node)
                        for processor in processors:
                            node_copy = processor(node_copy)
                        if node_copy != None:
                            result_list.append(node_copy)
                    else:
                        result_list.append(node)
            # add child nodes using appropriate list method. `append` will result in a nested list,
            # while `extend` produces a merged (flat) list.
            if child_count > 0:
                _node_count += child_count
                method = getattr(result_list, list_method)
                method(child_nodes)

    return result_list

def get_nested_filenode_list(nodes, filter_media_types=None, exclude_media_types=None, filter=None, ordering=None, processors=None, max_depth=None, max_nodes=None):
    """
    Returns a nested list of nodes, applying optional filters and processors to each node.
    Nested means that the resulting list will be multi-dimensional, i.e. each item in the list
    that is a folder containing child nodes will be followed by a sub-list containing those
    child nodes.

    Example of returned list::

        [
            <FileNode: Empty folder>,
            <FileNode: Photo folder>,
                [<FileNode: photo1.jpg>, <FileNode: photo2.jpg>,
                 <FileNode: another subfolder>],
                    [<FileNode: photo3.jpg>]
            <FileNode: file.txt>
        ]

    You can use this list in conjunction with Django's built-in
    list template filters to output nested lists in templates::

        {{ some_nested_list|unordered_list }}

    Using the FileNode structure from the example, the above line would result in the following output::

        <ul>
            <li>Empty folder</li>
            <li>Photo folder
                <ul>
                    <li>photo1.jpg</li>
                    <li>photo2.jpg</li>
                    <li>another subfolder
                        <ul>
                            <li>photo3.jpg</li>
                        </ul>
                    </li>
                </ul>
            </li>
            <li>file.txt</li>
        </ul>

    :param nodes: A QuerySet or list of FileNode objects
    :param filter_media_types: A list of media types to include in the resulting list, e.g. ``media_types.DOCUMENT``
    :param exclude_media_types: A list of media types to exclude from the resulting list
    :param filter: A dictionary of kwargs to be applied with ``QuerySet.filter()`` if ``nodes`` is a QuerySet
    :param processors: A list of callables to be applied to each node, e.g. ``force_unicode`` if you want the list to contain strings instead of FileNode objects
    :param max_depth: Can be used to limit the recursion depth (unlimited by default)
    :param max_nodes: Can be used to limit the number of items in the resulting list (unlimited by default)
    """
    return __get_filenode_list(nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types,
        filter=filter, ordering=ordering, processors=processors, list_method='append', max_depth=max_depth, max_nodes=max_nodes)

def get_merged_filenode_list(nodes, filter_media_types=None, exclude_media_types=None, filter=None, ordering=None, processors=None, max_depth=None, max_nodes=None):
    """
    Almost the same as :func:`get_nested_filenode_list`, but returns a flat (one-dimensional) list.
    Using the same QuerySet as in the example for `get_nested_filenode_list`, this method would return::

        [
            <FileNode: Empty folder>,
            <FileNode: Photo folder>,
            <FileNode: photo1.jpg>,
            <FileNode: photo2.jpg>,
            <FileNode: photo3.jpg>,
            <FileNode: file.txt>
        ]

    """
    return __get_filenode_list(nodes, filter_media_types=filter_media_types, exclude_media_types=exclude_media_types,
        filter=filter, ordering=ordering, processors=processors, list_method='extend', max_depth=max_depth, max_nodes=max_nodes)

# TODO: This would be better as a template filter, but its params are to complicated
def get_file_link(node, use_metadata=False, include_size=False, include_extension=False, include_icon=False, href=None, extra_class='', extra=''):
    """
    Returns a formatted HTML link tag to the FileNode's file, optionally including some meta information about the file.
    """
    link_text = None
    if use_metadata:
        link_text = node.get_metadata_display()
    if not link_text:
        link_text = node.__unicode__()
    if node.node_type != media_types.FOLDER:
        if include_extension:
            if extra != '':
                extra += ' '
            extra = '<span class="file-extension">%s</span>' % node.extension.upper()
        if include_size:
            if extra != '':
                extra += ', '
            extra += '<span class="file-size">%s</span>' % filesizeformat(node.size)
        if extra:
            extra = ' <span class="details">(%s)</span>' % extra
        link_class = 'file %s' % node.extension
    else:
        link_class = 'folder'
    if extra_class:
        link_class = '%s %s' % (link_class, extra_class)

    if node.node_type != media_types.FOLDER and not href:
        href = node.file.url

    icon = ''
    if include_icon:
        icon_file = node.get_icon_file()
        if icon_file:
            icon = '<span class="icon"><img src="%s" alt="%s" /></span>' % (
                icon_file.url, node.alt)

    if href:
        link = u'<a class="%s" href="%s">%s%s</a>%s' % (
            link_class, href, icon, link_text, extra)
    else:
        link = u'<span class="%s">%s%s</span>%s' % (
            link_class, icon, link_text, extra)

    return force_unicode(mark_safe(link))
