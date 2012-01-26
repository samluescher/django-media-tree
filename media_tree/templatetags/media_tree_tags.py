from media_tree.models import FileNode
from media_tree.utils.filenode import get_file_link
from django import template

register = template.Library()

def file_links(items, opts=None):
	"""
	Turns a (optionally nested) list of FileNode objects into a list of 
	strings, linking to the associated files.
	"""
	result = []
	kwargs = {
		'use_metadata': False, 
		'include_size': False, 
		'include_extension': False, 
		'include_icon': False
	}
	if isinstance(opts, basestring):
		for key in opts.split(' '):
			kwargs[key] = True 
	elif isinstance(opts, dict):
		kwargs.update(opts)
	for item in items:
		if isinstance(item, FileNode):
			result.append(get_file_link(item, **kwargs))
		else:
			result.append(file_links(item, kwargs))
	return result

register.filter(file_links)