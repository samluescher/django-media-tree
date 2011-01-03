from django import template
from sorl.thumbnail.templatetags.thumbnail import ThumbnailNode, thumbnail as sorl_thumbnail
import logging
from django.conf import settings
from media_tree import app_settings
import copy

THUMBNAIL_EXTENSIONS = app_settings.get('MEDIA_TREE_THUMBNAIL_EXTENSIONS')
THUMBNAIL_SIZES = app_settings.merge('MEDIA_TREE_THUMBNAIL_SIZES')

"""
Improvements over ThumbnailNode class:
- Preserves the original image's extension if possible, i.e. PNG images will have PNG thumbnails.
- Merges global thumbnail options with specific thumbnail options (sharpening is usually a good idea)
- [removed because obsolete] Size var can be a key of a pre-defined size in settings.MEDIA_TREE_THUMBNAIL_SIZESS dict 
"""
class MediaTreeThumbnailNode(ThumbnailNode):

    def __init__(self, *args, **kwargs):
        kwargs['extension'] = template.Variable('extension')
        super(MediaTreeThumbnailNode, self).__init__(*args, **kwargs)
        self._image_var_name = self.source_var.var.var+'.file'
        opts = app_settings.get('MEDIA_TREE_GLOBAL_THUMBNAIL_OPTIONS')
        opts.update(self.opts)
        self.opts = opts

    def render(self, context):
        file_node = self.source_var.resolve(context)
        self.source_var.var = template.Variable(self._image_var_name)

        #size = str(self.size_var.resolve(context))
        #if hasattr(settings, 'MEDIA_TREE_THUMBNAIL_SIZESS') and settings.MEDIA_TREE_THUMBNAIL_SIZESS.has_key(size):
        #    self.size_var = template.Variable('"'+settings.MEDIA_TREE_THUMBNAIL_SIZESS[size]+'"')

        if hasattr(file_node, 'extension') and file_node.extension in THUMBNAIL_EXTENSIONS:
            context['extension'] = file_node.extension
        else:
            context['extension'] = None
        
        try:
            return super(MediaTreeThumbnailNode, self).render(context)
        except:
            return ''

def node_thumbnail(parser, token):
    node = sorl_thumbnail(parser, token)
    return MediaTreeThumbnailNode(node.source_var, node.size_var, opts=node.opts, context_name=node.context_name)

class ThumbnailSizeNode(template.Node):
    def __init__(self, size_name=None, context_name=None):
        if size_name:
            self.size_name = template.Variable(size_name)
        else:
            self.size_name = None
        self.context_name = context_name

    def render(self, context):
        if self.size_name:
            size_name = self.size_name.resolve(context)
        else:
            size_name = 'default'

        if not THUMBNAIL_SIZES.has_key(size_name):
            raise template.TemplateSyntaxError('settings.MEDIA_TREE_THUMBNAIL_SIZES has no element "%s"' % size_name)
        size = THUMBNAIL_SIZES[size_name]
        
        if self.context_name:
            context[self.context_name] = size
            return ''
        else:
            return size

def thumbnail_size(parser, token):
    args = token.split_contents()
    tag = args.pop(0)
    if len(args) >= 2 and args[-2] == 'as':
        context_name = args[-1]
        args = args[:-2]
    else:
        context_name = None

    if len(args) > 1:
        raise template.TemplateSyntaxError("Invalid syntax. Expected "
            "'{%% %s [\"size_name\"] [as context_var] %%}'" % tag)
    elif len(args) == 1:
        size_name = args[0]
    else:
        size_name = None

    return ThumbnailSizeNode(size_name=size_name, context_name=context_name)

register = template.Library()
register.tag(node_thumbnail)
register.tag(thumbnail_size)
