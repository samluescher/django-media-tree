# encoding=utf-8
from media_tree.media_extenders import MediaExtender
from media_tree import media_types
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

class FocalPointExtender(MediaExtender):

    focal_x = models.DecimalField(_('Focal point X'), blank=True, null=True, max_digits=5, 
        decimal_places=3, validators=[MinValueValidator(0), MaxValueValidator(1)])
    focal_y = models.DecimalField(_('Focal point Y'), blank=True, null=True, max_digits=5, 
        decimal_places=3, validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text=_('Drag the marker on the image thumbnail to its most relevant portion. You can then use this information to crop the image accordingly.'))

    def get_crop(self):
        x = ''
        y = ''
        if self.focal_x != None:
            x = str(int(round(self.focal_x * 100)))
        if self.focal_y != None:
            y = str(int(round(self.focal_y * 100)))
        return "%s,%s" % (x, y)

