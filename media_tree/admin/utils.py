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

# TODO: Document... since some methods don't have the arguments... thread-safety etc
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