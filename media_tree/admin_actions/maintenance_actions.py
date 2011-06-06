from django import forms
from django.utils.translation import ungettext, ugettext as _
from django.template import RequestContext
from media_tree.models import FileNode
from media_tree.admin_actions.utils import get_actions_context
from media_tree.admin_actions.forms import FileNodeActionsForm
from django.shortcuts import render_to_response
from django.contrib.admin import helpers
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from media_tree import app_settings
from django.utils.safestring import mark_safe
import os

FILE_DIR = os.path.join(settings.MEDIA_ROOT, app_settings.get('MEDIA_TREE_UPLOAD_SUBDIR'))
FILE_URL = os.path.join(settings.MEDIA_URL, app_settings.get('MEDIA_TREE_UPLOAD_SUBDIR'))

class OrphanedFilesForm(FileNodeActionsForm):

    success_files = []
    error_files = []

    def __init__(self, queryset, orphaned_files_choices, *args, **kwargs):
        super(OrphanedFilesForm, self).__init__(queryset, *args, **kwargs)
        self.fields['orphaned_selected'] = forms.MultipleChoiceField(label=self.orphaned_selected_label, choices=orphaned_files_choices, widget=forms.widgets.CheckboxSelectMultiple)

class DeleteOrphanedFilesForm(OrphanedFilesForm):

    action_name = 'delete_orphaned_files'
    orphaned_selected_label = _('The following files exist on disk, but are not found in the database')

    def __init__(self, *args, **kwargs):
        super(DeleteOrphanedFilesForm, self).__init__(*args, **kwargs)
        self.fields['confirm'] = confirm = forms.BooleanField(label=_('Yes, I am sure that I want to delete the selected files from disk:'))  

    def save(self):
        """
        Deletes the selected files from storage
        """
        for basename in self.cleaned_data['orphaned_selected']:
            full_path = os.path.join(FILE_DIR, basename)
            try:
                os.remove(full_path)
                self.success_files.append(full_path)
            except OSError:
                self.error_files.append(full_path)

def delete_orphaned_files(modeladmin, request, queryset=None):

    execute = request.POST.get('execute')

    FILE_DIR = os.path.join(settings.MEDIA_ROOT, app_settings.get('MEDIA_TREE_UPLOAD_SUBDIR'))
    files_on_disk = []
    for basename in os.listdir(FILE_DIR):
        full_path = os.path.join(FILE_DIR, basename)
        if not os.path.isdir(full_path):
            files_on_disk.append(full_path)
            
    files_in_db = []
    nodes_with_missing_file_links = []
    for node in FileNode.objects.all():
        if node.node_type == FileNode.FILE:
            files_in_db.append(node.file.path)
            if not node.file.path in files_on_disk:
                link = mark_safe('<a href="%s">%s</a>' % (node.get_admin_url(), node.__unicode__()))
                nodes_with_missing_file_links.append(link)

    orphaned_files_choices = []
    for full_path in files_on_disk:
        link = mark_safe('<a href="%s">%s</a>' % (os.path.join(FILE_URL, basename), full_path))
        if not full_path in files_in_db:
            orphaned_files_choices.append((os.path.basename(full_path), link))

    if len(orphaned_files_choices) == 0 and len(nodes_with_missing_file_links) == 0:
        request.user.message_set.create(message=_('There are no orphaned files.'))
        return HttpResponseRedirect('')

    if execute:
        form = DeleteOrphanedFilesForm(queryset, orphaned_files_choices, request.POST)
        if form.is_valid():
            form.save()
            node = FileNode.get_top_node()
            request.user.message_set.create(message=ungettext('%i file deleted from storage.', '%i files deleted from storage.', len(form.success_files)) % len(form.success_files))
            if form.error_files:
                request.user.message_set.create(message=_('The following files could not be deleted from storage:')+' '+repr(form.error_files))
            return HttpResponseRedirect(node.get_admin_url())

    if not execute:
        if len(orphaned_files_choices) > 0:
            form = DeleteOrphanedFilesForm(queryset, orphaned_files_choices)
        else:
            form = None

    c = get_actions_context(modeladmin)
    c.update({
        'title': _('Orphaned files'),
        'submit_label': _('Delete selected files'),
        'form': form,
        'select_all': 'orphaned_selected',
        'node_list_title': _('The following files in the database do not exist on disk. You should fix these media objects:'),
        'node_list': nodes_with_missing_file_links,
    })
    return render_to_response('admin/media_tree/filenode/actions_form.html', c, context_instance=RequestContext(request))
delete_orphaned_files.short_description = _('Find orphaned files')
delete_orphaned_files.allow_empty_queryset = True

def rebuild_tree(modeladmin, request, queryset=None):
    """
    Rebuilds whole tree in database using `parent` link.
    """
    tree = FileNode.tree.rebuild()
    request.user.message_set.create(message=_('The full tree was rebuilt.'))
    return HttpResponseRedirect('')
rebuild_tree.short_description = _('Rebuild tree')
rebuild_tree.allow_empty_queryset = True
