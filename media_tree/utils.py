from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.core.files.storage import FileSystemStorage
from django.core.files.base import File
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


def autodiscover_media_extensions():
    """
    Auto-discover INSTALLED_APPS media_extensions.py modules and fail silently when
    not present. This forces an import on them to register any media extension bits
    they may want.
    
    Rip of django.contrib.admin.autodiscover()
    """
    import copy
    from django.conf import settings
    from django.utils.importlib import import_module
    from django.utils.module_loading import module_has_submodule

    for app in settings.INSTALLED_APPS:
        mod = import_module(app)
        # Attempt to import the app's admin module.
        try:
            #before_import_registry = copy.copy(site._registry)
            import_module('%s.media_extension' % app)
        except:
            # Reset the model registry to the state before the last import as
            # this import will have to reoccur on the next request and this
            # could raise NotRegistered and AlreadyRegistered exceptions
            # (see #8245).
            
            # TODO: what!?
            #site._registry = before_import_registry

            # Decide whether to bubble up this error. If the app just
            # doesn't have an admin module, we can ignore the error
            # attempting to import it, otherwise we want it to bubble up.
            if module_has_submodule(mod, 'media_extension'):
                raise


# TODO: Factor out to image extension
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


class IconFile(FieldFile):
    
    class PseudoField(object):
        def __init__(storage):
            self.storage = storage

    def __init__(self, instance, name):
        File.__init__(self, None, name)
        self.instance = instance
        self.storage = FileSystemStorage()
        self.field = self
        self.is_icon = True

    def save(self, *args, **kwargs):
        raise NotImplementedError('Icon files are read-only')

    def delete(self, *args, **kwargs):
        raise NotImplementedError('Icon files are read-only')

    def __unicode__(self):
        return self.instance.__unicode__()
        #return self.instance.get_media_type_name()

    def alt(self):
        return self.instance.alt()
