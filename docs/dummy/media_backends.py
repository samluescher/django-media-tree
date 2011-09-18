from media_tree.media_backends import MediaBackend
from media_tree import media_types


class DummyBackend(MediaBackend):

    SUPPORTED_MEDIA_TYPES = (media_types.SUPPORTED_IMAGE,)

    @staticmethod
    def check_conf():
        pass

    @staticmethod
    def get_thumbnail(source, options):
        pass

    @staticmethod
    def get_valid_thumbnail_options():
        return ()