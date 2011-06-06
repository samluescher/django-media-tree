# TODO: Add rest of admin_old's functionality (actions etc)
# TODO: Move external stuff to media_tree.contrib (all image-related stuff, for instance!)
# TODO: Can I use thread locals directly in here, without middleware?
# TODO: Remove child folders from expanded_folders_pk if target folder is not in there -- actually, a call close_folder?folder_id=... might be better 

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()

def get_current_request():
    """ returns the request object for this thead """
    return getattr(_thread_locals, "request", None)
    
    
"""
TODO: Search is currently restricted to root-level items 
"""

from django.utils.encoding import force_unicode
from django.contrib import messages
from django.shortcuts import render_to_response
from media_tree.models import FileNode
from media_tree.forms import FolderForm, FileForm, UploadForm
from media_tree.widgets import AdminThumbWidget
from media_tree.admin_actions import core_actions
from media_tree.admin_actions import maintenance_actions
from media_tree.admin_actions.utils import execute_empty_queryset_action
from mptt.admin import MPTTModelAdmin
from media_tree import defaults
from media_tree import app_settings, media_types
from media_tree.templatetags.filesize import filesize as format_filesize
from mptt.forms import TreeNodeChoiceField
from django.contrib import admin
from django.db import models
from django.template.loader import render_to_string
from django.contrib.admin.util import unquote
from django.core.exceptions import PermissionDenied
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.conf import settings
from django.core.urlresolvers import reverse
from django import forms
from django.core.exceptions import ValidationError, ViewDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.http import Http404
import os

try:
    # Django 1.2
    from django.views.decorators.csrf import csrf_view_exempt
except ImportError:
    # pre 1.2
    from django.contrib.csrf.middleware import csrf_view_exempt

MEDIA_SUBDIR = app_settings.get('MEDIA_TREE_MEDIA_SUBDIR')


