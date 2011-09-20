from media_tree import settings as app_settings
from media_tree.utils import get_module_attr
from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.core.files.storage import FileSystemStorage
from django.core.files.base import File
import os


ICON_DIRS = app_settings.MEDIA_TREE_ICON_DIRS


def get_static_storage():
    # Passing FileSystemStorage the STATIC_ROOT and STATIC_URL settings
    # if set will make it work with django.contrib.staticfiles while, if
    # those settings don't exist, it will fall back to MEDIA_ROOT / 
    # MEDIA_URL by default.
    return FileSystemStorage(
        location=getattr(settings, 'STATIC_ROOT', None),
        base_url=getattr(settings, 'STATIC_URL', None))


STATIC_STORAGE = get_static_storage()


class StaticFile(FieldFile):
    """
    A wrapper for static files that is compatible to the FieldFile class, i.e.
    you can use instances of this class in templates just like you use the value
    of FileFields (e.g. `{{ my_static_file.url }}`) 
    """
    def __init__(self, instance, name):
        File.__init__(self, None, name)
        self.instance = instance
        self.storage = STATIC_STORAGE
        self.field = self
        self.is_icon = True

    def save(self, *args, **kwargs):
        raise NotImplementedError('Static files are read-only')

    def delete(self, *args, **kwargs):
        raise NotImplementedError('Static files are read-only')

    def __unicode__(self):
        return self.instance.__unicode__()

    def alt(self):
        return self.instance.alt()


class StaticPathFinder:

    @staticmethod
    def find(names, dirs, file_ext):
        """
        Iterating a set of dirs under the static root, this method tries to find
        a file named like one of the names and file ext passed, and returns the
        storage path to the first file it encounters.
        
        Using this method makes it possible to override static files (such as 
        icon sets) in a similar way like templates in different locations can
        override others that have the same file name.
        """
        if not isinstance(names, list) or isinstance(names, tuple):
            names = (names,)
        for dir_name in dirs:
            for name in names:
                path = os.path.join(dir_name, name + file_ext)
                if STATIC_STORAGE.exists(path):
                    return path
    
    
class MimetypeStaticIconFileFinder:
    
    @staticmethod
    def find(file_node, dirs=ICON_DIRS, default_name=None, file_ext='.png'):
        """
        Iterating all icon dirs, try to find a file called like the node's
        extension / mime subtype / mime type (in that order).
        For instance, for an MP3 file ("audio/mpeg"), this would look for:
        "mp3.png" / "audio/mpeg.png" / "audio.png" 
        """
        names = []
        for attr_name in ('extension', 'mimetype', 'mime_supertype'):
            attr = getattr(file_node, attr_name)
            if attr:
                names.append(attr)
        if default_name:
            names.append(default_name)
        icon_path = StaticPathFinder.find(names, dirs, file_ext)
        if icon_path:
            return StaticFile(file_node, icon_path)


# TODO: Find a better way of caching ICON_FINDERS (and what about threads and different settings files defining different icon finders?) 
ICON_FINDERS = None

def get_icon_finders(finder_names):
    global ICON_FINDERS
    if not ICON_FINDERS:
        finders = []
        for finder_name in finder_names:
            finder = get_module_attr(finder_name)
            if not hasattr(finder, 'find'):
                raise ImproperlyConfigured('Module "%s" does not define a "find" method' % finder_name)
            finders.append(finder)
        ICON_FINDERS = finders
    return ICON_FINDERS
