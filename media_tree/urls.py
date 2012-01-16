from django.conf.urls.defaults import *
from media_tree.models import FileNode
from media_tree import media_types
import datetime

image_args = {
    'queryset': FileNode.objects.filter(published__exact=True, media_type__exact=media_types.SUPPORTED_IMAGE),
}

js_info_dict = {
    'packages': ('media_tree',),
}

image_detail_args = dict(image_args, template_name='media_tree/filenode/image.html')

urlpatterns = patterns('',
	url(r'^image/(?P<object_id>\d+)/$', 'media_tree.views.image_detail', name='media_tree_image_detail'),
)

