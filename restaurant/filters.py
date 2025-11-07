from typing import NoReturn, TYPE_CHECKING

from django.contrib.admin import SimpleListFilter
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet

import django_filters
from rest_framework.exceptions import NotFound

import restaurant.models as models

if TYPE_CHECKING:
    from restaurant.admin import DishAdmin, RestaurantAdmin


class DishFilterSet(django_filters.FilterSet):
    restaurant = django_filters.NumberFilter(method='filter_by_restaurant', label='Restaurant ID.')
    available_only = django_filters.NumberFilter(
        method='filter_available_only',
        label='Available only',
        help_text='0 = all dishes, 1 = only available.',
    )

    class Meta:
        model = models.Dish
        fields = ['restaurant', 'available_only']

    def filter_by_restaurant(self, queryset: QuerySet, name: str, value: int) -> QuerySet | NoReturn:
        if not models.Restaurant.objects.filter(pk=value).exists():
            raise NotFound(detail=f'Restaurant with id={value} was not found')
        return queryset.filter(restaurant_id=value)

    def filter_available_only(self, queryset: QuerySet, name: str, value: str | int | bool) -> QuerySet:
        if value in [1, '1', True, 'true']:
            return queryset.available()
        return queryset


class DishPriceFilter(SimpleListFilter):
    title = 'Цена'
    parameter_name = 'price'

    def lookups(self, request: WSGIRequest, model_admin: 'DishAdmin') -> list[tuple]:
        return [
            ('0-1', 'До 1 ₽'),
            ('1-100', 'От 1 до 100 ₽'),
            ('100-200', 'От 100 до 200 ₽'),
            ('200-500', 'От 200 до 500 ₽'),
            ('500-1000', 'От 500 до 1000 ₽'),
            ('1000-2000', 'От 1000 до 2000 ₽'),
            ('2000-5000', 'От 2000 до 5000 ₽'),
            ('5000-10_000', 'От 5000 до 10 000 ₽'),
            ('10_000', 'От 10 000 ₽'),
        ]

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value():
            value = self.value().split('-')
            try:
                queryset = queryset.filter(
                    price__gte=value[0],
                    price__lte=value[1],
                )
            except IndexError:
                queryset = queryset.filter(price__gte=value[0])
        return queryset.order_by(self.parameter_name)


class RestaurantRankingFilter(SimpleListFilter):
    title = 'Рейтинг'
    parameter_name = 'ranking'

    def lookups(self, request: WSGIRequest, model_admin: 'RestaurantAdmin') -> list[tuple]:
        return [
            ('0.0', 'Без рейтинга'),
            ('1.0-2.0', 'Менее 2'),
            ('2.0-3.0', 'От 2 до 3'),
            ('3.0-4.0', 'От 3 до 4'),
            ('4.0-5.0', 'От 4 до 5'),
            ('5.0', 'Ровно 5'),
        ]

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value():
            value = self.value().split('-')
            try:
                queryset = queryset.filter(
                    ranking__gte=value[0],
                    ranking__lte=value[1],
                )
            except IndexError:
                queryset = queryset.filter(ranking=value[0])
        return queryset.order_by(self.parameter_name)
