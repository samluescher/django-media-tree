# TODO: move to extension
from modeltranslation.translator import translator, TranslationOptions
from media_tree.models import FileNode

class FileNodeTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'author', 'copyright', 'keywords', 'override_alt', 'override_caption')

translator.register(FileNode, FileNodeTranslationOptions)

