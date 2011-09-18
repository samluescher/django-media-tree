from media_tree.media_backends import MediaBackend
from media_tree import media_types

class DummyBackend(MediaBackend):
    """
    Media backend for easy_thumbnails support. 
    """

    SUPPORTED_MEDIA_TYPES = (media_types.SUPPORTED_IMAGE,)

