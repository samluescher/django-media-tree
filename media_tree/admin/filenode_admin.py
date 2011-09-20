# ** next **
# TODO: Fix search inconsistencies. For example: Opening a folder and then searching for its name presents it with an expanded marker, but no children.
# TODO: Search results should be ordered alphabetically
# TODO: Folders shouldn't be expandable in search
# TODO: Filter is not working correctly: Should work like search and show a flat list including ALL files, not just those in opened folders
#   --> achieved moving open folder filtering to MediaTreeChangeList
# TODO: http://localhost:8000/admin/media_tree/filenode/?folder_id=1 should have zero indent, AJAX-loaded items can be auto-indented
#       TODO: Opening in new window etc. is currently unclear. Possibly ?folder_id=1 should be replaced with folder-path (real names!)
#   --> Actually, /folder_id/ should show zero-indented list and replace ?folder_id --> solves many problems
#
# TODO: Metadata output is too wrapped
# TODO: Add icon for change and add folder
# TODO: Change default folder icons to open source or custom graphics
#
# ** maybe **
# TODO: Refactor PIL stuff, width|height as extension? 
# TODO: Refactor SWFUpload stuff as extension. This would require signals calls
#   to be called in the FileNodeAdmin view methods. 
# TODO: Make renaming of files possible.
# TODO: When files are copied, they lose their human-readable name. Should actually create "File Copy 2.txt".
# TODO: Order by column (within parent) should be possible
        
from media_tree.fields import FileNodeChoiceField
from media_tree.models import FileNode
from media_tree.forms import FolderForm, FileForm, UploadForm
from media_tree.widgets import AdminThumbWidget
from media_tree.admin.actions import core_actions
from media_tree.admin.actions import maintenance_actions
from media_tree.admin.actions.utils import execute_empty_queryset_action
from media_tree import defaults
from media_tree import settings as app_settings, media_types
from django.template.defaultfilters import filesizeformat

from media_tree.admin.change_list import MediaTreeChangeList
from media_tree.admin.utils import get_current_request, set_current_request,  \
    get_request_attr, set_request_attr, is_search_request
from media_tree.media_backends import get_media_backend

try:
    from mptt.admin import MPTTModelAdmin
except ImportError:
    # Legacy mptt support
    from media_tree.contrib.legacy_mptt_support.admin import MPTTModelAdmin

from mptt.forms import TreeNodeChoiceField
import django
from django.contrib.admin import actions
from django.contrib.admin.options import csrf_protect_m
from django.utils.encoding import force_unicode
from django.contrib import messages
from django.shortcuts import render_to_response
from django.contrib import admin
from django.db import models, transaction
from django.template.loader import render_to_string
from django.contrib.admin.util import unquote
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.urlresolvers import reverse
from django import forms
from django.core.exceptions import ValidationError, ViewDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.contrib.admin.views.main import IS_POPUP_VAR
import os

try:
    # Django 1.2
    from django.views.decorators.csrf import csrf_view_exempt
except ImportError:
    # pre 1.2
    from django.contrib.csrf.middleware import csrf_view_exempt


STATIC_SUBDIR = app_settings.MEDIA_TREE_STATIC_SUBDIR


