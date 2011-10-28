from media_tree.models import FileNode
from media_tree.contrib.cms_plugins.helpers import PluginLink
from django import forms
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class MediaTreePluginFormBase(forms.ModelForm):

    def clean_link_type(self):
        if 'node' in self.cleaned_data:
            # TODO: Links for folders, for instance link to full-size image for all slideshow items.
            # Could be achieved using FileNode.get_list() processors
            if self.cleaned_data['link_type'] and self.cleaned_data['node'].node_type == FileNode.FOLDER:
                raise forms.ValidationError(_('You can only link individual files, not folders.'))
            if self.cleaned_data['link_type'] == PluginLink.LINK_IMAGE_DETAIL:
                if not PluginLink(self.cleaned_data['link_type'], obj=self.cleaned_data['node']).href():
                    raise forms.ValidationError(_('You need to attach the Media Tree application to a page in order to link to full size images.'))
        return self.cleaned_data['link_type']

    def clean_link_url(self):
        if self.cleaned_data.has_key('link_type') and self.cleaned_data['link_type'] in (PluginLink.LINK_URL, PluginLink.LINK_URL_REVERSE):
            if not self.cleaned_data['link_url']:
                raise forms.ValidationError(self.fields['link_url'].error_messages['required'])
            else:
                if not PluginLink(self.cleaned_data['link_type'], url=self.cleaned_data['link_url']).href():
                    raise forms.ValidationError(self.fields['link_url'].error_messages['invalid'])
        return self.cleaned_data['link_url']

    def clean_link_page(self):
        if self.cleaned_data.has_key('link_type') and self.cleaned_data['link_type'] == PluginLink.LINK_PAGE and not self.cleaned_data['link_page']:
            raise forms.ValidationError(self.fields['link_page'].error_messages['required'])
        return self.cleaned_data['link_page']















