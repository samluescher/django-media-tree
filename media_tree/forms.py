from media_tree.models import FileNode
from media_tree import app_settings
from django import forms
from django.utils.translation import ugettext as _
from media_tree.templatetags.filesize import filesize as format_filesize
import os

class FolderForm(forms.ModelForm):
    parent_folder = None

    class Meta:
        model = FileNode
        fieldsets = [
            (_('Folder'), {
                'fields': ['name',]
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

    class Meta:
        model = FileNode
        fieldsets = [
            (_('File'), {
                'fields': ['file', 'is_default']
            }),
            (_('Metadata'), {
                'fields': ['title', 'description']
            }),
            (_('Extended metadata'), {
                'fields': ['author', 'publish_author', 'copyright', 'publish_copyright', 'date_time', 'publish_date_time', 'keywords', 'override_caption', 'override_alt'],
                'classes': ['collapse']
            }),
        ]

    @staticmethod
    def upload_clean(uploaded_file):
        if not os.path.splitext(uploaded_file.name)[1].lstrip('.').lower() in app_settings.get('MEDIA_TREE_ALLOWED_FILE_TYPES'):
            raise forms.ValidationError(_('This file type is not allowed.'))
        max_size = app_settings.get('MEDIA_TREE_FILE_SIZE_LIMIT');
        if max_size and uploaded_file.size > max_size:
            raise forms.ValidationError(_('Maximum file size is %s.') % format_filesize(max_size))
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
        exclude = ('file', 'name', 'is_default')
