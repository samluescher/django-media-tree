# TODO: Can't move as sibling due to valid_choices being restricted to folders
# TODO: Detect correct column on changelist to insert upload info (e.g. in stream view)
# TODO: Files are not renumbered when name exists within parent.
# TODO: Bring admin actions back
# TODO: Only last upload success message is shown on page reload, they end up being cleared on upload_file_view()

# Medium priority:
#
# TODO: _ref_node_id -- use foreignkey widget that only displays folders (also for move and upload forms)
#   would be easier if MoveNodeForm used a ModelChoiceField
# TODO: ghost can't be dropped properly if it contains a tall image. Needs a treebeard fix because
#   treebeard expects all rows to be the same height
# TODO: how to present top-level folders in collapsed form initially?
# TODO: restore breadcrumbs to show path, and allow a subfolder to be opened via ?parent param
# TODO: move several nodes at the same time
# TODO: copy-drag nodes with alt key


# Low priority:
#
# TODO: Make renaming of files possible.
# TODO: When files are copied, they lose their human-readable name. Should actually create "File Copy 2.txt".
#
# TODO: Ordering of tree by column (within parent) should be possible
# TODO: Refactor FineUploader stuff as extension. This would require signals calls
#       to be called in the FileNodeAdmin view methods.
# TODO: When using raw id interface, after adding new, name and icon are not
#       populated like when list item is selected. Look into dismissAddAnotherPopup().


from ..models import FileNode
from .. import settings as app_settings
from .forms import MoveForm, FileForm, FolderForm, UploadForm
from .utils import get_current_request, set_current_request,  \
    get_special_request_attr, set_special_request_attr, is_search_request
from ..media_backends import get_media_backend
from ..widgets import AdminThumbWidget
from .change_list import MediaTreeChangeList

from treebeard.admin import TreeAdmin

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.options import csrf_protect_m
from django.contrib.admin.views.main import SEARCH_VAR
from django.template.loader import render_to_string
from django.shortcuts import render_to_response
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils.html import escape
from django.utils.encoding import force_text
from django.template.defaultfilters import filesizeformat
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
import json
import os

STATIC_SUBDIR = app_settings.MEDIA_TREE_STATIC_SUBDIR


