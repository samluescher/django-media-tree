"""
This module provides a few template tags related to generating thumbnails and
image versions. You can use these tags in your templates after loading the tag
library as follows::

    {% load media_tree_thumbnail %}

.. Note::
   Most of the code of this module is an almost identical copy of
   easy_thumbnails' template tag, modified to work with ``FileNode`` sources and
   the configured ``MEDIA_BACKEND``. Hence, the :func:`thumbnail` tag is
   compatible to that of easy_thumbnails, but it will work with any
   thumbnail-generating application if you provide an appropriate
   ``MediaBackend`` class.
"""

from media_tree import settings as app_settings
from media_tree.models import FileNode
from media_tree.media_backends import get_media_backend
from media_tree import media_types
from django.conf import settings
from django import template
from django.template import Library, Node, VariableDoesNotExist, \
    TemplateSyntaxError
from django.utils.html import escape
import re


THUMBNAIL_SIZES = app_settings.MEDIA_TREE_THUMBNAIL_SIZES
RE_SIZE = re.compile(r'(\d+)x(\d+)$')
MEDIA_BACKEND = get_media_backend(fail_silently=False, handles_media_types=(
    media_types.SUPPORTED_IMAGE,))
VALID_OPTIONS = MEDIA_BACKEND.get_valid_thumbnail_options() if MEDIA_BACKEND else {}
register = template.Library()


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
    """Returns a pre-configured thumbnail size, or assigns it to a context
    variable.

    Basic tag syntax::

        {% thumbnail_size [size_name] [as var_name] %}
        
    The ``size`` parameter can be any of the size names configured using the
    setting ``MEDIA_TREE_THUMBNAIL_SIZES``. If omitted, the default size will
    be returned.
    
    If the ``as var_name`` clause is present, the size will be assigned to
    the respective context variable instead of being returned.
    
    You can use this template tag in conjunction with :func:`thumbnail` in order
    to use pre-configured thumbnail sizes in your templates.
    
    For example::
    
        {% thumbnail_size "large" as large_size %}
        {% thumbnail some_file large_size as large_thumb %}
        <img src="{{ large_thumb.url }} width="{{ large_thumb.width }} ... />
        
    """
    
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


register.tag(thumbnail_size)


def split_args(args):
    """
    Split a list of argument strings into a dictionary where each key is an
    argument name.

    An argument looks like ``crop``, ``crop="some option"`` or ``crop=my_var``.
    Arguments which provide no value get a value of ``True``.

    """
    args_dict = {}
    for arg in args:
        split_arg = arg.split('=', 1)
        if len(split_arg) > 1:
            value = split_arg[1]
        else:
            value = True
        args_dict[split_arg[0]] = value
    return args_dict


class ThumbnailNode(Node):
    def __init__(self, source_var, opts, context_name=None):
        self.source_var = source_var
        self.opts = opts
        self.context_name = context_name

    def render(self, context):
        # Note that this isn't a global constant because we need to change the
        # value for tests.
        raise_errors = getattr(settings, 'TEMPLATE_DEBUG', False)
        # Get the source file.
        try:
            source = self.source_var.resolve(context)
            if isinstance(source, FileNode):
                source = source.file
        except VariableDoesNotExist:
            if raise_errors:
                raise VariableDoesNotExist("Variable '%s' does not exist." %
                        self.source_var)
            return self.bail_out(context)
        # Resolve the thumbnail option values.
        try:
            opts = {}
            for key, value in self.opts.iteritems():
                if hasattr(value, 'resolve'):
                    value = value.resolve(context)
                opts[str(key)] = value
        except:
            if raise_errors:
                raise
            return self.bail_out(context)
            
        # Size variable can be either a tuple/list of two integers or a
        # valid string, only the string is checked.
        size = opts['size']
        if isinstance(size, basestring):
            m = RE_SIZE.match(size)
            if m:
                opts['size'] = (int(m.group(1)), int(m.group(2)))
            else:
                if raise_errors:
                    raise TemplateSyntaxError("Variable '%s' was resolved "
                            "but '%s' is not a valid size." %
                            (self.size_var, size))
                return self.bail_out(context)
        try:
            thumbnail = MEDIA_BACKEND.get_thumbnail(source, opts)
        except:
            if raise_errors:
                raise
            return self.bail_out(context)
        # Return the thumbnail file url, or put the file on the context.
        if self.context_name is None:
            return escape(thumbnail.url)
        else:
            context[self.context_name] = thumbnail
            return ''

    def bail_out(self, context):
        if self.context_name:
            context[self.context_name] = ''
        return ''


