from media_tree.models import FileNode
from media_tree import settings as app_settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import filesizeformat

import os

class FolderForm(forms.ModelForm):
    parent_folder = None

    class Meta:
        model = FileNode
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
        ]

    def clean_name(self):
        qs = FileNode.objects.filter(parent=self.parent_folder)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.filter(name__exact=self.cleaned_data['name']).count() > 0:
            raise forms.ValidationError(_('A %s with this name already exists.') % FileNode._meta.verbose_name)
        return self.cleaned_data['name']

class FileForm(forms.ModelForm):

    # TODO:
    #set_manual_dimensions = forms.BooleanField(_('set manual dimensions'), required=False)
    
    class Meta:
        model = FileNode
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

class UploadForm(forms.Form):
    file = forms.FileField()
    def clean_file(self):
        return FileForm.upload_clean(self.cleaned_data['file'])

class MetadataForm(forms.ModelForm):
    class Meta:
        model = FileNode
        exclude = ('file', 'name', 'is_default', 'preview_file')