class FileNodeAdmin(TreeAdmin):

    list_display = app_settings.MEDIA_TREE_LIST_DISPLAY
    list_filter = app_settings.MEDIA_TREE_LIST_FILTER
    search_fields = app_settings.MEDIA_TREE_SEARCH_FIELDS

    formfield_overrides = {
        models.FileField: {'widget': AdminThumbWidget},
        models.ImageField: {'widget': AdminThumbWidget},
    }

    change_list_template = 'admin/media_tree/filenode/tree_change_list.html'

    ADD_FOLDER_VIEW_NAME = 'add_folder'

    class Media:
        js = [
            os.path.join(STATIC_SUBDIR, 'js', 'jquery.init.js').replace("\\","/"),
            os.path.join(STATIC_SUBDIR, 'lib/jquery.fineuploader-4.4.0', 'jquery.fineuploader-4.4.0.js').replace("\\","/"),
            os.path.join(STATIC_SUBDIR, 'js', 'filenode_changelist.js').replace("\\","/"),
            os.path.join(STATIC_SUBDIR, 'js', 'django_admin_fileuploader.js').replace("\\","/"),
        ]
        css = {
            'all': (
                os.path.join(STATIC_SUBDIR, 'css', 'filenode_admin.css').replace("\\","/"),
                os.path.join(STATIC_SUBDIR, 'css', 'filenode_preview.css').replace("\\","/"),
            )
        }

    def get_queryset(self, request):
        if get_special_request_attr(request, 'list_type', None) == 'stream':
            return admin.ModelAdmin.get_queryset(self, request).exclude(node_type=FileNode.FOLDER).order_by('-modified')
        else:
            return super(FileNodeAdmin, self).get_queryset(request)

    def node_preview(self, node, icons_only=False):
        request = get_current_request()
        template = 'admin/media_tree/filenode/includes/preview.html'
        thumbnail_backend = get_media_backend(handles_media_types=(node.media_type,), supports_thumbnails=True)
        if not thumbnail_backend:
            icons_only = True
            template = 'media_tree/filenode/includes/icon.html'
            # TODO SPLIT preview.html in two: one that doesn't need media backend!

        context = {
            'node': node,
            'preview_file': node.get_icon_file() if icons_only else node.get_preview_file(),
            'class': 'collapsed-folder' if node.is_folder() else '',
        }

        if not icons_only:
            thumb = thumbnail_backend.get_thumbnail(context['preview_file'], {'size': self.get_thumbnail_size(request)})
            context['thumb'] = thumb

        preview = render_to_string(template, context).strip()

        if node.is_folder():
            preview = "%s%s" % (preview, render_to_string(template, {
                'node': node,
                'preview_file': node.get_preview_file(default_name='_folder_expanded'),
                'class': 'expanded-folder hidden'
            }).strip())

        meta = '<link class="meta" rel="alternate" data-id="%s" type="%s" href="%s" data-name="%s" data-alt="%s" data-caption="%s">' % (
            node.pk, FileNode.get_mimetype(node.file.path) if node.file else '', escape(node.file.url) if node.file else '',
            escape(node), escape(node.alt), escape(node.get_caption_formatted()))

        return "%s%s" % (preview, meta)
    node_preview.short_description = ''
    node_preview.allow_tags = True

    def node_preview_and_name(self, node):
        return '%s<span class="name">%s</span>' % (self.node_preview(node).strip(), node.name)
    node_preview_and_name.short_description = _('media object')
    node_preview_and_name.allow_tags = True

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

    def metadata_check(self, node):
        return node.has_metadata_including_descendants()
    metadata_check.short_description = _('Metadata')
    metadata_check.allow_tags = True
    metadata_check.boolean = True

    def _get_form_class(self, request, obj):
        if obj:
            node_type = obj.node_type
        else:
            if request.path_info.strip('/').split('/').pop() == self.ADD_FOLDER_VIEW_NAME:
                node_type = FileNode.FOLDER
            else:
                node_type = FileNode.FILE
        if node_type == FileNode.FILE:
            return FileForm
        if node_type == FileNode.FOLDER:
            return FolderForm

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = self._get_form_class(request, obj)
        return super(FileNodeAdmin, self).get_form(request, obj, **kwargs)

    def try_to_move_node(self, as_child, node, pos, request, target):
        # Make sure to validate using the appropriate form. This will validate
        # allowed media types, whether parent is a folder, etc.
        params = {
            '_ref_node_id': target.pk,
            '_position': pos,
            'node_type': node.node_type
        }
        form = MoveForm(params, instance=node)
        if not form.is_valid():
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
            return HttpResponseBadRequest('Malformed POST params')
        return super(FileNodeAdmin, self).try_to_move_node(as_child, node, pos, request, target)

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        return MediaTreeChangeList

    def get_fieldsets(self, request, obj=None):
        fieldsets = getattr(self._get_form_class(request, obj).Meta, 'fieldsets', None)
        if fieldsets:
            return fieldsets
        return super(FileNodeAdmin, self).get_fieldsets(request, obj)

    def get_urls(self):
        try:
            from django.conf.urls.defaults import patterns, url
        except ImportError:
            # Django 1.6
            from django.conf.urls import patterns, url
        urls = super(FileNodeAdmin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        url_patterns = patterns('',
            url(r'^jsi18n/', self.admin_site.admin_view(self.i18n_javascript), name='media_tree_jsi18n'),
            url(r'^upload/$',
                self.admin_site.admin_view(self.upload_file_view),
                name='%s_%s_upload' % info),
            url(r'^%s/$' % self.ADD_FOLDER_VIEW_NAME,
                self.admin_site.admin_view(self.add_folder_view),
                name='%s_%s_add_folder' % info),
            #url(r'^!/(?P<path>.*)/$',
            #    self.admin_site.admin_view(self.open_path_view),
            #    name='%s_%s_open_path' % info),
            #url(r'^!/$',
            #    self.admin_site.admin_view(self.open_path_view),
            #    name='%s_%s_open_root' % info),
            #url(r'^(.+)/expand/$',
            #    self.admin_site.admin_view(self.folder_expand_view),
            #    name='%s_%s_folder_expand' % info),
        )
        url_patterns.extend(urls)
        return url_patterns

    def init_changelist_view_options(self, request):
        context = {}

        list_type = None
        if 'list_type' in request.GET:
            request.GET = request.GET.copy()
            list_type = request.GET.get('list_type')
            del request.GET['list_type']
            if list_type == 'stream':
                request.session['list_type'] = list_type
            else:
                request.session['list_type'] = None
                list_type = None

        search = request.GET.get(SEARCH_VAR, None)
        if search and search != '':
            list_type = 'stream'

        list_type = list_type or request.session.get('list_type', None)
        set_special_request_attr(request, 'list_type', list_type)
        context.update({'list_type': list_type})

        # If depth limiting was not already specified, set it to 1 to only
        # include one level of depth in the change list's queryset, since we
        # want to load additional levels via XHR.
        if list_type != 'stream':
            set_special_request_attr(request, 'max_depth', 1)

        if 'thumbnail_size' in request.GET:
            request.GET = request.GET.copy()
            thumb_size_key = request.GET.get('thumbnail_size')
            del request.GET['thumbnail_size']
            if not thumb_size_key in app_settings.MEDIA_TREE_ADMIN_THUMBNAIL_SIZES:
                thumb_size_key = None
            request.session['thumbnail_size'] = thumb_size_key
        thumb_size_key = request.session.get('thumbnail_size', None) or 'default'
        set_special_request_attr(request, 'thumbnail_size', thumb_size_key)
        backend = get_media_backend()
        if backend and backend.supports_thumbnails():
            context.update({
                'thumbnail_sizes': app_settings.MEDIA_TREE_ADMIN_THUMBNAIL_SIZES,
                'thumbnail_size_key': thumb_size_key,
                'thumbnail_size': self.get_thumbnail_size(request),
            })

        return context

    def get_thumbnail_size(self, request):
        thumb_size_key = get_special_request_attr(request, 'thumbnail_size') or 'default'
        return app_settings.MEDIA_TREE_ADMIN_THUMBNAIL_SIZES[thumb_size_key]

    def get_upload_form(self, request):
        target_folder_id = request.session.get('target_folder_id', None)
        try:
            target_folder = FileNode.objects.get(pk=target_folder_id)
        except FileNode.DoesNotExist:
            request.session['target_folder_id'] = None
        upload_form = UploadForm(initial={'_ref_node_id': request.session.get('target_folder_id', None)})
        del upload_form.fields['file']
        upload_form.fields['_ref_node_id'].label = _('To folder')
        return upload_form

    def changelist_view(self, request, extra_context=None):
        set_current_request(request)

        cl = self.get_changelist(request)
        cl.init_request(request)

        extra_context = extra_context or {}
        extra_context.update(self.init_changelist_view_options(request))
        extra_context.update({
            'upload_form': self.get_upload_form(request),
        })

        return super(FileNodeAdmin, self).changelist_view(request, extra_context)

    @csrf_protect_m
    def add_folder_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['form'] = 'foo'
        return self.add_view(request, form_url, extra_context)

    @csrf_protect_m
    def upload_file_view(self, request, extra_context=None):
        try:
            if not self.has_add_permission(request):
                raise PermissionDenied()

            #self.init_parent_folder(request)

            if request.method == 'POST':
                form = UploadForm(request.POST, request.FILES)
                if form.is_valid():
                    node = form.save(commit=False)
                    self.save_model(request, node, None, False)

                    parent = node.get_parent()
                    if parent:
                        messages.info(request, _('Successfully uploaded file "%s" to "%s".') % (node, parent))
                    else:
                        messages.info(request, _('Successfully uploaded file "%s".') % node)

                    if parent:
                        request.session['target_folder_id'] = parent.pk
                    else:
                        request.session['target_folder_id'] = None

                    # Respond with success
                    if request.is_ajax():
                        return HttpResponse(json.dumps({'success': True}), content_type="application/json")
                    else:
                        return HttpResponseRedirect(reverse('admin:media_tree_filenode_changelist'))
                else:
                    # invalid form data
                    if request.is_ajax():
                        error_messages = ' '.join(
                            [force_text(item) for sublist in form.errors.values() for item in sublist])
                        messages.error(request, error_messages)
                        return HttpResponse(json.dumps({'error': error_messages}),
                            content_type="application/json", status=403)

            # Form is rendered for troubleshooting XHR upload.
            # If this form works, the problem is not server-side.
            if not settings.DEBUG:
                raise ViewDoesNotExist
            if request.method == 'GET':
                form = UploadForm()
            context = dict(self.admin_site.each_context(),
                form=form,
                app_label=self.model._meta.app_label
            )
            context.update(extra_context or {})
            return render_to_response('admin/media_tree/filenode/upload_form.html', context,
                context_instance=RequestContext(request))

        except Exception as e:
            if not settings.DEBUG and request.is_ajax():
                return HttpResponse(json.dumps({'error': ugettext('Server Error')}),
                    content_type="application/json")
            else:
                raise

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

admin.site.register(FileNode, FileNodeAdmin)
