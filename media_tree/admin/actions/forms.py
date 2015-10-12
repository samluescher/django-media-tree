from media_tree.models import FileNode
from media_tree.fields import FileNodeChoiceField
from media_tree.forms import MetadataForm
from media_tree.utils import get_media_storage
from django import forms
from django.forms.util import ErrorList
from django.utils.translation import ugettext as _
from django.contrib.admin import helpers
from django.core.files.uploadedfile import UploadedFile
from django.db.models import FileField
from mptt.exceptions import InvalidMove

# TODO: mptt currently ignores order_insertion_by when calling insert_at or move_to. Bug report pending.

class FileNodeActionsForm(forms.Form):

    enable_target_node_field = False
    confirm_fields = None

    def __init__(self, queryset, *args, **kwargs):
        self.success_count = 0
        super(FileNodeActionsForm, self).__init__(*args, **kwargs)
        valid_targets = FileNode._tree_manager.filter(node_type=FileNode.FOLDER)
        self.selected_nodes = queryset

        selected_nodes_pk = []
        if queryset:
            for node in queryset:
                opts = node._mptt_meta
                selected_nodes_pk.append(node.pk)
                valid_targets = valid_targets.exclude(**{
                    opts.tree_id_attr: getattr(node, opts.tree_id_attr),
                    '%s__gte' % opts.left_attr: getattr(node, opts.left_attr),
                    '%s__lte' % opts.right_attr: getattr(node, opts.right_attr),
                })
            self.fields[helpers.ACTION_CHECKBOX_NAME] = forms.ModelMultipleChoiceField(queryset=FileNode.objects.all(), initial=selected_nodes_pk, required=True, widget=forms.widgets.MultipleHiddenInput())

        self.fields['action'] = forms.CharField(initial=self.action_name, required=True, widget=forms.widgets.HiddenInput())
        if self.enable_target_node_field:
            self.fields['target_node'] = FileNodeChoiceField(label=_('to'), queryset=valid_targets, required=False)
        self.fields['execute'] = forms.BooleanField(initial=True, required=True, widget=forms.widgets.HiddenInput())

    def get_selected_nodes(self):
        if hasattr(self, 'cleaned_data') and helpers.ACTION_CHECKBOX_NAME in self.cleaned_data:
            return self.cleaned_data[helpers.ACTION_CHECKBOX_NAME]
        else:
            return self.selected_nodes

    def clean(self):
        if self.confirm_fields:
            self.confirmed_data = {}
            for key in self.confirm_fields:
                if key in self.cleaned_data and self.data.get('confirm_'+key, False):
                    self.confirmed_data[key] = self.cleaned_data[key]
        return self.cleaned_data


class FileNodeActionsWithUserForm(FileNodeActionsForm):

    def __init__(self, queryset, user, *args, **kwargs):
        super(FileNodeActionsWithUserForm, self).__init__(queryset, *args, **kwargs)
        self.user = user


class MoveSelectedForm(FileNodeActionsWithUserForm):

    action_name = 'move_selected'
    enable_target_node_field = True

    def move_node(self, node, target):
        try:
            # Reload object because tree attributes may be out of date
            node = node.__class__.objects.get(pk=node.pk)
            descendant_count = node.get_descendants().count()

            if node.parent != target:
                node.parent = target
                node.attach_user(self.user, change=True)
                node.save()
                self.success_count += 1 + descendant_count
            return node
        except InvalidMove as e:
            self.errors[NON_FIELD_ERRORS] = ErrorList(e)
            raise

    def save(self):
        """
        Attempts to move the nodes using the selected target and
        position.

        If an invalid move is attempted, the related error message will
        be added to the form's non-field errors and the error will be
        re-raised. Callers should attempt to catch ``InvalidMove`` to
        redisplay the form with the error, should it occur.
        """
        self.success_count = 0
        for node in self.get_selected_nodes():
            self.move_node(node, self.cleaned_data['target_node'])


