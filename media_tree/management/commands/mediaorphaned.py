from media_tree.utils.maintenance import get_orphaned_files
from media_tree.utils import get_media_storage
from django.core.management.base import BaseCommand, CommandError
from optparse import make_option

class Command(BaseCommand):

    help = 'Lists (and optionally deletes) all media_tree orphaned files, '  \
        + 'i.e. media files existing in storage that are not in the database.'

    option_list = BaseCommand.option_list + (
        make_option('--delete',
            action='store_true',
            dest='delete',
            default=False,
            help='Delete all orphaned files from storage'),
        )

    def handle(self, *args, **options):
        orphaned_files = get_orphaned_files()
        storage = get_media_storage()
        for path in orphaned_files:
            if options['delete']:
                storage.delete(path)
                self.stdout.write("Deleted %s\n" % storage.path(path))
            else:
                self.stdout.write("%s\n" % storage.path(path))
