from media_tree.utils.filenode import get_file_link

class FolderLinkBase(object):

    filter_media_types = None
    selected_folder = None
    folder_param_name = None
    count_descendants = False
    count_children = False

    def __init__(self, node):
        self.node = node

    def get_link_content(self):
        return self.node.__unicode__()

    # TODO: This should include the default image for each folder as its icon
    def __unicode__(self):

        if self.count_descendants:
            count_qs = self.node.get_descendants()
        elif self.count_children:
            count_qs = self.node.get_children()
        else:
            count_qs = None

        if count_qs:
            if self.filter_media_types:
                count_qs = count_qs.filter(media_type__in=self.filter_media_types)
            count = ' <span class="count">(%i)</span>' % count_qs.count()
        else:
            count = ''
        extra_class = ''
        if self.node == self.selected_folder:
            extra_class = 'selected'
        query = '?%s=%i' % (self.folder_param_name, self.node.pk)
        return get_file_link(self.node, href=query, extra=count, extra_class=extra_class, include_icon=True)
