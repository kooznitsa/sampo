from django.db import models as django_models
from django.db.models.query import QuerySet


class RestaurantQuerySet(django_models.QuerySet):

    def with_dishes(self) -> QuerySet:
        return self.filter(dishes__isnull=False).distinct()
