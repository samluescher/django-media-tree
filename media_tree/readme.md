Django Media Tree
=================

@TODO: installer package with proper dependencies

A Django app for managing your site media (images, audio, video, archives etc.) and organizing it in one central, tree-based location.

__Features__:

* Enables you to organize all of your site media in nested folders  
* Supports various media types (images, audio, video, archives etc.) 
* Multi-upload queue with progress indicators (using SWFUpload)
* Add metadata to all media for accessible web sites 
* Integration with [Django CMS](http://www.django-cms.org). Plugins include: Image, slideshow, gallery, download list – roll your own! 
* Plugin interface based on Django's admin actions, allowing you to write your own batch-processing actions 
* Extension interface for custom media types with extra fields, based on signals
* Uses mptt to efficiently model a file-and-folder system, allowing you to select whole folder trees with little database load 
