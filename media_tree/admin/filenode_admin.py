# TODO: If in subfolder view, reset_expanded_folders_pk is called and expanded_folders are not stored 
# TODO: Metadata tooltip is too narrow and text gets too wrapped
# TODO: Add icon for change and add folder
# TODO: Ordering of tree by column (within parent) should be possible
# TODO: Refactor SWFUpload stuff as extension. This would require signals calls
#   to be called in the FileNodeAdmin view methods.
# TODO: Make renaming of files possible.
# TODO: When files are copied, they lose their human-readable name. Should actually create "File Copy 2.txt".
# TODO: Bug: With child folder changelist view and child of child expanded -- after uploading a file, the child of child has the expanded triangle, 
#   but no child child child objects are visible.


from media_tree.fields import FileNodeChoiceField
from media_tree.models import FileNode
from media_tree.forms import FolderForm, FileForm, UploadForm
from media_tree.fields import FileNodeChoiceField
from media_tree.widgets import AdminThumbWidget
from media_tree.admin.actions import core_actions
from media_tree.admin.actions import maintenance_actions
from media_tree.admin.actions.utils import execute_empty_queryset_action
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
from django.shortcuts import get_object_or_404, render_to_response
from django.contrib import admin
from django.db import models, transaction
from django.template.loader import render_to_string
from django.contrib.admin.util import unquote
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django.core.urlresolvers import reverse
from django import forms
from django.core.exceptions import ValidationError, ViewDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
from django.contrib.admin.views.main import IS_POPUP_VAR
from django.utils.text import capfirst
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
    mptt_level_indent = app_settings.MEDIA_TREE_MPTT_ADMIN_LEVEL_INDENT

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

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'parent' and issubclass(db_field.rel.to, FileNode):
            # overriding formfield_for_dbfield, thus bypassign both Django's and mptt's
            # formfield_for_foreignkey method, and also preventing Django from wrapping
            # field with RelatedFieldWidgetWrapper ("add" button resulting in a file add form) 
            valid_targets = FileNode.tree.filter(**db_field.rel.limit_choices_to)
            request = kwargs['request']
            node = get_request_attr(request, 'save_node', None)
            if node:
                # Exclude invalid folders, e.g. node cannot be a child of itself
                # (ripped from mptt.forms.MoveNodeForm)
                opts = node._mptt_meta
                valid_targets = valid_targets.exclude(**{
                    opts.tree_id_attr: getattr(node, opts.tree_id_attr),
                    '%s__gte' % opts.left_attr: getattr(node, opts.left_attr),
                    '%s__lte' % opts.right_attr: getattr(node, opts.right_attr),
                })
            field = FileNodeChoiceField(queryset=valid_targets, label=capfirst(db_field.verbose_name), required=not db_field.blank)
            return field

        return super(FileNodeAdmin, self).formfield_for_dbfield(db_field,
             **kwargs)

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

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if not change:
            if not obj.node_type:
                obj.node_type = get_request_attr(request, 'save_node_type', None)
        super(FileNodeAdmin, self).save_model(request, obj, form, change)

    def metadata_check(self, node):
        icon = _boolean_icon(node.has_metadata_including_descendants())
        return '<span class="metadata"><span class="metadata-icon">%s</span><span class="displayed-metadata">%s</span></span>' % (
            icon, node.get_caption_formatted())
    metadata_check.short_description = _('Metadata')
    metadata_check.allow_tags = True

    def expand_collapse(self, node):
        request = get_current_request()
        if not is_search_request(request):
            rel = 'parent:%i' % node.parent_id if node.parent_id else ''
        else:
            rel = ''
        if hasattr(node, 'reduce_levels'):
            qs_params = {'reduce_levels': node.reduce_levels}
        else:
            qs_params = None
        if node.is_folder():
            empty = ' empty' if node.get_children().count() == 0 else ''
            return '<a href="%s" class="folder-toggle%s" rel="%s"><span>%s</span></a>' %  \
                (node.get_admin_url(qs_params), empty, rel, '+')
        else:
            return '<a class="folder-toggle dummy" rel="%s">&nbsp;</a>' % (rel,)
    expand_collapse.short_description = ''
    expand_collapse.allow_tags = True

    def admin_preview(self, node, icons_only=False):
        request = get_current_request()
        template = 'admin/media_tree/filenode/includes/preview.html'
        if not get_media_backend():
            icons_only = True
            template = 'media_tree/filenode/includes/icon.html'
            # TODO SPLIT preview.html in two: one that doesn't need media backend!
        
        thumb_size_name = get_request_attr(request, 'thumbnail_size') or 'default'

        preview = render_to_string(template, {
            'node': node,
            'preview_file': node.get_icon_file() if icons_only else node.get_preview_file(),
            'class': 'collapsed' if node.is_folder() else '',
            'thumbnail_size': app_settings.MEDIA_TREE_ADMIN_THUMBNAIL_SIZES[thumb_size_name]
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
        tools += '<li><a class="change" href="%s">%s</a></li>' % (reverse('admin:media_tree_filenode_change', args=(node.pk,)), ugettext('change'))
        #if node.is_folder():
        #    tools += '<li><a class="add-folder" href="%s?folder_id=%s">%s</a></li>' % (
        #        reverse('admin:media_tree_filenode_add_folder', args=()), str(node.pk), ugettext('add folder'))
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

    def size_formatted(self, node, with_descendants=True):
        if node.node_type == FileNode.FOLDER:
            if with_descendants:
                descendants = node.get_descendants()
                if descendants.count() > 0:
                    size = descendants.aggregate(models.Sum('size'))['size__sum']
                else:
                    size = None
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
        folder_id = request.GET.get('folder_id', None) or request.POST.get('parent', None)
        reduce_levels = request.GET.get('reduce_levels', None) or request.POST.get('reduce_levels', None)
        if folder_id or reduce_levels:
            request.GET = request.GET.copy()
            try:
                del request.GET['folder_id']
            except KeyError:
                pass
            try:
                del request.GET['reduce_levels']
            except KeyError:
                pass

        if folder_id:
            parent_folder = get_object_or_404(FileNode, pk=folder_id, node_type=FileNode.FOLDER)
        else:
            parent_folder = FileNode.get_top_node()

        if reduce_levels:
            try:
                reduce_levels = int(reduce_levels)
            except ValueError:
                reduce_levels = None

        if not reduce_levels and not request.is_ajax() and parent_folder.level >= 0:
            self.reset_expanded_folders_pk(request)
            reduce_levels = parent_folder.level + 1

        set_request_attr(request, 'parent_folder', parent_folder)
        set_request_attr(request, 'reduce_levels', reduce_levels)

    def get_parent_folder(self, request):
        return get_request_attr(request, 'parent_folder', None)

    def get_expanded_folders_pk(self, request):
        if not hasattr(request, 'expanded_folders_pk'):
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

        return getattr(request, 'expanded_folders_pk', None)

    def reset_expanded_folders_pk(self, request):
        setattr(request, 'expanded_folders_pk', [])

    def folder_is_open(self, request, folder):
        return folder.pk in self.get_expanded_folders_pk(request)

    def set_expanded_folders_pk(self, response, expanded_folders_pk):
        response.set_cookie('expanded_folders_pk', '|'.join([str(pk) for pk in expanded_folders_pk]), path='/')

    def init_changelist_view_options(self, request):
        if 'thumbnail_size' in request.GET:
            request.GET = request.GET.copy()
            thumb_size_name = request.GET.get('thumbnail_size')
            del request.GET['thumbnail_size']
            if not thumb_size_name in app_settings.MEDIA_TREE_ADMIN_THUMBNAIL_SIZES:
                 thumb_size_name = None
            request.session['thumbnail_size'] = thumb_size_name
        thumb_size_name = request.session.get('thumbnail_size', 'default')
        set_request_attr(request, 'thumbnail_size', thumb_size_name)
        return {
            'thumbnail_sizes': app_settings.MEDIA_TREE_ADMIN_THUMBNAIL_SIZES.keys(),
            'thumbnail_size': thumb_size_name
        }


    def changelist_view(self, request, extra_context=None):
        response = execute_empty_queryset_action(self, request)
        if response:
            return response

        if not is_search_request(request):
            self.init_parent_folder(request)
        else:
            self.reset_expanded_folders_pk(request)
        parent_folder = self.get_parent_folder(request)
        set_current_request(request)

        if not extra_context:
            extra_context = {}

        extra_context.update(self.init_changelist_view_options(request))

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

        if parent_folder:
            extra_context.update({'node': parent_folder})

        response = super(FileNodeAdmin, self).changelist_view(request, extra_context)
        if isinstance(response, HttpResponse) and parent_folder and not parent_folder.is_top_node():
            expanded_folders_pk = self.get_expanded_folders_pk(request)
            if not parent_folder.pk in expanded_folders_pk:
                expanded_folders_pk.append(parent_folder.pk)
                self.set_expanded_folders_pk(response, expanded_folders_pk)
        return response

    def folder_expand_view(self, request, object_id, extra_context=None):
        node = get_object_or_404(FileNode, pk=unquote(object_id), node_type=FileNode.FOLDER)
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
        set_request_attr(request, 'save_node_type', node_type)
        response = super(FileNodeAdmin, self).add_view(request, form_url, extra_context)
        if isinstance(response, HttpResponseRedirect) and not parent_folder.is_top_node():
            return HttpResponseRedirect(reverse('admin:media_tree_filenode_folder_expand', 
                args=(parent_folder.pk,)))
        return response

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
        try:
            object_id = str(object_id)
            node = get_object_or_404(FileNode, pk=unquote(object_id))
        except ValueError:
            raise Http404
        set_request_attr(request, 'save_node', node)
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

    def open_path_view(self, request, path=''):
        if path is None or path == '':
            return self.changelist_view(request)
        try:
            obj = FileNode.objects.get(path=path)
        except FileNode.DoesNotExist:
            raise Http404
        if obj.is_folder():
            request.GET = request.GET.copy()
            request.GET['folder_id'] = str(obj.pk)
            return self.changelist_view(request)
        else:
            return self.change_view(request, obj.pk)

    def i18n_javascript(self, request):
        """
        Displays the i18n JavaScript that the Django admin requires.

        This takes into account the USE_I18N setting. If it's set to False, the
        generated JavaScript will be leaner and faster.
        """
        if settings.USE_I18N:
            from django.views.i18n import javascript_catalog
        else:
            from django.views.i18n import null_javascript_catalog as javascript_catalog
        return javascript_catalog(request, packages=['media_tree'])

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(FileNodeAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.module_name
        url_patterns = patterns('',
            url(r'^jsi18n/', self.admin_site.admin_view(self.i18n_javascript), name='media_tree_jsi18n'),
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
            url(r'^!/(?P<path>.*)/$',
                self.admin_site.admin_view(self.open_path_view),
                name='%s_%s_open_path' % info),
            url(r'^!/$',
                self.admin_site.admin_view(self.open_path_view),
                name='%s_%s_open_root' % info),
            url(r'^(.+)/expand/$',
                self.admin_site.admin_view(self.folder_expand_view),
                name='%s_%s_folder_expand' % info),
        )
        url_patterns.extend(urls)
        return url_patterns


FileNodeAdmin.register_action(core_actions.copy_selected)
FileNodeAdmin.register_action(core_actions.move_selected)
FileNodeAdmin.register_action(core_actions.change_metadata_for_selected)
FileNodeAdmin.register_action(core_actions.expand_selected)
FileNodeAdmin.register_action(core_actions.collapse_selected)

FileNodeAdmin.register_action(maintenance_actions.delete_orphaned_files, ('media_tree.manage_filenode',))
if settings.DEBUG:
    FileNodeAdmin.register_action(maintenance_actions.rebuild_tree, ('media_tree.manage_filenode',))

FileNodeAdmin.register_action(maintenance_actions.clear_cache, ('media_tree.manage_filenode',))

admin.site.register(FileNode, FileNodeAdmin)