class CopySelectedForm(FileNodeActionsWithUserForm):

    action_name = 'copy_selected'
    enable_target_node_field = True

    def copy_node(self, node, target):

        def clone_node(from_node):
            copy_additional_fields = ('node_type',)
            args = dict([(fld.name, getattr(from_node, fld.name))
                for fld in from_node._meta.fields
                    if fld.name in copy_additional_fields or fld.editable  \
                    and fld != from_node._meta.auto_field  \
                    and not isinstance(fld, FileField)])
            return from_node.__class__(**args)

        def make_uploaded_files(node, from_node):
            for fld in node._meta.fields:
                if isinstance(fld, FileField):
                    # Creating an UploadedFile from the original file results in the file being copied on disk on save()
                    existing_file = getattr(from_node, fld.name)
                    uploaded_file = UploadedFile(existing_file, existing_file.name, None, from_node.size)
                    setattr(node, fld.name, uploaded_file)

        new_node = clone_node(node)
        make_uploaded_files(new_node, node)
        new_node.parent = target
        new_node.attach_user(self.user, change=True)
        new_node.save()
        if new_node.node_type == FileNode.FOLDER:
            self.copy_nodes_rec(node.get_children(), new_node)
        return new_node

    def copy_nodes_rec(self, nodes, target):
        for node in nodes:
            self.copy_node(node, target)
            self.success_count += 1

    def save(self):
        self.success_count = 0
        self.copy_nodes_rec(self.get_selected_nodes(), self.cleaned_data['target_node'])


class ChangeMetadataForSelectedForm(FileNodeActionsWithUserForm):

    action_name = 'change_metadata_for_selected'
    enable_target_node_field = False
    confirm_fields = []

    recursive = forms.BooleanField(label=_('Change metadata of all child objects'), required=False)

    def __init__(self, *args, **kwargs):
        super(ChangeMetadataForSelectedForm, self).__init__(*args, **kwargs)
        copy_form = MetadataForm()
        copy_fields = copy_form.fields
        exclude = MetadataForm.Meta.exclude
        for key in copy_fields.keys():
            if not key in self.fields and not key in exclude:
                self.confirm_fields.append(key)
                self.fields[key] = copy_fields[key]
                model_field = copy_form.instance._meta.get_field(key)
                if model_field.validators:
                    for validator in model_field.validators:
                        if not validator in self.fields[key].validators:
                            self.fields[key].validators.append(validator)

    def update_node(self, node, metadata):
        changed = False
        for key in metadata:
            if getattr(node, key) != metadata[key]:
                setattr(node, key, metadata[key])
                changed = True
        node.attach_user(self.user, change=True)
        node.save()
        return changed

    def save_nodes_rec(self, nodes):
        for node in nodes:
            if self.update_node(node, self.confirmed_data):
                self.success_count += 1
            if self.cleaned_data['recursive'] and node.is_folder():
                self.save_nodes_rec(node.get_children())

    def save(self):
        self.success_count = 0
        self.save_nodes_rec(self.get_selected_nodes())


class StorageFilesForm(FileNodeActionsForm):

    def __init__(self, queryset, orphaned_files_choices, *args, **kwargs):
        self.success_files = []
        self.error_files = []
        super(StorageFilesForm, self).__init__(queryset, *args, **kwargs)
        self.fields['selected_files'] = forms.MultipleChoiceField(label=self.selected_files_label, choices=orphaned_files_choices, widget=forms.widgets.CheckboxSelectMultiple)


class DeleteStorageFilesForm(StorageFilesForm):

    def __init__(self, *args, **kwargs):
        super(DeleteStorageFilesForm, self).__init__(*args, **kwargs)
        self.fields['confirm'] = confirm = forms.BooleanField(label=_('Yes, I am sure that I want to delete the selected files from storage:'))

    def save(self):
        """
        Deletes the selected files from storage
        """
        storage = get_media_storage()
        for storage_name in self.cleaned_data['selected_files']:
            full_path = storage.path(storage_name)
            try:
                storage.delete(storage_name)
                self.success_files.append(full_path)
            except OSError:
                self.error_files.append(full_path)


class DeleteOrphanedFilesForm(DeleteStorageFilesForm):

    action_name = 'delete_orphaned_files'
    selected_files_label = _('The following files exist in storage, but are not found in the database')


class DeleteCacheFilesForm(DeleteStorageFilesForm):

    action_name = 'clear_cache'
    selected_files_label = _('Cache files')
