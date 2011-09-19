.. _media-backends:

Using FileNodes in templates
****************************

Although Media Tree is designed to be agnostic of the module you use to generate
image versions and thumbnails, it includes some tags to assist you with
generating thumbnails from ``FileNode`` objects, since this is one of the most
common tasks when working with image files in web applications.


A word about Media Backends
===========================

Media Tree's template tags do not use an imaging toolkit directly, but an
abstraction class designed to wrap the actual image manipulation handled by a
third-party module (such as ``easy_thumbnails`` or ``sorl.thumbnail``, to name
two popular choices).

The advantage of wrapping thumbnail generation like this is that Media Tree does
not need to depend on a specific image generation library, with the additional
benefit that you can just use the abstract template tags in your templates and
switch to another ``MediaBackend`` at any time.


Thumbnail Template Tags
=======================

.. automodule:: media_tree.templatetags.media_tree_thumbnail
   :members:
   :exclude-members: split_args
   