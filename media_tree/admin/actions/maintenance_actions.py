from media_tree.utils.maintenance import get_broken_media, get_cache_files
from media_tree.utils import get_media_storage
from media_tree.models import FileNode
from media_tree.admin.actions.utils import get_actions_context
from media_tree.admin.actions.forms import DeleteOrphanedFilesForm, DeleteCacheFilesForm
from django import forms
from django.utils.translation import ungettext, ugettext as _
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin import helpers
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from django.utils.safestring import mark_safe


def delete_orphaned_files(modeladmin, request, queryset=None):
    """
    Deletes orphaned files, i.e. media files existing in storage that are not in the database.
    """
    
    execute = request.POST.get('execute')
    
    storage = get_media_storage()
    broken_node_links = []
    orphaned_files_choices = []

    broken_nodes, orphaned_files = get_broken_media()

    for node in broken_nodes:
        link = mark_safe('<a href="%s">%s</a>' % (node.get_admin_url(), node.__unicode__()))
        broken_node_links.append(link)

    for storage_name in orphaned_files:
        file_path = storage.path(storage_name)
        link = mark_safe('<a href="%s">%s</a>' % (
            storage.url(storage_name), file_path))
        orphaned_files_choices.append((storage_name, link))

    if not len(orphaned_files_choices) and not len(broken_node_links):
        messages.success(request, message=_('There are no orphaned files.'))
        return HttpResponseRedirect('')

    if execute:
        form = DeleteOrphanedFilesForm(queryset, orphaned_files_choices, request.POST)
        if form.is_valid():
            form.save()
            node = FileNode.get_top_node()
            messages.success(request, message=ungettext('Deleted %i file from storage.', 'Deleted %i files from storage.', len(form.success_files)) % len(form.success_files))
            if form.error_files:
                messages.error(request, message=_('The following files could not be deleted from storage:')+' '+repr(form.error_files))
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
        'select_all': 'selected_files',
        'node_list_title': _('The following files in the database do not exist in storage. You should fix these media objects:'),
        'node_list': broken_node_links,
    })
    return render_to_response('admin/media_tree/filenode/actions_form.html', c, context_instance=RequestContext(request))
delete_orphaned_files.short_description = _('Find orphaned files')
delete_orphaned_files.allow_empty_queryset = True


def rebuild_tree(modeladmin, request, queryset=None):
    """
    Rebuilds whole tree in database using `parent` link.
    """
    tree = FileNode.tree.rebuild()
    messages.success(request, message=_('The node tree was rebuilt.'))
    return HttpResponseRedirect('')
rebuild_tree.short_description = _('Repair node tree')
rebuild_tree.allow_empty_queryset = True


def clear_cache(modeladmin, request, queryset=None):
    """
    Clears media cache files such as thumbnails.
    """
    
    execute = request.POST.get('execute')
    
    files_in_storage = []
    storage = get_media_storage()
    cache_files_choices = []
    for storage_name in get_cache_files():
        link = mark_safe('<a href="%s">%s</a>' % (
            storage.url(storage_name), storage_name))
        cache_files_choices.append((storage_name, link))

    if not len(cache_files_choices):
        messages.warning(request, message=_('There are no cache files.'))
        return HttpResponseRedirect('')

    if execute:
        form = DeleteCacheFilesForm(queryset, cache_files_choices, request.POST)
        if form.is_valid():
            form.save()
            node = FileNode.get_top_node()
            message = ungettext('Deleted %i cache file.', 'Deleted %i cache files.', len(form.success_files)) % len(form.success_files)
            if len(form.success_files) == len(cache_files_choices):
                message = '%s %s' % (_('The cache was cleared.'), message)
            messages.success(request, message=message)
            if form.error_files:
                messages.error(request, message=_('The following files could not be deleted:')+' '+repr(form.error_files))
            return HttpResponseRedirect(node.get_admin_url())

    if not execute:
        if len(cache_files_choices) > 0:
            form = DeleteCacheFilesForm(queryset, cache_files_choices)
        else:
            form = None

    c = get_actions_context(modeladmin)
    c.update({
        'title': _('Clear cache'),
        'submit_label': _('Delete selected files'),
        'form': form,
        'select_all': 'selected_files',
    })
    return render_to_response('admin/media_tree/filenode/actions_form.html', c, context_instance=RequestContext(request))

    return HttpResponseRedirect('')
clear_cache.short_description = _('Clear cache')
clear_cache.allow_empty_queryset = True
