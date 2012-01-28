from media_tree.contrib.cms_plugins.media_tree_image.views import ImagePluginDetailView
from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/$', ImagePluginDetailView.as_view(),
    	name='media_tree.contrib.cms_plugins.media_tree_image.ImagePluginDetailView'),
)
