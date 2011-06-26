class ThumbnailError(Exception):
    pass
    
def get_media_backend():
    # TODO: make configurable
    from media_tree.media_backends.easy_thumbnails_backend import EasyThumbnailsBackend
    return EasyThumbnailsBackend
    
    
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
    