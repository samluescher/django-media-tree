from django import template

register = template.Library()

def media_tree_listing(cl):
	pass
media_tree_listing = register.inclusion_tag('media_tree/filenode/listing.html')(media_tree_listing)