class FileNodeAdmin(MPTTModelAdmin):
    """The FileNodeAdmin aims to let you manage your media files on the web like
    you are used to on your desktop computer.
    
    Mimicking the file explorer of an operating system, you can browse your
    virtual folder structure, copy and move items, upload more media files, and
    perform many other tasks.
        
    The FileNodeAdmin can be used in your own Django projects, serving as a file
    selection dialog when linking ``FileNode`` objects to your own models.
    
    You can also extend the admin interface in many different fashions to suit
    your custom requirements. Please refer to :ref:`extending` for more
    information about extending Media Tree.
    """
    
    change_list_template = 'admin/media_tree/filenode/mptt_change_list.html'
    
    list_display = app_settings.MEDIA_TREE_LIST_DISPLAY
    list_filter = app_settings.MEDIA_TREE_LIST_FILTER
    #list_display_links = app_settings.MEDIA_TREE_LIST_DISPLAY_LINKS
    search_fields = app_settings.MEDIA_TREE_SEARCH_FIELDS
    ordering = app_settings.MEDIA_TREE_ORDERING_DEFAULT
    mptt_indent_field = 'browse_controls'

    formfield_overrides = {
        models.FileField: {'widget': AdminThumbWidget},
        models.ImageField: {'widget': AdminThumbWidget},
    }

    _registered_actions = []

    class Media:
        js = [
            os.path.join(STATIC_SUBDIR, 'lib/swfupload/swfupload_fp10', 'swfupload.js'),
            os.path.join(STATIC_SUBDIR, 'lib/swfupload/plugins', 'swfupload.queue.js'),
            os.path.join(STATIC_SUBDIR, 'lib/swfupload/plugins', 'swfupload.cookies.js'),
            os.path.join(STATIC_SUBDIR, 'lib/jquery', 'jquery.js'),
            os.path.join(STATIC_SUBDIR, 'lib/jquery', 'jquery.ui.js'),
            os.path.join(STATIC_SUBDIR, 'lib/jquery', 'jquery.cookie.js'),
            os.path.join(STATIC_SUBDIR, 'js', 'admin_enhancements.js'),
            os.path.join(STATIC_SUBDIR, 'js', 'jquery.swfupload_manager.js'),
        ]
        css = {
            'all': (
                os.path.join(STATIC_SUBDIR, 'css', 'swfupload.css'),
                os.path.join(STATIC_SUBDIR, 'css', 'ui.css'),
            )
        }

    def __init__(self, *args, **kwargs):
        super(FileNodeAdmin, self).__init__(*args, **kwargs)
        # http://stackoverflow.com/questions/1618728/disable-link-to-edit-object-in-djangos-admin-display-list-only
        self.list_display_links = (None, )

    @staticmethod
    def register_action(func, required_perms=None):
        FileNodeAdmin._registered_actions.append({
            'action': func,
            'required_perms': required_perms
        })

    def get_actions(self, request):
        is_popup_var = request.GET.get(IS_POPUP_VAR, None)
        # In ModelAdmin.get_actions(), actions are disabled if the popup var is 
        # present. Since FileNodeAdmin always needs a checkbox, this is 
        # circumvented here:
        if IS_POPUP_VAR in request.GET:
            request.GET = request.GET.copy()
            del request.GET[IS_POPUP_VAR]
        # get all actions from parent
        actions = super(FileNodeAdmin, self).get_actions(request)
        # and restore popup var
        if is_popup_var:
            request.GET[IS_POPUP_VAR] = is_popup_var

        # Replaces bulk delete method with method that properly updates tree attributes
        # when deleting.
        if 'delete_selected' in actions:
            actions['delete_selected'] = (self.delete_selected_tree, 'delete_selected', _("Delete selected %(verbose_name_plural)s"))

        for action_def in FileNodeAdmin._registered_actions:
            if not action_def['required_perms'] or request.user.has_perms(action_def['required_perms']):
                action = self.get_action(action_def['action'])
                actions[action[1]] = action

        return actions

    def delete_selected_tree(self, modeladmin, request, queryset):
        """
        Deletes multiple instances and makes sure the MPTT fields get recalculated properly.
        (Because merely doing a bulk delete doesn't trigger the post_delete hooks.)
        """
        # If the user has not yet confirmed the deletion, call the regular delete 
        # action that will present a confirmation page
        if not request.POST.get('post'):
            return actions.delete_selected(modeladmin, request, queryset)
        # Otherwise, delete objects one by one
        n = 0
        for obj in queryset:
            obj.delete()
            n += 1
        self.message_user(request, _("Successfully deleted %s items." % n))

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return MediaTreeChangeList

    def queryset(self, request):
        #qs = super(FileNodeAdmin, self).queryset(request)
        qs = FileNode.tree.all()
        parent_folder = self.get_parent_folder(request)
        if parent_folder:
            if parent_folder.is_top_node():
                expanded_folders_pk = self.get_expanded_folders_pk(request)
                if expanded_folders_pk:
                    qs = qs.filter(models.Q(parent=None) | models.Q(parent__pk__in=expanded_folders_pk))
                else:
                    qs = qs.filter(parent=None)
            else:
                qs = qs.filter(parent=parent_folder)
        
        return qs

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if not change:
            if not obj.node_type:
                obj.node_type = get_request_attr(request, 'save_node_type', None)
            if not obj.parent:
                obj.parent = get_request_attr(request, 'save_node_parent', None)
        super(FileNodeAdmin, self).save_model(request, obj, form, change)

    def metadata_check(self, node):
        icon = _boolean_icon(node.has_metadata_including_descendants())
        return '<span class="metadata"><span class="metadata-icon">%s</span><span class="displayed-metadata">%s</span></span>' % (
            icon, node.get_metadata_formatted())
    metadata_check.short_description = _('Metadata')
    metadata_check.allow_tags = True

    def expand_collapse(self, node):
        request = get_current_request()
        if not is_search_request(request):
            rel = 'parent:%i' % node.parent_id if node.parent_id else ''
        else:
            rel = ''
        if hasattr(node, 'actual_level'):
            actual_level = '&parent_level=%i' % node.actual_level
        else:
            actual_level = ''
        if node.is_folder():
            return '<a href="?folder_id=%i%s" class="folder-toggle" rel="%s"><span>%s</span></a>' %  \
                (node.pk, actual_level, rel, '+')
        else:
            return '<a class="folder-toggle dummy" rel="%s">&nbsp;</a>' % (rel,)
    expand_collapse.short_description = ''
    expand_collapse.allow_tags = True
            
    def admin_preview(self, node, icons_only=False):
        template = 'admin/media_tree/filenode/includes/preview.html'
        if not get_media_backend():
            icons_only = True
            template = 'html/media_tree/filenode/includes/icon.html'
            # TODO SPLIT preview.html in two: one that doesn't need media backend!
        preview = render_to_string(template, {
            'node': node,
            'preview_file': node.get_icon_file() if icons_only else node.get_preview_file(),
            'class': 'collapsed' if node.is_folder() else ''
        })
        if node.is_folder():
            preview += render_to_string(template, {
                'node': node,
                'preview_file': node.get_preview_file(default_name='_folder_expanded'),
                'class': 'expanded'
            })
        return preview
    admin_preview.short_description = ''
    admin_preview.allow_tags = True

    def admin_link(self, node, include_preview=False):
        return '<a href="%s">%s<span class="name">%s</span></a>' % (
            node.get_admin_url(), self.admin_preview(node) if include_preview else '', node.name)

    def node_tools(self, node):
        tools = ''
        tools += '<li><a class="change" href="%s">%s</a></li>' % (reverse('admin:media_tree_filenode_change', args=(node.pk,)), _('change')) 
        #if node.is_folder():
        #    tools += '<li><a class="add-folder" href="%s?folder_id=%s">%s</a></li>' % (
        #        reverse('admin:media_tree_filenode_add_folder', args=()), str(node.pk), _('add folder')) 
        return '<ul class="node-tools">%s</ul>' % tools
    node_tools.short_description = ''
    node_tools.allow_tags = True

    def anchor_name(self, node):
        return 'node-%i' % node.pk

    def browse_controls(self, node):
        state = ''
        if node.is_folder():
            request = get_current_request()
            state = 'expanded' if self.folder_is_open(request, node) else 'collapsed'
        return '<span id="%s" class="browse-controls %s %s">%s%s</span>' %  \
            (self.anchor_name(node), 'folder' if node.is_folder() else 'file', 
            state, self.expand_collapse(node), self.admin_link(node, True))
    browse_controls.short_description = ''
    browse_controls.allow_tags = True

    def size_formatted(self, node, descendants=True):
        if node.node_type == FileNode.FOLDER:
            if descendants: 
                size = node.get_descendants().aggregate(models.Sum('size'))['size__sum']
            else:
                size = None
        else:
            size = node.size
        if not size:
            return ''
        else:
            return '<span class="filesize">%s</span>' % filesizeformat(size)
    size_formatted.short_description = _('size')
    size_formatted.admin_order_field = 'size'
    size_formatted.allow_tags = True

    def init_parent_folder(self, request):
        folder_id = request.GET.get('folder_id', None) or request.POST.get('folder_id', None)
        parent_level = request.GET.get('parent_level', None) or request.POST.get('parent_level', None)
        if folder_id or parent_level:
            request.GET = request.GET.copy()

        if folder_id:
            try:
                del request.GET['folder_id']
            except KeyError:
                pass
            try:
                parent_folder = FileNode.objects.get(pk=folder_id, node_type=FileNode.FOLDER)
            except FileNode.DoesNotExist:
                raise Http404
        else:
            parent_folder = FileNode.get_top_node()

        if parent_level:
            try:
                del request.GET['parent_level']
            except KeyError:
                pass
            try:
                parent_level = int(parent_level)
            except ValueError:
                parent_level = None

        set_request_attr(request, 'parent_folder', parent_folder)
        set_request_attr(request, 'parent_level', parent_level)

    def get_parent_folder(self, request):
        return get_request_attr(request, 'parent_folder', None)
    
    def get_expanded_folders_pk(self, request):
        expanded_folders_pk = getattr(request, 'expanded_folders_pk', None)
        if not expanded_folders_pk:
            expanded_folders_pk = []
            cookie = request.COOKIES.get('expanded_folders_pk', None)
            if cookie:
                try:
                    expanded_folders_pk = [int(pk) for pk in cookie.split('|')]
                except ValueError:
                    pass
            # for each folder in the expanded_folders_pk, check if all of its 
            # ancestors are also in the list, since a child folder cannot be 
            # opened if its parent folders aren't
            for folder in FileNode.objects.filter(pk__in=expanded_folders_pk):
                for ancestor in folder.get_ancestors():
                    if not ancestor.pk in expanded_folders_pk and folder.pk in expanded_folders_pk:
                        expanded_folders_pk.remove(folder.pk)
            setattr(request, 'expanded_folders_pk', expanded_folders_pk)
            
        return expanded_folders_pk

    def folder_is_open(self, request, folder):
        return folder.pk in self.get_expanded_folders_pk(request)
        
    def set_expanded_folders_pk(self, response, expanded_folders_pk):
        response.set_cookie('expanded_folders_pk', '|'.join([str(pk) for pk in expanded_folders_pk]), path='/')
    
    def changelist_view(self, request, extra_context=None):
        response = execute_empty_queryset_action(self, request)
        if response: 
            return response

        if not is_search_request(request):
            self.init_parent_folder(request)
        parent_folder = self.get_parent_folder(request)
        set_current_request(request)
        
        if not extra_context:
            extra_context = {}
        if app_settings.MEDIA_TREE_SWFUPLOAD:
            middleware = 'media_tree.middleware.SessionPostMiddleware'
            if not middleware in settings.MIDDLEWARE_CLASSES:
                request.user.message_set.create(message=_('You need to put %s in your MIDDLEWARE_CLASSES setting to use SWFUpload.') % middleware)
            else:
                swfupload_upload_url = reverse('admin:media_tree_filenode_upload')
                #swfupload_flash_url = os.path.join(settings.MEDIA_URL, STATIC_SUBDIR, 'lib/swfupload/swfupload_fp10/swfupload.swf')
                swfupload_flash_url = reverse('admin:media_tree_filenode_static_swfupload_swf')
                extra_context.update({
                    'file_types': app_settings.MEDIA_TREE_ALLOWED_FILE_TYPES,
                    'file_size_limit': app_settings.MEDIA_TREE_FILE_SIZE_LIMIT,
                    'swfupload_flash_url': swfupload_flash_url,
                    'swfupload_upload_url': swfupload_upload_url,
                })
        if request.GET.get(IS_POPUP_VAR, None):
            extra_context.update({'select_button': True})
        
        response = super(FileNodeAdmin, self).changelist_view(request, extra_context)
        if isinstance(response, HttpResponse) and parent_folder and not parent_folder.is_top_node():
            expanded_folders_pk = self.get_expanded_folders_pk(request)
            if not parent_folder.pk in expanded_folders_pk:  
                expanded_folders_pk.append(parent_folder.pk)
                self.set_expanded_folders_pk(response, expanded_folders_pk)
        return response

    def folder_view(self, request, object_id, extra_context=None):
        node = FileNode.objects.get(pk=unquote(object_id), node_type=FileNode.FOLDER)
        expand = list(node.get_ancestors())
        expand.append(node)
        response = HttpResponseRedirect('%s#%s' % (reverse('admin:media_tree_filenode_changelist'), self.anchor_name(node))); 
        self.set_expanded_folders_pk(response, [expanded.pk for expanded in expand])
        return response

    def _add_node_view(self, request, form_url='', extra_context=None, node_type=FileNode.FILE):
        self.init_parent_folder(request)
        parent_folder = self.get_parent_folder(request)
        if not extra_context: 
            extra_context = {}
        extra_context.update({
            'node': parent_folder,
            'breadcrumbs_title': _('Add')
        })
        if not parent_folder.is_top_node():
            set_request_attr(request, 'save_node_parent', parent_folder)
        set_request_attr(request, 'save_node_type', node_type)
        return super(FileNodeAdmin, self).add_view(request, form_url, extra_context)

    @csrf_protect_m
    @transaction.commit_on_success
    def add_view(self, request, form_url='', extra_context=None):
        return self._add_node_view(request, form_url, extra_context, 
            node_type=FileNode.FILE)

    @csrf_protect_m
    @transaction.commit_on_success
    def add_folder_view(self, request, form_url='', extra_context=None):
        return self._add_node_view(request, form_url, extra_context, 
            node_type=FileNode.FOLDER)

    def change_view(self, request, object_id, extra_context=None):
        node = FileNode.objects.get(pk=unquote(object_id))
        set_request_attr(request, 'save_node_type', node.node_type)
        if not extra_context: 
            extra_context = {}
        extra_context.update({
            'node': node,
        })
        if node.is_folder():
            extra_context.update({
                'breadcrumbs_title': _('Change')
            })

        return super(FileNodeAdmin, self).change_view(request, object_id, extra_context=extra_context)

    def get_form(self, request, *args, **kwargs):
        if get_request_attr(request, 'save_node_type', None) == FileNode.FOLDER:
            self.form = FolderForm
        else:
            self.form = FileForm
        self.fieldsets = self.form.Meta.fieldsets

        form = super(FileNodeAdmin, self).get_form(request, *args, **kwargs)
        form.parent_folder = self.get_parent_folder(request)
        return form

    # Upload view is exempted from CSRF protection since SWFUpload cannot send cookies (i.e. it can only
    # send cookie values as POST values, but that would render this check useless anyway).
    # However, Flash Player should already be enforcing a same-domain policy.
    @csrf_view_exempt
    def upload_file_view(self, request):
        self.init_parent_folder(request)
        if not self.has_add_permission(request):
            raise PermissionDenied
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                node = FileNode(file=form.cleaned_data['file'], node_type=FileNode.FILE)
                parent_folder = self.get_parent_folder(request)
                if not parent_folder.is_top_node():
                    node.parent = parent_folder
                self.save_model(request, node, None, False)
                # Respond with 'ok' for the client to verify that the upload was successful, since sometimes a failed
                # request would not result in a HTTP error and look like a successful upload.
                # For instance: When requesting the admin view without authentication, there is a redirect to the
                # login form, which to SWFUpload looks like a successful upload request.
                if request.is_ajax() or 'Adobe Flash' in request.META.get('HTTP_USER_AGENT', ''):
                    return HttpResponse("ok", mimetype="text/plain")
                else:
                    messages.info(request, _('Successfully uploaded file %s.') % node.name)
                    return HttpResponseRedirect(reverse('admin:media_tree_filenode_changelist'))
            else:
                if not settings.DEBUG:
                    raise ValidationError
                    return
        if not settings.DEBUG:
            raise ViewDoesNotExist
        else:
            # Form is rendered for troubleshooting SWFUpload. If this form works, the problem is not server-side.
            from django.template import Template, RequestContext
            if request.method != 'POST':
                form = UploadForm()
            return render_to_response('admin/media_tree/filenode/upload_form.html', 
                {'form': form, 'node': self.get_parent_folder(request)}, context_instance=RequestContext(request))

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(FileNodeAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        url_patterns = patterns('',
            # Since Flash Player enforces a same-domain policy, the upload will break if static files 
            # are served from another domain. So the built-in static file view is used for the uploader SWF:
            url(r'^static/swfupload\.swf$', 
                'django.views.static.serve', 
                {'document_root': os.path.join(
                    # Use STATIC_ROOT by default, use MEDIA_ROOT as fallback
                    getattr(settings, 'STATIC_ROOT', getattr(settings, 'MEDIA_ROOT')), 
                    STATIC_SUBDIR), 
                'path': 'lib/swfupload/swfupload_fp10/swfupload.swf'}, 
                name='%s_%s_static_swfupload_swf' % info),
            url(r'^upload/$', 
                self.admin_site.admin_view(self.upload_file_view), 
                name='%s_%s_upload' % info),
            url(r'^add_folder/$', 
                self.admin_site.admin_view(self.add_folder_view),
                name='%s_%s_add_folder' % info),
            url(r'^(.+)/view/$',
                self.admin_site.admin_view(self.folder_view),
                name='%s_%s_folder' % info),
        )
        url_patterns.extend(urls)
        return url_patterns


FileNodeAdmin.register_action(core_actions.copy_selected)
FileNodeAdmin.register_action(core_actions.move_selected)
FileNodeAdmin.register_action(core_actions.change_metadata_for_selected)

FileNodeAdmin.register_action(maintenance_actions.delete_orphaned_files, ('media_tree.manage_filenode',))
FileNodeAdmin.register_action(maintenance_actions.rebuild_tree, ('media_tree.manage_filenode',))

# TODO: Add clear_cache action
#FileNodeAdmin.register_action(maintenance_actions.clear_cache, ('media_tree.manage_filenode',))

admin.site.register(FileNode, FileNodeAdmin)

