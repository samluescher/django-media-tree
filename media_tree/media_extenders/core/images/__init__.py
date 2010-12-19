# encoding=utf-8
from media_tree.media_extenders import MediaExtender
from django.db import models
from django.utils.translation import ugettext_lazy as _
from media_tree import media_types
from PIL import Image
from PIL.ExifTags import TAGS
from django.db.models import fields
from django.utils.encoding import smart_unicode, smart_str
from django.conf import settings
from datetime import datetime

# http://mostrom.eu/tutorials-and-code/using-pil-to-read-iptc-python
from PIL import IptcImagePlugin

IPTC_KEY_MAP = {
    (2,5): 'title',
    (2,105): 'title',
    (2,120): 'description',
    (2,116): 'copyright',
    (2,25): 'keywords',
    (2,80): 'author',
    (2,55): 'date_time',
}

def get_iptc_info(instance):
    im = instance.saved_image
    info = {}
    iptc = IptcImagePlugin.getiptcinfo(im)
    for key, value in iptc.items():
        if key in IPTC_KEY_MAP:
            info[IPTC_KEY_MAP[key]] = value
    return info	

EXIF_KEY_MAP = {
    'DateTimeOriginal': 'date_time',
    'DateTimeDigitized': 'date_time'
}

def get_exif_info(instance):
    im = instance.saved_image
    info = {}
    exif_info = im._getexif()
    for tag, value in exif_info.items():
        key = TAGS.get(tag, tag)
        if key in EXIF_KEY_MAP:
            info[EXIF_KEY_MAP[key]] = value
    return info

STRING_ENCODING_GUESS = getattr(settings, 'EXIFIPTC_STRING_ENCODING_GUESS', ['utf8', 'macroman', 'us-ascii', 'iso-8859-1', 'iso-8859-2', 'windows-1250','windows-1252'])

def guess_string_encoding_and_convert(text):
    from django.utils.encoding import smart_unicode
    converted = None
    for encoding in STRING_ENCODING_GUESS:
        try:
            return smart_unicode(text, encoding, errors='strict')
        except:
            pass
    return text

DATE_FORMAT_GUESS = getattr(settings, 'EXIFIPTC_DATE_FORMAT_GUESS', ['%Y%m%d', '%Y:%m:%d %H:%M:%S', '%Y:%m:%d', '%Y-%m-%d'])

def guess_date_format_and_convert(text):
    for format in DATE_FORMAT_GUESS:
        try:
            return datetime.strptime(text, format)
        except ValueError:
            pass
    from lib.dateutil import parser
    try:
        value = parser.parse(text)
    except ValueError:
        value = None
    return value

class ExifIptcExtender(MediaExtender):
    """
    Extracts IPTC and EXIF metadata using PIL and uses the information for the 
    corresponding fields of the FileNode instance.
    """
    
    # TODO make add Exif extender and add fields
    # aperture = models.FloatField(_('Aperture'), max_length=255)
    # OR just add EXIF fields to extra_metadata PickledField
    @staticmethod
    def pre_save(sender, **kwargs):
        instance = kwargs['instance']
        if instance.media_type == media_types.SUPPORTED_IMAGE and getattr(instance, 'saved_image', None):
            info = {}
            try:
                info.update(get_exif_info(instance))
            except:
                pass
            try:
                info.update(get_iptc_info(instance))
            except:
                pass
            for key, value in info.items():
                current_value = getattr(instance, key)
                field = instance._meta.get_field(key)
                if issubclass(field.__class__, fields.CharField) or issubclass(field.__class__, fields.TextField):
                    if isinstance(value, list):
                        value = ', '.join(value)
                    value = guess_string_encoding_and_convert(value)
                    # concatenate strings
                    if value and current_value:
                        value = current_value+' '+value
                elif current_value:
                    # non-string fields won't be overwritten
                    value = None
                else:
                    # type conversions should happen here
                    if issubclass(field.__class__, fields.DateField):
                        value = guess_date_format_and_convert(value)
                if value:
                    setattr(instance, key, value)
