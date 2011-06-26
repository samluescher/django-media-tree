from media_tree.media_backends import MediaBackend, ThumbnailError
from media_tree.utils import get_media_storage
from media_tree import app_settings
from easy_thumbnails.files import get_thumbnailer
from easy_thumbnails import utils
from django.conf import settings
import os


class EasyThumbnailsBackend(MediaBackend):
    """
    Media backend for easy_thumbnails support. 
    """

    @staticmethod
    def get_thumbnail(source, options):
        try:
            thumbnail = get_thumbnailer(source).get_thumbnail(options)
        except Exception as inst:
            raise ThumbnailError(inst)
        return thumbnail

    @staticmethod
    def get_valid_thumbnail_options():
        options = utils.valid_processor_options()
        options.remove('size')
        return options