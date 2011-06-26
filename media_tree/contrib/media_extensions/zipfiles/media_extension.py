from media_tree.contrib.media_extensions.zipfiles import zip_operations as operations
from media_tree import extension
from cStringIO import StringIO
from django.http import HttpResponse
from django.utils.translation import ugettext, ugettext_lazy as _

# TODO: Implement extract_selected_archives
class ZipFileAdminExtender(extension.AdminExtender):
    
    def download_selected_as_archive(modeladmin, request, queryset):
        if queryset.count() == 1:
            file_name = queryset[0].name
        else:
            file_name = ugettext('Archive')
        file_ext = 'zip'
        
        response = HttpResponse(mimetype='application/zip')
        response['Content-Disposition'] = 'attachment; filename=%s.%s' % (
            file_name, file_ext)
        buffer = StringIO()
        operations.compress_nodes(buffer, queryset)
        buffer.flush()
        response.write(buffer.getvalue())
        response['Content-Length'] = len(response.content);
        buffer.close()
        return response
    download_selected_as_archive.short_description = _('Download selected %(verbose_name_plural)s as archive')
    
    actions = [download_selected_as_archive]

extension.register(ZipFileAdminExtender)
