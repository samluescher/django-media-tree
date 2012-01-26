from media_tree.media_backends import MediaBackend, ThumbnailError
from media_tree.utils import get_media_storage
from media_tree import settings as app_settings
from media_tree import media_types
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails import utils
from django.conf import settings
import os


class EasyThumbnailsBackend(MediaBackend):
    """
    Media backend for easy_thumbnails support. 
    """

    SUPPORTED_MEDIA_TYPES = (media_types.SUPPORTED_IMAGE,)

    @staticmethod
    def check_conf():
        if not 'easy_thumbnails' in settings.INSTALLED_APPS:
            from django.core.exceptions import ImproperlyConfigured
            raise ImproperlyConfigured('`easy_thumbnails` is not in your INSTALLED_APPS.')

    @staticmethod
    def get_thumbnail(source, options):
        try:
            opts = {}
            opts.update(app_settings.MEDIA_TREE_GLOBAL_THUMBNAIL_OPTIONS or {})
            opts.update(options)
            thumbnail = get_thumbnailer(source).get_thumbnail(opts)
        except Exception as inst:
            EasyThumbnailsBackend.check_conf()
            if app_settings.MEDIA_TREE_MEDIA_BACKEND_DEBUG:
                raise ThumbnailError(inst)
            else:
                return None
        return thumbnail

    @staticmethod
    def get_valid_thumbnail_options():
        options = utils.valid_processor_options()
        options.remove('size')
        return options

    @staticmethod
    def get_cache_paths(subdirs=None):
        if hasattr(settings, 'THUMBNAIL_SUBDIR'):
            return MediaBackend.get_cache_paths((settings.THUMBNAIL_SUBDIR,))
        return ()