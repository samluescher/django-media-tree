from media_tree import app_settings
from media_tree.utils import get_module_attr
from django.core.exceptions import ImproperlyConfigured

class ThumbnailError(Exception):
    pass
    
# TODO: Since media_backends is a tuple, there should actually be a way of 
# traversing these backends until a backend can handle a specific type of file.
def get_media_backend(fail_silently=True, handles_media_types=None):
    """
    Returns the MediaBackend subclass that is configured for use with 
    media_tree.
    """
    backends = app_settings.get('MEDIA_TREE_MEDIA_BACKENDS')
    if not len(backends):
        if not fail_silently:
            raise ImproperlyConfigured('There is no media backend configured.'  \
                + ' Please define `MEDIA_TREE_MEDIA_BACKENDS` in your settings.')
        else:
            return False
    for path in backends:
        backend = get_module_attr(path)
        if not handles_media_types or backend.handles_media_types(handles_media_types):
            return backend
    
    if not fail_silently:
        raise ImproperlyConfigured('There is no media backend configured to handle'  \
            ' the specified file types.')
    return False
    
    
class MediaBackend:
    
    SUPPORTED_MEDIA_TYPES = None
    SUPPORTED_FILE_EXTENSIONS = None
    
    @classmethod
    def handles_media_types(cls, media_types):
        return len(set(media_types) - set(cls.SUPPORTED_MEDIA_TYPES)) == 0 

    @staticmethod
    def handles_file_extensions(file_extensions):
        return len(set(file_extensions) - set(cls.SUPPORTED_FILE_EXTENSIONS)) == 0 
    
    @staticmethod
    def get_thumbnail(source, options):
        raise NotImplementedError('Media backends need to implement the `get_thumbnail()` method.')

    @staticmethod
    def get_valid_thumbnail_options():
        raise NotImplementedError('Media backends need to implement the `get_valid_thumbnail_options()` method.')

    @staticmethod
    def get_cache_paths():
        if hasattr(settings, 'THUMBNAIL_SUBDIR'):
            return (
                get_media_storage().path(
                os.path.join(app_settings.get('MEDIA_TREE_UPLOAD_SUBDIR'),
                    settings.THUMBNAIL_SUBDIR)),
            )
        return ()
