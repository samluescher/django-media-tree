from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
import re
import os

def import_extender(path):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing extender module %s: "%s"' % (module, e))
    try:
        func = getattr(mod, attr)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" callable extender' % (module, attr))
    return func

def widthratio(value, max_value, max_width):
    """
    Does the same like Django's `widthratio` template tag (scales max_width to factor value/max_value) 
    """
    ratio = float(value) / float(max_value)
    return int(round(ratio * max_width))

def multi_splitext(basename):
    """
    Similar to os.path.slittext(), but with special handling for files with multiple extensions,
    such as "archive.tar.gz": Returns a list containg three elements, the first being the
    name without any extensions (taking into account hidden files/leading periods),
    the second being the "full" extension, the third being the extension as returned by 
    os.path.splitext.
    
    Examples:
        
        os.path.join('foo.bar')        # => ('foo', '.bar')
        multi_splitext('foo.bar')      # => ['foo', '.bar', '.bar']

        os.path.join('foo.tar.gz')     # => ('foo.tar', '.gz')
        multi_splitext('foo.tar.gz')   # => ['foo', '.tar.gz', '.gz']

        os.path.join('.foo.tar.gz')    # => ('.foo.tar', '.gz')
        multi_splitext('.foo.tar.gz')  # => ['.foo', '.tar.gz', '.gz']

        os.path.join('.htaccess')      # => ('.htaccess', '')
        multi_splitext('.htaccess')    # => ['.htaccess', '', '']

        os.path.join('.foo.bar.')      # => ('.foo.bar', '.')
        multi_splitext('.foo.bar.')    # => ['.foo.bar', '.', '.']

    """
    groups = list(re.compile('^(\.*.*?)((\.[^\.]+)*|\.)$').match(basename).groups())
    if not groups[2]:
        groups[2] = groups[1]
    return groups


class FileIcon():
    def __init__(self, base_path, file_node_instance):
        self.base_path = base_path
        self.file_node_instance = file_node_instance

    def __unicode__(self):
        # TODO not working
        return self.file_node_instance.get_media_type_name()

    def alt(self):
        # TODO not working
        return self.file_node_instance.alt()

    def _get_path(self):
        #self._require_file()
        return os.path.join(settings.MEDIA_ROOT, self.base_path)
    path = property(_get_path)

    def _get_url(self):
        #self._require_file()
        return os.path.join(settings.MEDIA_URL, self.base_path)
    url = property(_get_url)

