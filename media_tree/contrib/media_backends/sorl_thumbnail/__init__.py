from media_tree.media_backends import MediaBackend, ThumbnailError
from sorl.thumbnail import get_thumbnail

class SorlThumbnailsBackend(MediaBackend):
    """
    Media backend for sorl.thumbnails support. 
    Experimental and currently not officially supported.
    """
    
    SUPPORTED_MEDIA_TYPES = (media_types.SUPPORTED_IMAGE,)
    
    @staticmethod
    def get_thumbnail(source, options):
        size = options['size']
        del options['size']
        if not isinstance(size, basestring):
            size = 'x'.join([str(s) for s in size])
        try:
            thumbnail = get_thumbnail(source, size, **options)
        except Exception as inst:
            raise ThumbnailError(inst)
        return thumbnail

