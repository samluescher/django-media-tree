Management Commands 
*******************

You can use the following management commands to assist you with media file 
management.


Orphaned files 
==============

Use the following command to list all orphaned files, i.e. media files existing 
in storage that are not in the database::

	manage.py mediaorphaned

Use the following command to **delete** all orphaned files::

	manage.py mediaorphaned --delete


Media cache 
===========

Use the following command to list all media cache files, such as thumbnails::

	manage.py mediacache

Use the following command to **delete** all media cache files::

	manage.py mediacache --delete
