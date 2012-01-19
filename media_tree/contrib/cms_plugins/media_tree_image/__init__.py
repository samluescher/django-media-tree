"""
Plugin: Image
*************

This plugin allows you to put a single picture on a page, as a figure complete
with caption and other metadata.

Installation
============

To use this plugin, put ``media_tree.contrib.cms_plugins.media_tree_image`` 
in your installed apps, and run ``manage.py syncdb``.

Template
========

Override the template ``cms/plugins/media_tree_image.html`` if you want to 
customize the output. Please take a look at the default template for more 
information.

By default, images are rendered to the output using the template 
``media_tree/filenode/includes/figure.html``, which includes captions.
"""