from django.views.generic.list_detail import object_detail
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from media_tree.urls import image_detail_args

def image_detail(request, object_id):
    kwargs = {'object_id': object_id, 'extra_context': {}}
    kwargs.update(image_detail_args)
    back_page_id = request.GET.get('back_page')
    if back_page_id:
        from cms.models import Page
        page = get_object_or_404(Page, pk=back_page_id)
        kwargs['extra_context'].update({
            'back_link_url': page.get_absolute_url(),
            'back_link_text': _('Back to %s') % page.get_title(),
        })
    return object_detail(request, **kwargs)
