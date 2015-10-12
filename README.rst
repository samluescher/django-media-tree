Django Media Tree |latest-version|
**********************************

|travis-ci| |coveralls| |health| |downloads| |license|

Django Media Tree is a Django app for managing your website's media files in a
folder tree, and using them in your own applications.

.. |latest-version| image:: https://img.shields.io/pypi/v/django-media-tree.svg
   :alt: Latest version on PyPI
   :target: https://pypi.python.org/pypi/django-media-tree
.. |travis-ci| image:: https://travis-ci.org/samluescher/django-media-tree.svg
   :alt: Build status
   :target: https://travis-ci.org/samluescher/django-media-tree
.. |coveralls| image:: https://coveralls.io/repos/samluescher/django-media-tree/badge.svg
   :alt: Test coverage
   :target: https://coveralls.io/r/samluescher/django-media-tree
.. |health| image:: https://landscape.io/github/samluescher/django-media-tree/master/landscape.svg?style=flat
   :target: https://landscape.io/github/samluescher/django-media-tree/master
   :alt: Code Health
.. |downloads| image:: https://img.shields.io/pypi/dm/django-media-tree.svg
   :alt: Monthly downloads from PyPI
   :target: https://pypi.python.org/pypi/django-media-tree
.. |license| image:: https://img.shields.io/pypi/l/django-media-tree.svg
   :alt: Software license
   :target: https://github.com/samluescher/django-media-tree/blob/master/LICENSE

Key Features
============

* Enables you to organize all of your site media in nested folders.
* Supports various media types (images, audio, video, archives etc).
* Extension system, enabling you to easily add special processing for different
  media types and extend the admin interface.
* Speedy AJAX-enhanced admin interface with drag & drop and dynamic resizing.
* Upload queue with progress indicators (using Fine Uploader).
* Add metadata to all media to improve accessibility of your web sites.
* Integration with `Django CMS`_. Plugins include: image, slideshow, gallery,
  download list -- create your own!

.. _Django CMS: http://www.django-cms.org/

Documentation
=============

http://django-media-tree.readthedocs.org/

Development
===========

Contributors should make sure the demo project builds successfully with their
changes before placing a pull request on GitHub.  This is best done by running
the tests.

* Either: ``python setup.py -q test`` (run ``tox`` against all supported versions)
* Or: ``python setup.py test -a --skip-missing-interpreters`` (skip Python
  interpreters that are not available)
* Or: ``python setup.py test -a "-e py27-django16"`` (only test the Python 2.7
  + Django 1.6 combination)

It's also advisable to run ``flake8`` and address complaints before pushing
changes to ensure code health increases.
