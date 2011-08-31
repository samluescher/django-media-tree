from django import template
from django.contrib.admin.templatetags.admin_list import result_headers, results

register = template.Library()

# from django.contrib.admin.templatetags.admin_list.result_list(cl)
def _result_list(cl):
    return {'cl': cl,
        'result_headers': list(result_headers(cl)),
        'results': list(cl.result_list) #list(results(cl))
    }

def result_list_thumbnails(cl):
    return _result_list(cl)
result_list_thumbnails = register.inclusion_tag("admin/media_tree/filenode/change_list_results_thumbnails.html")(result_list_thumbnails)
