#from media_tree.admin.filenode_admin import *

from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory
from ..models import FileNode

class FileNodeAdmin(TreeAdmin):
    form = movenodeform_factory(FileNode)

admin.site.register(FileNode, FileNodeAdmin)
