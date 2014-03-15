from media_tree.models import FileNode
from media_tree.contrib.views.listing import FileNodeListingView
from media_tree.contrib.views.detail import FileNodeDetailView
from media_tree.contrib.views.detail.image import ImageNodeDetailView
from django.views.generic.base import TemplateView
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

	(r'^$', TemplateView.as_view(
		template_name="media_tree/base.html"
	)),

    url(r'^listing/$', FileNodeListingView.as_view(
        # notice that queryset can be any iterable, for instance a list:
        queryset=FileNode.objects.filter(level=0),
    ), name="demo_listing"),

    url(r'^files/(?P<path>.+)/$', FileNodeDetailView.as_view(
        queryset=FileNode.objects.filter(extension='txt')
    ), name="demo_detail"),

    url(r'^images/(?P<path>.+)/$', ImageNodeDetailView.as_view(
        queryset=FileNode.objects.get(path='Example Pictures').get_descendants()
    ), name="demo_image"),

    url(r'^admin/', include(admin.site.urls)),
)

# do NOT use this on a production server
from django.conf import settings
from django.conf.urls.static import static
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

