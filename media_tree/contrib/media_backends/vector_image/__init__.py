from media_tree.media_backends import MediaBackend
from media_tree import media_types
from django.db.models.fields.files import FieldFile


class VectorThumbnail(FieldFile):
	def __init__(self, *args, **kwargs):
		super(VectorThumbnail, self).__init__(*args, **kwargs)
		self.width = None
		self.height = None


class VectorImageBackend(MediaBackend):
	"""
	Media backend for browser-supported vector files. Returns no real
	thumbnail, but a wrapper to the original vector image.
	"""
	
	SUPPORTED_MEDIA_TYPES = (media_types.VECTOR_IMAGE,)

	@staticmethod
	def supports_thumbnails():
		return True
	
	@staticmethod
	def get_thumbnail(source, options):
		thumb = VectorThumbnail(None, source, source.name)
		thumb.width = options['size'][0]
		thumb.height = options['size'][1]
		return thumb

	@staticmethod
	def get_valid_thumbnail_options():
		return ()
