from typing import NoReturn

from django.db.models import QuerySet

import django_filters
from rest_framework.exceptions import NotFound

import restaurant.models as models


class DishFilterSet(django_filters.FilterSet):
    restaurant = django_filters.NumberFilter(method='filter_by_restaurant')

    class Meta:
        model = models.Dish
        fields = ['restaurant']

    def filter_by_restaurant(self, queryset: QuerySet, name: str, value: int) -> models.Dish | NoReturn:
        if not models.Restaurant.objects.filter(pk=value).exists():
            raise NotFound(detail=f'Restaurant with id={value} was not found')
        return queryset.filter(restaurant_id=value)
