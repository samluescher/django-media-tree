"""
Plugin: Gallery
***************

This plugin allows you to put an image gallery on a page. Galleries can include
nested folder structures or display merged (flat) compositions of all images in 
a range of subfolders. Pictures can be browsed or auto-played.

Installation
============

To use this plugin, put ``media_tree.contrib.cms_plugins.media_tree_gallery`` 
in your installed apps, and run ``manage.py syncdb``.

Template
========

Override the template ``cms/plugins/media_tree_gallery.html`` if you want to 
customize the output. Please take a look at the default template for more 
information.

By default, images are rendered to the output using the template 
``media_tree/filenode/includes/figure.html``, which includes captions.

.. Note::
   The default template requires you to include `jQuery <http://jquery.com/>`_
   in your pages, since it uses the `jQuery Cycle Plugin 
   <http://jquery.malsup.com/cycle/>`_ (bundled) for image transitions.
"""