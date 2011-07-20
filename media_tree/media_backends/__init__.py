from media_tree import app_settings
from media_tree.utils import get_module_attr

class ThumbnailError(Exception):
    pass
    
# TODO: Since media_backends is a tuple, there should actually be a way of 
# traversing these backends until a backend can handle a specific type of file.
def get_media_backend(fail_if_unconfigured=False):
    """
    Returns the MediaBackend subclass that is configured for use with 
    media_tree.
    """
    backends = app_settings.get('MEDIA_TREE_MEDIA_BACKENDS')
    if not len(backends):
        if fail_if_unconfigured:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('There is no media backend configured.'  \
                + ' Please define `MEDIA_TREE_MEDIA_BACKENDS` in your settings.')
        else:
            return False
    return get_module_attr(backends[0])
 
    
class MediaBackend:
    
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
