from django import template
from django.contrib.admin.templatetags.admin_list import result_headers, results

register = template.Library()

@register.inclusion_tag(
    'admin/media_tree/filenode/flat_change_list_results.html', takes_context=True)
def result_tree_flat(context, cl, request):
    """
    Added 'filtered' param, so the template's js knows whether the results have
    been affected by a GET param or not. Only when the results are not filtered
    you can drag and sort the tree
    """

    return {
        #'filtered': is_filtered_cl(cl, request),
        'results': list(cl.result_list),
    }
