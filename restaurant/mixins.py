from django.db import models


class DateTimeMixin(models.Model):
    created_at = models.DateTimeField(verbose_name='Время создания', auto_now_add=True, null=True)
    updated_at = models.DateTimeField(verbose_name='Время обновления', auto_now=True, null=True)

    class Meta:
        abstract = True
