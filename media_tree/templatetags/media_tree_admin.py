from django import template
from django.contrib.admin.templatetags.admin_list import items_for_result
import re

register = template.Library()

TH_REGEX = re.compile('<th(\s+[^>]+)?>(.*)</th>')


def th_for_result(cl, res):
    for item in items_for_result(cl, res, None):
        match = TH_REGEX.match(item)
        if match:
            return match.group(2)


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
        'results': (th_for_result(cl, res) for res in list(cl.result_list)),
    }
