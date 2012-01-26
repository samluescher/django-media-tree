from media_tree.models import FileNode
from media_tree.utils.filenode import get_file_link
from django import template

register = template.Library()

def file_links(items, opts=None):
	result = []
	kwargs = {
		'use_metadata': True, 
		'include_size': True, 
		'include_extension': True, 
		'include_icon': True
	}
	if opts:
		kwargs.update(opts)
	for item in items:
		if isinstance(item, FileNode):
			result.append(get_file_link(item, **kwargs))
		else:
			result.append(file_links(item, kwargs))
	return result

register.filter(file_links)