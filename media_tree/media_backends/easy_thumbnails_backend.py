from media_tree.media_backends import ThumbnailError
from easy_thumbnails.files import get_thumbnailer


class EasyThumbnailsBackend(object):
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
