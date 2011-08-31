from django.conf import settings
from django.utils.importlib import import_module
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import get_storage_class
from django.utils.html import conditional_escape
import re


def get_media_storage():
    klass = get_storage_class()
    return klass()
    
# TODO: This function should probably cache all imported modules
def get_module_attr(path):
    i = path.rfind('.')
    module_name, attr_name = path[:i], path[i+1:]
    try:
        module = import_module(module_name)
    except ImportError, e:
        raise ImproperlyConfigured('Error importing module %s: "%s"' % (module_name, e))
    try:
        attr = getattr(module, attr_name)
    except AttributeError:
        raise ImproperlyConfigured('Module "%s" does not define a "%s" callable' % (module_name, attr_name))
    return attr


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


def join_formatted(text, new_text, glue_format_if_true = u'%s%s', glue_format_if_false = u'%s%s', condition=None, format = u'%s'):
    """
    Joins two strings, escaping the second, and using one of two string
    formats for glueing them together, depending on whether a condition is True 
    or False.
    
    This function is a shorthand for complicated code blocks when you
    want to format some strings and link them together. A typical use
    case might be: Wrap string B with <strong> tags, but only if it is
    not empty, and join it with A with a comma in between, but only if
    A is not empty, etc. 
    """
    if condition is None:
        condition = text and new_text
    add_text = conditional_escape(new_text)
    if add_text:
        add_text = format % add_text
    glue_format = glue_format_if_true if condition else glue_format_if_false
    return glue_format % (text, add_text)


# TODO: Factor out to image extension
def widthratio(value, max_value, max_width):
    """
    Does the same like Django's `widthratio` template tag (scales max_width to factor value/max_value) 
    """
    ratio = float(value) / float(max_value)
    return int(round(ratio * max_width))
