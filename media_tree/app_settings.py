from django.conf import settings
from media_tree import defaults

def get(key):
    if hasattr(settings, key):
        return getattr(settings, key)
    else:
        return getattr(defaults, key)

def merge(key):
    dict = getattr(defaults, key)
    if hasattr(settings, key):
        dict.update(getattr(settings, key))
    return dict
