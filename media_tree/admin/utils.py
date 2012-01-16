from django.contrib.admin.views.main import SEARCH_VAR

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()

def set_current_request(request):
    _thread_locals.request = request
    
def get_current_request():
    """ returns the request object for this thread """
    return getattr(_thread_locals, "request", None)

# Sometimes we need to pass around parameters between standard ModelAdmin methods,
# and since the methods don't have these parameters, we are passing them through a
# dictionary in the request object. This is hackish, but there currently is no
# better solution. 
def set_request_attr(request, attr, value):
    if not hasattr(request, 'media_tree'):
        request.media_tree = {}
    request.media_tree[attr] = value

def get_request_attr(request, attr, default=None):
    if not hasattr(request, 'media_tree'):
        return default
    return request.media_tree.get(attr, default)

def is_search_request(request):
    return request.GET.get(SEARCH_VAR, None) != None