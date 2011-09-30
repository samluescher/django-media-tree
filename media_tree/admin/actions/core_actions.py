from media_tree.models import FileNode
from media_tree.admin.actions.utils import get_actions_context
from media_tree.admin.actions.forms import MoveSelectedForm, CopySelectedForm, ChangeMetadataForSelectedForm
from media_tree.forms import MetadataForm
from django import forms
from django.utils.translation import ungettext, ugettext as _
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.admin import helpers
from django.http import HttpResponse, HttpResponseRedirect

def get_current_node(form):
    selected_nodes = form.get_selected_nodes()
    if len(selected_nodes) > 0:
        current_node = selected_nodes[0].parent
    if not current_node:
        return FileNode.get_top_node()
    else:
        return current_node

def filenode_admin_action(modeladmin, request, queryset, form_class, extra_context, success_messages, form_initial=None, is_recursive=True):
    """
    """
    execute = request.POST.get('execute')
    current_node = None
    if execute:
        form = form_class(queryset, request.POST)
        if form.is_valid():
            form.save()
            redirect_node = form.cleaned_data.get('target_node', None)
            if not redirect_node:
                redirect_node = get_current_node(form)
            request.user.message_set.create(message=ungettext(success_messages[0], success_messages[1], form.success_count) % {
                'count': form.success_count, 
                'verbose_name': FileNode._meta.verbose_name, 
                'verbose_name_plural': FileNode._meta.verbose_name_plural
            })
            return HttpResponseRedirect(redirect_node.get_admin_url())
    if not execute:
        form = form_class(queryset, initial=form_initial)

    context = get_actions_context(modeladmin)
    context.update(extra_context)
    context.update({
        'breadcrumbs_title': context['title'],
        'form': form,
        'node': get_current_node(form)
    })
    if not 'node_list' in context:
        if is_recursive:
            max_depth = None
        else:
            max_depth = 1
        context['node_list'] = FileNode.get_nested_list(form.selected_nodes, 
            processors=[FileNode.get_admin_link], max_depth=max_depth)
    return render_to_response('admin/media_tree/filenode/actions_form.html', context, context_instance=RequestContext(request))

def move_selected(modeladmin, request, queryset):
    success_messages = ['%(count)i %(verbose_name)s moved.', '%(count)i %(verbose_name_plural)s moved.']
    extra_context = ({
        'title': _('Move media objects'),
        'submit_label': _('Move'),
    })
    return filenode_admin_action(modeladmin, request, queryset, MoveSelectedForm, extra_context, success_messages)
move_selected.short_description = _('Move selected %(verbose_name_plural)s')

def copy_selected(modeladmin, request, queryset):
    success_messages = ['%(count)i %(verbose_name)s copied.', '%(count)i %(verbose_name_plural)s copied.']
    extra_context = ({
        'title': _('Copy media objects'),
        'submit_label': _('Copy'),
    })
    return filenode_admin_action(modeladmin, request, queryset, CopySelectedForm, extra_context, success_messages)
copy_selected.short_description = _('Copy selected %(verbose_name_plural)s')

def change_metadata_for_selected(modeladmin, request, queryset):
    # TODO Use AdminDateTimeWidget etc
    # TODO Should be able to leave required fields blank if confirmation not checked
    
    # Compare all nodes in queryset in order to display initial values
    # in form that have an identical value for all nodes 
    initial = {}
    for node in queryset:
        for field in node._meta.fields:
            if field.editable:
                value = getattr(node, field.name)
                if not field.name in initial:
                    initial[field.name] = value
                elif value != initial[field.name]:
                    initial[field.name] = None

    success_messages = ['%(count)i %(verbose_name)s changed.', '%(count)i %(verbose_name_plural)s changed.']
    extra_context = ({
        'title': _('Change metadata for several media objects'),
        'submit_label': _('Overwrite selected fields'),
    })
    return filenode_admin_action(modeladmin, request, queryset, 
        ChangeMetadataForSelectedForm, extra_context, success_messages, form_initial=initial)
change_metadata_for_selected.short_description = _('Change metadata for selected %(verbose_name_plural)s')
