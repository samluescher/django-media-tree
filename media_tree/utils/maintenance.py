from media_tree.utils import get_media_storage
from media_tree.media_backends import get_media_backend
from media_tree.models import FileNode
from media_tree import settings as app_settings
from unicodedata import normalize
import os


def get_cache_files():
    storage = get_media_storage()
    cache_files = []

    for cache_dir in get_media_backend().get_cache_paths():
        if storage.exists(cache_dir):
            files_in_dir = [storage.path(os.path.join(cache_dir, filename))  \
                for filename in storage.listdir(cache_dir)[1]]
            for file_path in files_in_dir:
                # need to normalize unicode path due to https://code.djangoproject.com/ticket/16315
                file_path = normalize('NFC', file_path)
                storage_name = os.path.join(cache_dir, os.path.basename(file_path))
                cache_files.append(storage_name)

    return cache_files


def get_broken_media():
    storage = get_media_storage()
    media_subdir = app_settings.MEDIA_TREE_UPLOAD_SUBDIR
    broken_nodes = []
    orphaned_files = []

    files_in_db = []
    for node in FileNode.objects.filter(node_type=FileNode.FILE):
        path = node.file.path
        # need to normalize unicode path due to https://code.djangoproject.com/ticket/16315
        path = normalize('NFC', path)
        files_in_db.append(path)
        if not storage.exists(node.file):
            broken_nodes.append(node)

    files_in_storage = [storage.path(os.path.join(media_subdir, filename))  \
        for filename in storage.listdir(media_subdir)[1]]

    for file_path in files_in_storage:
        # need to normalize unicode path due to https://code.djangoproject.com/ticket/16315
        file_path = normalize('NFC', file_path)
        if not file_path in files_in_db:
            storage_name = os.path.join(media_subdir, os.path.basename(file_path))
            orphaned_files.append(storage_name)

    return [broken_nodes, orphaned_files]


def get_orphaned_files():
    return get_broken_media()[1]
