"""
The module ``media_tree.contrib.cms_plugins`` contains a number of plugins for
using ``FileNode`` objects on pages created with
`Django CMS <https://www.django-cms.org>`_.

Installation
============

For optimum admin functionality when using these plugins, you should put
``media_tree.contrib.cms_plugins`` in your installed apps, and run 
``manage.py collectstatic``.

If you are not using the ``staticfiles`` app, you have to manually copy 
the contents of the ``static`` folder to your static root.

"""

# TODO: Needs to honor published=False, also of subfolders.