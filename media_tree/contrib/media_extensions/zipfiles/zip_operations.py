import zipfile
import os

def write_nodes_recursive(archive, nodes, parent_path=''):
    for node in nodes:
        arcname = os.path.join(parent_path, node.name)
        if node.is_file():
            archive.write(node.file.path, arcname)
        elif node.is_folder():
            write_nodes_recursive(archive, node.get_children(), arcname)

def compress_nodes(file, nodes):
    archive = zipfile.ZipFile(file, "w", zipfile.ZIP_DEFLATED)
    write_nodes_recursive(archive, nodes)
    archive.close()
    return archive