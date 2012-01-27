Django Media Tree Documentation
*******************************

Introduction
============

Django Media Tree is a Django app for managing your website's media files in a
folder tree, and using them in your own applications.

Key features:

* Enables you to organize all of your site media in nested folders.
* Supports various media types (images, audio, video, archives etc).
* Extension system, enabling you to easily add special processing for different
  media types and extend the admin interface.
* Speedy AJAX-enhanced admin interface.
* Upload queue with progress indicators (using SWFUpload).
* Add metadata to all media to improve accessibility of your web sites.
* Integration with `Django CMS <http://www.django-cms.org>`_. Plugins include:
  image, slideshow, gallery, download list -- create your own! 


The Media Tree application
==========================

.. toctree::
   :maxdepth: 2

   installation
   admin
   models
   configuration
   utils
   bundled_extensions
   

Extending und using Media Tree with other applications
======================================================

Your choices range from implementing file listing and detail views based on the
bundled generic view classes, extending Media Tree itself and its admin
interface, or writing custom plugins for use with your own applications.

.. toctree::
   :maxdepth: 2

   fields
   templates
   views
   extending
   custom_plugins
   bundled_plugins

   
Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

