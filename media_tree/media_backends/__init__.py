class ThumbnailError(Exception):
    pass
    
def get_media_backend():
    # TODO: make configurable
    from media_tree.media_backends.easy_thumbnails_backend import EasyThumbnailsBackend
    return EasyThumbnailsBackend
    