class FileNodeAdmin(MPTTModelAdmin):
    
    change_list_template = 'admin/media_tree/filenode/mptt_change_list.html'
    
    list_display = app_settings.get('MEDIA_TREE_LIST_DISPLAY')
    list_filter = app_settings.get('MEDIA_TREE_LIST_FILTER')
    #list_display_links = app_settings.get('MEDIA_TREE_LIST_DISPLAY_LINKS')
    search_fields = app_settings.get('MEDIA_TREE_SEARCH_FIELDS')
    ordering = app_settings.get('MEDIA_TREE_ORDERING_DEFAULT')
    mptt_indent_field = 'browse_controls'

    formfield_overrides = {
        models.FileField: {'widget': AdminThumbWidget},
        models.ImageField: {'widget': AdminThumbWidget},
    }

    actions = []

    filter_by_parent_folder = None

    class Media:
        js = [
            os.path.join(MEDIA_SUBDIR, 'lib/swfupload/swfupload_fp10', 'swfupload.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/swfupload/plugins', 'swfupload.queue.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/swfupload/plugins', 'swfupload.cookies.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/jquery', 'jquery.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/jquery', 'jquery.ui.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/jquery', 'jquery.cookie.js'),
            os.path.join(MEDIA_SUBDIR, 'js', 'admin_enhancements.js'),
            os.path.join(MEDIA_SUBDIR, 'js', 'jquery.swfupload_manager.js'),
        ]
        css = {
            'all': (
                os.path.join(MEDIA_SUBDIR, 'css', 'swfupload.css'),
                os.path.join(MEDIA_SUBDIR, 'css', 'ui.css'),
            )
        }

    def __init__(self, *args, **kwargs):
        super(FileNodeAdmin, self).__init__(*args, **kwargs)
        # http://stackoverflow.com/questions/1618728/disable-link-to-edit-object-in-djangos-admin-display-list-only
        self.list_display_links = (None, )

    @staticmethod
    def register_action(func):
        FileNodeAdmin.actions.append(func)

    def queryset(self, request):
        qs = super(FileNodeAdmin, self).queryset(request)
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

    def expand_collapse(self, node):
        rel = 'parent:%i' % node.parent_id if node.parent_id else ''
        if node.is_folder():
            if node.get_descendant_count() > 0:
                state = 'expanded' if self.folder_is_open(get_current_request(), node) else 'collapsed'
                return '<a href="?folder_id=%i" class="folder-toggle %s" rel="%s"><span>%s</span></a>' %  \
                    (node.pk, state, rel, '+')
            else:
                return '<a class="folder-toggle dummy empty" rel="%s">&nbsp;</a>' % (rel,)
        else:
            return '<a class="folder-toggle dummy" rel="%s">&nbsp;</a>' % (rel,)
    expand_collapse.short_description = ''
    expand_collapse.allow_tags = True
            
    def admin_preview(self, node):
        return render_to_string('admin/media_tree/filenode/includes/preview.html', {'node': node})
    admin_preview.short_description = ''
    admin_preview.allow_tags = True

    def admin_preview_link(self, node):
        if node.is_folder():
            return '<a href="%s" class="folder"><span>%s</span></a>' % (node.get_admin_url(), _('folder'))
        else:
            return '<a href="%s">%s</a>' % (node.get_admin_url(), self.admin_preview(node))

    def admin_link(self, node):
        return '<a class="name" href="%s">%s</a>' % (node.get_admin_url(), node.name)

    def browse_controls(self, node):
        return '<span class="browse-controls">%s&nbsp;%s&nbsp;%s</span>' %  \
            (self.expand_collapse(node), self.admin_preview_link(node), self.admin_link(node))
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
            return '<span class="filesize">%s</span>' % format_filesize(size)
    size_formatted.short_description = _('size')
    size_formatted.admin_order_field = 'size'
    size_formatted.allow_tags = True

    def init_parent_folder(self, request):
        folder_id = request.GET.get('folder_id', None) or request.POST.get('folder_id', None)
        if folder_id:
            try:
                request.GET = request.GET.copy()
                del request.GET['folder_id']
            except KeyError:
                pass
            try:
                parent_folder = FileNode.objects.get(pk=folder_id, node_type=FileNode.FOLDER)
            except FileNode.DoesNotExist:
                raise Http404
        else:
            parent_folder = FileNode.get_top_node()
        setattr(request, 'media_tree_parent_folder', parent_folder)

    def get_parent_folder(self, request):
        return getattr(request, 'media_tree_parent_folder', None)
    
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
            setattr(request, 'expanded_folders_pk', expanded_folders_pk)
        return expanded_folders_pk

    def folder_is_open(self, request, folder):
        return folder.pk in self.get_expanded_folders_pk(request)
        
    def set_expanded_folders_pk(self, response, expanded_folders_pk):
        response.set_cookie('expanded_folders_pk', '|'.join([str(pk) for pk in expanded_folders_pk]), path='/')
    
    def changelist_view(self, request, extra_context=None):
        self.init_parent_folder(request)
        parent_folder = self.get_parent_folder(request)
        _thread_locals.request = request
        
        if app_settings.get('MEDIA_TREE_SWFUPLOAD'):
            middleware = 'media_tree.middleware.SessionPostMiddleware'
            if not middleware in settings.MIDDLEWARE_CLASSES:
                request.user.message_set.create(message=_('You need to put %s in your MIDDLEWARE_CLASSES setting to use SWFUpload.') % middleware)
            else:
                swfupload_upload_url = reverse('admin:media_tree_upload')
                #swfupload_flash_url = os.path.join(settings.MEDIA_URL, MEDIA_SUBDIR, 'lib/swfupload/swfupload_fp10/swfupload.swf')
                swfupload_flash_url = reverse('admin:media_tree_static_swfupload_swf')
                if not extra_context:
                    extra_context = {}
                extra_context.update({
                    'file_types': app_settings.get('MEDIA_TREE_ALLOWED_FILE_TYPES'),
                    'file_size_limit': app_settings.get('MEDIA_TREE_FILE_SIZE_LIMIT'),
                    'swfupload_flash_url': swfupload_flash_url,
                    'swfupload_upload_url': swfupload_upload_url,
                })
        
        response = super(FileNodeAdmin, self).changelist_view(request, extra_context)
        if isinstance(response, HttpResponse) and not parent_folder.is_top_node():
            expanded_folders_pk = self.get_expanded_folders_pk(request)
            if not parent_folder.pk in expanded_folders_pk:  
                expanded_folders_pk.append(parent_folder.pk)
                self.set_expanded_folders_pk(response, expanded_folders_pk)
        return response

    def change_view(self, request, object_id, extra_context=None):
        node = FileNode.objects.get(pk=unquote(object_id))
        return super(FileNodeAdmin, self).change_view(request, object_id, extra_context={'node': node})

    def get_form(self, request, *args, **kwargs):
        if request.GET.get('save_node_type', FileNode.FILE) == FileNode.FOLDER:
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
                    node.insert_at(parent_folder, save=False)
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
            return render_to_response('admin/media_tree/filenode/upload_form.html', {'form': form, 'node': self.get_parent_folder(request)}, context_instance=RequestContext(request))

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(FileNodeAdmin, self).get_urls()
        url_patterns = patterns('',
            # Since Flash Player enforces a same-domain policy, the upload will break if static files 
            # are served from another domain. So the built-in static file view is used for the uploader SWF:
            url(r'^static/swfupload\.swf$', "django.views.static.serve", 
                {'document_root': os.path.join(settings.MEDIA_ROOT, MEDIA_SUBDIR), 
                'path': 'lib/swfupload/swfupload_fp10/swfupload.swf'}, name='media_tree_static_swfupload_swf'),
            url(r'^upload/$', self.admin_site.admin_view(self.upload_file_view), name='media_tree_upload'),
        )
        url_patterns.extend(urls)
        return url_patterns

admin.site.register(FileNode, FileNodeAdmin)

