from media_tree.models import FileNode
from media_tree.forms import FolderForm, FileForm, UploadForm
from media_tree.fields import AdminThumbWidget
from media_tree.admin_actions import core_actions
from media_tree.admin_actions.utils import execute_empty_queryset_action
from media_tree.mptt_admin import MPTTModelAdmin
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
import os

try:
    # Django 1.2
    from django.views.decorators.csrf import csrf_view_exempt
except ImportError:
    # pre 1.2
    from django.contrib.csrf.middleware import csrf_view_exempt

MEDIA_SUBDIR = app_settings.get('MEDIA_TREE_MEDIA_SUBDIR')
FILE_ICONS = app_settings.get('MEDIA_TREE_FILE_ICONS')

'''
TODO: For ZIPs in list, click "actions" drop down on the right --> Extract to folder --> Form w/ Extracted files+folder preview, "to folder", "Create subfolder"
TODO: Delete does not work from change form if in subfolder
'''

class IconNode:
    def __init__(self, filename, media_type):
        self.file = os.path.join(MEDIA_SUBDIR, 'img/icons', filename)
        self.alt = app_settings.get('MEDIA_TREE_CONTENT_TYPES')[media_type]

class FileNodeAdmin(MPTTModelAdmin, admin.ModelAdmin):
    list_display = app_settings.get('MEDIA_TREE_LIST_DISPLAY')
    list_filter = app_settings.get('MEDIA_TREE_LIST_FILTER')
    list_display_links = app_settings.get('MEDIA_TREE_LIST_DISPLAY_LINKS')
    search_fields = app_settings.get('MEDIA_TREE_SEARCH_FIELDS')
    ordering = app_settings.get('MEDIA_TREE_ORDERING_DEFAULT')

    formfield_overrides = {
        models.FileField: {'widget': AdminThumbWidget},
        models.ImageField: {'widget': AdminThumbWidget},
    }

    actions = []

    class Media:
        js = [
            os.path.join(MEDIA_SUBDIR, 'lib/swfupload/swfupload_fp10', 'swfupload.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/swfupload/plugins', 'swfupload.queue.js'),
            os.path.join(MEDIA_SUBDIR, 'lib/swfupload/plugins', 'swfupload.cookies.js'),
            os.path.join(MEDIA_SUBDIR, 'js', 'admin_enhancements.js'),
            os.path.join(MEDIA_SUBDIR, 'js', 'jquery.swfupload_manager.js'),
        ]
        css = {
            'all': (
                os.path.join(MEDIA_SUBDIR, 'css', 'swfupload.css'),
            )
        }

    @staticmethod
    def register_action(func):
        FileNodeAdmin.actions.append(func)

    def _media(self):
        import logging
        logging.debug('MEDIA')
        return super(FileNodeAdmin, self)._media()

    def get_form(self, request, *args, **kwargs):
        if request.GET.get('save_node_type', FileNode.FILE) == FileNode.FOLDER:
            self.form = FolderForm
        else:
            self.form = FileForm
        self.fieldsets = self.form.Meta.fieldsets

        form = super(FileNodeAdmin, self).get_form(request, *args, **kwargs)
        form.parent_folder = self.get_parent_folder(request)
        return form

    # TODO move to model, with thumbnail() method
    def admin_thumbnail(self, node):
        #url = node.pk
        url = None
        if node.media_type == media_types.SUPPORTED_IMAGE or node.preview_file:
            thumbNode = node
            return render_to_string('admin/media_tree/filenode/thumbnail.html', { 'node': thumbNode, 'url': url, 'MEDIA_URL': settings.MEDIA_URL })
        else:
            if FILE_ICONS.has_key(node.extension):
                icon_file = FILE_ICONS[node.extension]
            else:
                icon_file = FILE_ICONS[node.media_type]
            thumbNode = IconNode(icon_file, node.media_type)
            return render_to_string('admin/media_tree/filenode/icon.html', { 'node': thumbNode, 'url': url, 'MEDIA_URL': settings.MEDIA_URL })
    admin_thumbnail.short_description = ' ' # TODO Space due to Django bug http://code.djangoproject.com/ticket/12434
    admin_thumbnail.allow_tags = True

    def size_formatted(self, node):
        if node.node_type == FileNode.FOLDER:
            return ''
        else:
            return format_filesize(node.size)
    size_formatted.short_description = _('size')
    size_formatted.admin_order_field = 'size'

    def queryset(self, request):
        qs = super(FileNodeAdmin, self).queryset(request)
        if getattr(request, 'filter_by_parent_folder', False):
            return qs.filter(parent=self.get_parent_folder(request))
        else:
            return qs

    def save_model(self, request, obj, form, change):
        obj.attach_user(request.user, change)
        if not change:
            obj.node_type = request.GET.get('save_node_type', FileNode.FILE)
            parent_folder = self.get_parent_folder(request)
            if parent_folder:
                obj.insert_at(parent_folder, commit=True)
                return
        obj.save()
        # Make sure there is only one default node per folder, per media_type
        # TODO move to model?
        if obj.node_type == FileNode.FILE and obj.is_default:
            other_default_nodes = obj.get_siblings().filter(is_default=True, media_type=obj.media_type)
            for node in other_default_nodes:
                node.is_default = False
                node.save()

    def set_parent_folder(self, request, folder_or_id):
        if folder_or_id != None:
            if isinstance(folder_or_id, FileNode):
                folder = folder_or_id
            else:
                folder = FileNode.objects.get(pk=unquote(folder_or_id), node_type=FileNode.FOLDER)
        else:
            folder = None
        request.parent_folder = folder

    def get_parent_folder(self, request):
        return getattr(request, 'parent_folder', None)

    def add_parent_folder_context(self, request, extra_context):
        if extra_context == None:
            extra_context = {}
        parent_folder = self.get_parent_folder(request)
        extra_context.update({ 'node': parent_folder if parent_folder else FileNode.get_root_node() });
        return extra_context

    def change_view(self, request, object_id, extra_context=None):
        node = FileNode.objects.get(pk=unquote(object_id))
        self.set_parent_folder(request, node.parent)
        request.GET = request.GET.copy()
        request.GET.update({'save_node_type': node.node_type})
        return super(FileNodeAdmin, self).change_view(request, object_id, extra_context={'node': node})

    def add_file_view(self, request, form_url='', extra_context=None, folder_id=None):
        self.set_parent_folder(request, folder_id)
        return super(FileNodeAdmin, self).add_view(request, form_url, self.add_parent_folder_context(request, extra_context))

    # Upload view is exempted from CSRF protection since SWFUpload can not send cookies (i.e. it can only
    # send cookie values as post values, but that would make this check useless anyway).
    # However, Flash Player should already enforce a same-domain policy.
    @csrf_view_exempt
    def upload_file_view(self, request, folder_id=None):
        if not self.has_add_permission(request):
            raise PermissionDenied
        self.set_parent_folder(request, folder_id)
        if request.method == 'POST':
            form = UploadForm(request.POST, request.FILES)
            if form.is_valid():
                node = FileNode(file=form.cleaned_data['file'])
                self.save_model(request, node, None, False)
                # Respond with 'ok' for the client to verify that the upload was successful, since sometimes a failed
                # request would not result in a HTTP error and look like a successful upload.
                # For instance: When requesting the admin view without authentication, there is a redirect to the
                # login form, which to SWFUpload looks like a successful upload request.
                return HttpResponse("ok", mimetype="text/plain")
            else:
                if not settings.DEBUG:
                    raise ValidationError
                    return
        if not settings.DEBUG:
            raise ViewDoesNotExist
        else:
            # Form is rendered for troubleshooting SWFUpload. If this form works, the problem is not server-side.
            from django.template import Template, RequestContext
            t = Template('<form method="POST" enctype="multipart/form-data">'
                +'<h1>upload_file_view test form</h1><p>{{ form.file.errors }}{{ form.file }}</p>'
                +'<p><input type="submit" value="OK" /></p></form>')
            if request.method != 'POST':
                form = UploadForm()
            return HttpResponse(t.render(RequestContext(request, {'form': form})))

    def add_folder_view(self, request, form_url='', extra_context=None, folder_id=None):
        self.set_parent_folder(request, folder_id)
        request.GET = request.GET.copy()
        request.GET.update({'save_node_type': FileNode.FOLDER})
        return super(FileNodeAdmin, self).add_view(request, form_url, self.add_parent_folder_context(request, extra_context))

    def changelist_view(self, request, extra_context=None):
        response = execute_empty_queryset_action(self, request)
        if response: 
            return response
        
        extra_context = self.add_parent_folder_context(request, extra_context)
        if request.GET.get('q', None): # or request.GET.get('has_metadata__exact', None):
            search = FileNode.get_root_node()
            search.name = _('Search results')
            extra_context = {'node': search}
        else:
            setattr(request, 'filter_by_parent_folder', True)
            
        if app_settings.get('MEDIA_TREE_SWFUPLOAD'):
            middleware = 'media_tree.middleware.SessionPostMiddleware'
            if not middleware in settings.MIDDLEWARE_CLASSES:
                request.user.message_set.create(message=_('You need to put %s in your MIDDLEWARE_CLASSES setting to use SWFUpload.') % middleware)
            else:
                parent_folder = self.get_parent_folder(request)
                if parent_folder:
                    swfupload_upload_url = reverse('admin:media_tree_upload', kwargs={'folder_id': parent_folder.pk})
                else:
                    swfupload_upload_url = reverse('admin:media_tree_upload_root')
                #swfupload_flash_url = os.path.join(settings.MEDIA_URL, MEDIA_SUBDIR, 'lib/swfupload/swfupload_fp10/swfupload.swf')
                swfupload_flash_url = reverse('admin:media_tree_static_swfupload_swf')
                extra_context.update({
                    'file_types': app_settings.get('MEDIA_TREE_ALLOWED_FILE_TYPES'),
                    'file_size_limit': app_settings.get('MEDIA_TREE_FILE_SIZE_LIMIT'),
                    'swfupload_flash_url': swfupload_flash_url,
                    'swfupload_upload_url': swfupload_upload_url,
                })
        return super(FileNodeAdmin, self).changelist_view(request, extra_context)

    def node_view(self, request, object_id=None, object_path=''):
        if object_id:
            node = FileNode.objects.get(pk=unquote(object_id))
        else:
            node = FileNode.get_root_node()
        # If an incomplete or false path to the node was requested (which happens,
        # for instance, when clicking on search results: redirect to correct URL)
        node_url = node.get_admin_url()
        if request.path != node_url:
            return HttpResponseRedirect(node_url)
        # Otherwise show changelist for folder nodes or file form for file nodes
        if node.node_type == FileNode.FOLDER:
            self.set_parent_folder(request, node)
            return self.changelist_view(request)
        else:
            self.set_parent_folder(request, node.parent)
            return self.change_view(request, object_id)

    def get_urls(self):
        from django.conf.urls.defaults import patterns, url
        urls = super(FileNodeAdmin, self).get_urls()
        url_patterns = patterns('',
            # Since Flash Player enforces a same-domain policy, the upload will break if static files 
            # are served from another domain. So the built-in static file view is used for the uploader SWF:
            url(r'^static/swfupload\.swf$', "django.views.static.serve", 
                {'document_root': os.path.join(settings.MEDIA_ROOT, MEDIA_SUBDIR), 
                'path': 'lib/swfupload/swfupload_fp10/swfupload.swf'}, name='media_tree_static_swfupload_swf'),

            url(r'^jsi18n/', self.admin_site.admin_view(self.i18n_javascript), name='media_tree_jsi18n'),

            url(r'^((\d+/)*(?P<folder_id>\d+)/)?add/$', self.admin_site.admin_view(self.add_file_view)),
            url(r'^(\d+/)*(?P<folder_id>\d+)/upload/$', self.admin_site.admin_view(self.upload_file_view), name='media_tree_upload'),
            url(r'^upload/$', self.admin_site.admin_view(self.upload_file_view), name='media_tree_upload_root'),
            url(r'^((\d+/)*(?P<folder_id>\d+)/)?add_folder/$', self.admin_site.admin_view(self.add_folder_view)),
            url(r'^((\d+/)*(?P<object_id>\d+)/)change/$', self.admin_site.admin_view(self.change_view)),
            url(r'^((\d+/)*(?P<object_id>\d+)/)delete/$', self.admin_site.admin_view(self.delete_view)),
            url(r'^((\d+/)*(?P<object_id>\d+)/)history/$', self.admin_site.admin_view(self.history_view)),
            url(r'^((?P<object_path>(\d+/)*)(?P<object_id>\d+)/)$', self.admin_site.admin_view(self.node_view), name="media_tree_node"),
        )
        url_patterns.extend(urls)
        return url_patterns

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


FileNodeAdmin.register_action(core_actions.copy_selected)
FileNodeAdmin.register_action(core_actions.move_selected)
FileNodeAdmin.register_action(core_actions.change_metadata_for_selected)

ADMIN_ACTIONS = app_settings.get('MEDIA_TREE_ADMIN_ACTIONS')
if ADMIN_ACTIONS:
    from media_tree.utils import import_extender
    for path in ADMIN_ACTIONS:
        FileNodeAdmin.register_action(import_extender(path))

admin.site.register(FileNode, FileNodeAdmin)
