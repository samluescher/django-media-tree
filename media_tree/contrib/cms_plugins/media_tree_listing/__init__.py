"""
Plugin: File listing
********************

This plugin allows you to put a file listing on a page, displaying download
links for the selected ``FileNode`` objects in a folder tree.

The folder tree does not have to be identical to the actual tree in your 
media library. Instead, you can create arbitrarily nested structures, or output
a merged (flat) list.

Installation
============

To use this plugin, put ``media_tree.contrib.cms_plugins.media_tree_listing`` 
in your installed apps, and run ``manage.py syncdb``.

Template
========

Override the template ``cms/plugins/media_tree_listing.html`` if you want to 
customize the output. Please take a look at the default template for more 
information.
"""