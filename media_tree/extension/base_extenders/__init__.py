from django.forms.widgets import MediaDefiningClass
from media_tree.forms import FileForm


class MediaTreeExtender(object):

    @classmethod
    def contribute(extender, extended_class=None):
        raise NotImplementedError('Class `%s` has not implemented a `contribute()` method.' % extender)


class MediaDefiningExtender(MediaTreeExtender):
    __metaclass__ = MediaDefiningClass
    class Meta:
        pass
    
    @classmethod
    def contribute(extender, extended_class=FileForm):
        # TODO this should raise a NotImplementedError if class does not
        # define its own contribute()
        if hasattr(extender, 'Media'):
            combined_media = extended_class().media + extender().media
            class NewMediaClass:
                js = combined_media._js
                css = combined_media._css
            extended_class.Media = NewMediaClass
        # TODO: what about the `extend` property? Media extender should
        # be able to override media instead of extending.

        # TODO: Maybe do this more elegantly = SEE:
        # https://docs.djangoproject.com/en/dev/topics/forms/media/#media-as-a-dynamic-property
        #
        #    def _media(self):
        #        return forms.Media(css={'all': ('pretty.css',)},
        #                           js=('animations.js', 'actions.js'))
        #    media = property(_media)