def thumbnail(parser, token):
    """
    Creates a thumbnail of an ``ImageField`` or ``FileNode`` representing a
    supported image file.

    Basic tag syntax::

        {% thumbnail [source] [size] [options] %}

    ``source`` can be a ``File`` object, usually an Image/FileField of a model
    instance, or a ``FileNode`` instance, whose ``file`` attribute will be 
    used as the source.

    ``size`` can either be:

    * the size in the format ``[width]x[height]`` (for example,
      ``{% thumbnail person.photo 100x50 %}``) or

    * a variable containing a valid size (i.e. either a string in the
      ``[width]x[height]`` format or a tuple containing two integers):
      ``{% thumbnail person.photo size_var %}``.

    *options* are a space separated list of options which are used when
    processing the image to a thumbnail such as ``sharpen``, ``crop`` and
    ``quality=90``.

    The thumbnail tag can also place a ``ThumbnailFile`` object in the context,
    providing access to the properties of the thumbnail such as the height and
    width::

        {% thumbnail [source] [size] [options] as [variable] %}

    When ``as [variable]`` is used, the tag does not return the absolute URL of
    the thumbnail.

    Having access to the ``ThumbnailFile`` object is extremely useful, since
    you should always include the width and height attributes in the output
    HTML.

    Example usage, passing the tag a ``FileNode`` instance::
    
        {% thumbnail some_node "100x200" as thumb %}
        <img src="{{ thumb.url }} alt="{{ some_node.alt }}"
            width="{{ thumb.width }} height="{{ thumb.height }}" />

    **Debugging**

    By default, if there is an error creating the thumbnail or resolving the
    image variable then the thumbnail tag will just return an empty string (and
    if there was a context variable to be set then it will also be set to an
    empty string).

    For example, you will not see an error if the thumbnail could not
    be written to directory because of permissions error. To display those
    errors rather than failing silently, set ``THUMBNAIL_DEBUG = True`` in
    your Django project's settings module.

    """
    args = token.split_contents()
    tag = args[0]

    # Check to see if we're setting to a context variable.
    if len(args) > 4 and args[-2] == 'as':
        context_name = args[-1]
        args = args[:-2]
    else:
        context_name = None

    if len(args) < 3:
        raise TemplateSyntaxError("Invalid syntax. Expected "
            "'{%% %s source size [option1 option2 ...] %%}' or "
            "'{%% %s source size [option1 option2 ...] as variable %%}'" %
            (tag, tag))

    opts = {}

    # The first argument is the source file.
    source_var = parser.compile_filter(args[1])

    # The second argument is the requested size. If it's the static "10x10"
    # format, wrap it in quotes so that it is compiled correctly.
    size = args[2]
    match = RE_SIZE.match(size)
    if match:
        size = '"%s"' % size
    opts['size'] = parser.compile_filter(size)

    # All further arguments are options.
    args_list = split_args(args[3:]).items()
    for arg, value in args_list:
        if arg in VALID_OPTIONS:
            if value and value is not True:
                value = parser.compile_filter(value)
            opts[arg] = value
        else:
            raise TemplateSyntaxError("'%s' tag received a bad argument: "
                                      "'%s'" % (tag, arg))
    return ThumbnailNode(source_var, opts=opts, context_name=context_name)

register.tag(thumbnail)
