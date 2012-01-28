from media_tree.models import FileNode
from media_tree.utils.filenode import get_file_link
from django import template

register = template.Library()

def get_kwargs_for_file_link(opts):
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
	return kwargs	

def file_links(items, opts=None):
	"""
	Turns a (optionally nested) list of FileNode objects into a list of 
	strings, linking to the associated files.
	"""
	result = []
	kwargs = get_kwargs_for_file_link(opts)
	for item in items:
		if isinstance(item, FileNode):
			result.append(get_file_link(item, **kwargs))
		else:
			result.append(file_links(item, kwargs))
	return result

register.filter(file_links)

def file_link(node, opts=None):
	"""
	Turns a FileNode object into a string, linking to the associated file.
	"""
	kwargs = get_kwargs_for_file_link(opts)
	return get_file_link(node, **kwargs)

register.filter(file_link)