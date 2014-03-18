from django.contrib.admin import helpers
from media_tree.models import FileNode
from django.utils.translation import ugettext as _

def get_actions_context(modeladmin):
    return {
        'node': FileNode.get_top_node(), # TODO get current folder
        "opts": modeladmin.model._meta,
        #"root_path": modeladmin.admin_site.root_path,
        "app_label": modeladmin.model._meta.app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

def execute_empty_queryset_action(modeladmin, request):
    action = request.POST.get('action', None)
    if request.method == 'POST' and action and not request.POST.get(helpers.ACTION_CHECKBOX_NAME, None):
        actions = modeladmin.get_actions(request)
        if actions.has_key(action):
            func = actions[action][0]
            if getattr(actions[action][0], 'allow_empty_queryset', False):
                return func(modeladmin, request)
            else:
                pass
                # Django 1.2 already creates a message
                # request.user.message_set.create(message=_('No %s selected.') % FileNode._meta.verbose_name_plural)
