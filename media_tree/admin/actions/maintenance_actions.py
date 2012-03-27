from media_tree.utils import get_media_storage
from media_tree.media_backends import get_media_backend
from media_tree.models import FileNode
from media_tree.admin.actions.utils import get_actions_context
from media_tree.admin.actions.forms import DeleteOrphanedFilesForm, DeleteCacheFilesForm
from media_tree import settings as app_settings
from django import forms
from django.utils.translation import ungettext, ugettext as _
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin import helpers
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib import messages
from django.utils.safestring import mark_safe
import os


def delete_orphaned_files(modeladmin, request, queryset=None):
    from unicodedata import normalize
    
    execute = request.POST.get('execute')
    media_subdir = app_settings.MEDIA_TREE_UPLOAD_SUBDIR
    
    files_in_storage = []
    storage = get_media_storage()

    files_in_db = []
    nodes_with_missing_file_links = []
    for node in FileNode.objects.filter(node_type=FileNode.FILE):
        path = node.file.path
        # need to normalize unicode path due to https://code.djangoproject.com/ticket/16315
        path = normalize('NFC', path)
        files_in_db.append(path)
        if not storage.exists(node.file):
            link = mark_safe('<a href="%s">%s</a>' % (node.get_admin_url(), node.__unicode__()))
            nodes_with_missing_file_links.append(link)

    files_in_storage = [storage.path(os.path.join(media_subdir, filename))  \
        for filename in storage.listdir(media_subdir)[1]]

    orphaned_files_choices = []
    for file_path in files_in_storage:
        # need to normalize unicode path due to https://code.djangoproject.com/ticket/16315
        file_path = normalize('NFC', file_path)
        if not file_path in files_in_db:
            storage_name = os.path.join(media_subdir, os.path.basename(file_path))
            link = mark_safe('<a href="%s">%s</a>' % (
                storage.url(storage_name), file_path))
            orphaned_files_choices.append((storage_name, link))

    if not len(orphaned_files_choices) and not len(nodes_with_missing_file_links):
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
    messages.success(request, message=_('The node tree was rebuilt.'))
    return HttpResponseRedirect('')
rebuild_tree.short_description = _('Repair node tree')
rebuild_tree.allow_empty_queryset = True


def clear_cache(modeladmin, request, queryset=None):
    """
    """
    from unicodedata import normalize
    
    execute = request.POST.get('execute')
    
    files_in_storage = []
    storage = get_media_storage()

    cache_files_choices = []

    for cache_dir in get_media_backend().get_cache_paths():
        if storage.exists(cache_dir):
            files_in_dir = [storage.path(os.path.join(cache_dir, filename))  \
                for filename in storage.listdir(cache_dir)[1]]
            for file_path in files_in_dir:
                # need to normalize unicode path due to https://code.djangoproject.com/ticket/16315
                file_path = normalize('NFC', file_path)
                storage_name = os.path.join(cache_dir, os.path.basename(file_path))
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
