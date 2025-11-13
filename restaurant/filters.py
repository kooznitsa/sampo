from typing import NoReturn, TYPE_CHECKING

from django.contrib.admin import SimpleListFilter
from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet

import django_filters
from rest_framework.exceptions import NotFound

import restaurant.enums as enums
import restaurant.models as models

if TYPE_CHECKING:
    from restaurant.admin import DishAdmin, RestaurantAdmin


class DishFilterSet(django_filters.FilterSet):
    restaurant = django_filters.NumberFilter(method='filter_restaurant', label='Restaurant ID.')
    available_only = django_filters.NumberFilter(
        method='filter_available_only',
        label='Available only',
        help_text='0 = all dishes, 1 = only available.',
    )
    price = django_filters.ChoiceFilter(method='filter_price', label='Price (RUB).', choices=enums.PriceEnum.choices)

    class Meta:
        model = models.Dish
        fields = ['restaurant', 'available_only']

    def filter_restaurant(self, queryset: QuerySet, name: str, value: int) -> QuerySet | NoReturn:
        if not models.Restaurant.objects.filter(pk=value).exists():
            raise NotFound(detail=f'Restaurant with id={value} was not found')
        return queryset.filter(restaurant_id=value)

    def filter_available_only(self, queryset: QuerySet, name: str, value: str | int | bool) -> QuerySet:
        if value in [1, '1', True, 'true']:
            return queryset.available()
        return queryset

    def filter_price(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        value_split = value.split('-')
        try:
            queryset = queryset.filter(
                price__gte=value_split[0],
                price__lte=value_split[1],
            )
        except IndexError:
            queryset = queryset.filter(price__gte=value_split[0])
        return queryset


class RestaurantFilterSet(django_filters.FilterSet):
    ranking = django_filters.ChoiceFilter(method='filter_ranking', label='Ranking.', choices=enums.RankingEnum.choices)
    num_of_reviews = django_filters.ChoiceFilter(
        method='filter_num_of_reviews', label='Number of reviews.', choices=enums.NumOfReviewsEnum.choices,
    )
    is_active = django_filters.BooleanFilter(field_name='is_active', label='Active restaurant.')
    category = django_filters.NumberFilter(field_name='category', label='Category.')

    def filter_ranking(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        value_split = value.split('-')
        try:
            queryset = queryset.filter(
                ranking__gte=value_split[0],
                ranking__lte=value_split[1],
            )
        except IndexError:
            queryset = queryset.filter(ranking=value_split[0])
        return queryset

    def filter_num_of_reviews(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        first, second = value.split('-')
        if first and second:
            queryset = queryset.filter(num_of_reviews__gte=first, num_of_reviews__lte=second)
        if first and not second:
            queryset = queryset.filter(num_of_reviews__gte=first)
        return queryset


class DishAvailableFilter(SimpleListFilter):
    title = 'В наличии'
    parameter_name = 'is_available'

    def lookups(self, request: WSGIRequest, model_admin: 'DishAdmin') -> list[tuple]:
        return [(True, 'Да'), (False, 'Нет')]

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value() and self.value() in [1, '1', True, 'true']:
            return queryset.available()
        return queryset


class DishPriceFilter(SimpleListFilter):
    title = 'Цена'
    parameter_name = 'price'

    def lookups(self, request: WSGIRequest, model_admin: 'DishAdmin') -> list[tuple]:
        return enums.PriceEnum.choices

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
            queryset = queryset.order_by(self.parameter_name)
        return queryset


class RestaurantRankingFilter(SimpleListFilter):
    title = 'Рейтинг'
    parameter_name = 'ranking'

    def lookups(self, request: WSGIRequest, model_admin: 'RestaurantAdmin') -> list[tuple]:
        return enums.RankingEnum.choices

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
            queryset = queryset.order_by(self.parameter_name)
        return queryset


class RestaurantNumOfReviewsFilter(SimpleListFilter):
    title = 'Количество оценок'
    parameter_name = 'num_of_reviews'

    def lookups(self, request: WSGIRequest, model_admin: 'RestaurantAdmin') -> list[tuple]:
        return enums.NumOfReviewsEnum.choices

    def queryset(self, request: WSGIRequest, queryset: QuerySet) -> QuerySet:
        if self.value():
            first, second = self.value().split('-')
            if first and second:
                queryset = queryset.filter(num_of_reviews__gte=first, num_of_reviews__lte=second)
            if first and not second:
                queryset = queryset.filter(num_of_reviews__gte=first)
        return queryset.order_by(self.parameter_name)
