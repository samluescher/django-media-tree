from media_tree.models import FileNode
from media_tree import settings as app_settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat

import os

class FileNodeForm(forms.ModelForm):

    class Meta:
        model = FileNode

    def clean(self):
        if self.cleaned_data['parent']:
            allowed_types = self.cleaned_data['parent'].allowed_child_node_types
        else:
            allowed_types = app_settings.MEDIA_TREE_ROOT_ALLOWED_NODE_TYPES

        if allowed_types and len(allowed_types) and not self.cleaned_data['node_type'] in allowed_types:
            raise forms.ValidationError(_('Can\'t save media object in this folder. Please select an appropriate parent folder.'))

        return self.cleaned_data


class FolderForm(FileNodeForm):

    class Meta(FileNodeForm.Meta):
        fieldsets = [
            (_('Folder'), {
                'fields': ['parent', 'name',]
            }),
            (_('Metadata'), {
                'fields': ['title', 'description']
            }),
            (_('Extended metadata'), {
                'fields': ['author', 'copyright', 'date_time'],
                'classes': ['collapse']
            }),
            (_('Permissions'), {
                'fields': ['allowed_child_node_types'],
                'classes': ['collapse']
            }),
        ]

    def clean(self):
        self.cleaned_data['node_type'] = FileNode.FOLDER
        return super(FolderForm, self).clean()

    def clean_name(self):
        qs = FileNode.objects.filter(parent=self.cleaned_data['parent'])
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.filter(name__exact=self.cleaned_data['name']).count() > 0:
            raise forms.ValidationError(_('A %s with this name already exists.') % FileNode._meta.verbose_name)
        return self.cleaned_data['name']


class FileForm(FileNodeForm):

    # TODO:
    #set_manual_dimensions = forms.BooleanField(_('set manual dimensions'), required=False)
    
    class Meta(FileNodeForm.Meta):
        fieldsets = [
            (_('File'), {
                #'fields': ['name', 'file']
                'fields': ['parent', 'file']
            }),
            (_('Display'), {
                'fields': ['published', 'preview_file', 'position', 'is_default'],
                'classes': ['collapse']
            }),
            (_('Metadata'), {
                'fields': ['title', 'description']
            }),
            (_('Extended metadata'), {
                'fields': ['author', 'publish_author', 'copyright', 'publish_copyright', 'date_time', 'publish_date_time', 'keywords', 'override_caption', 'override_alt', 'width', 'height'],
                'classes': ['collapse']
            }),
        ]

    def __init__(self, *args, **kwargs):
        super(FileForm, self).__init__(*args, **kwargs)
        if 'name' in self.fields:
            del self.fields['name']

    def clean(self):
        self.cleaned_data['node_type'] = FileNode.FILE
        return super(FileForm, self).clean()

    @staticmethod
    def upload_clean(uploaded_file):
        if not os.path.splitext(uploaded_file.name)[1].lstrip('.').lower() in app_settings.MEDIA_TREE_ALLOWED_FILE_TYPES:
            raise forms.ValidationError(_('This file type is not allowed.'))
        max_size = app_settings.MEDIA_TREE_FILE_SIZE_LIMIT;
        if max_size and uploaded_file.size > max_size:
            raise forms.ValidationError(_('Maximum file size is %s.') % filesizeformat(max_size))
        return uploaded_file

    def clean_file(self):
        return FileForm.upload_clean(self.cleaned_data['file'])


class UploadForm(FileForm):
    fieldsets = None

    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        for key in self.fields.keys():
            if not key in ('file', 'parent'):
                del self.fields[key]


class MetadataForm(forms.ModelForm):
    class Meta:
        model = FileNode
        exclude = ('file', 'name', 'is_default', 'preview_file')
