from django.db import models as django_models
from django.db.models import F, Q
from django.db.models.functions import TruncDate
from django.db.models.query import QuerySet


class RestaurantQuerySet(django_models.QuerySet):

    def with_dishes(self) -> QuerySet:
        return self.filter(dishes__isnull=False).distinct()


class DishQuerySet(django_models.QuerySet):

    def available(self) -> QuerySet:
        """Get dishes which have restaurants with no update date
        or dishes updated no later than corresponding restaurants' menus.
        """
        return (
            self.annotate(update_date=TruncDate('updated_at'))
            .filter(Q(restaurant__menu_update_date__isnull=True) | Q(update_date__gte=F('restaurant__menu_update_date')))
        )
