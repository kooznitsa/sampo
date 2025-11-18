from typing import Any

from django.db.models.query import QuerySet

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter,
    OpenApiRequest, OpenApiResponse,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from restaurant.elastic import DishElasticQueryManager
import restaurant.enums as enums
import restaurant.filters as filters
import restaurant.models as models
import restaurant.tasks as tasks
import restaurant.v1.serializers as serializers


@extend_schema(tags=['restaurants'])
@extend_schema_view(
    create=extend_schema(description='Create restaurant.'),
    destroy=extend_schema(description='Delete restaurant by ID.'),
    filter_by_category=extend_schema(description='Options to filter restaurants by category.'),
    filter_by_num_of_reviews=extend_schema(description='Options to filter restaurants by number of reviews.'),
    filter_by_ranking=extend_schema(description='Options to filter restaurants by ranking.'),
    list=extend_schema(description='List all restaurants.'),
    partial_update=extend_schema(description='Partially update restaurant by ID.'),
    retrieve=extend_schema(description='Get restaurant by ID.'),
    scrape_menu=extend_schema(
        description='Scrape restaurant menu.',
        request=OpenApiRequest(OpenApiTypes.NONE),
        responses={status.HTTP_202_ACCEPTED: OpenApiResponse(description='Menu scraping task added to queue')},
    ),
    scrape_restaurant=extend_schema(
        description='Scrape restaurant data.',
        request=OpenApiRequest(OpenApiTypes.NONE),
        responses={status.HTTP_202_ACCEPTED: OpenApiResponse(description='Restaurant scraping task added to queue')},
    ),
    update=extend_schema(description='Update restaurant by ID.'),
)
class RestaurantViewSet(viewsets.ModelViewSet):
    filterset_class = filters.RestaurantFilterSet
    model = models.Restaurant
    queryset = model.objects.select_related('category', 'city').order_by('pk')
    serializer_class = serializers.RestaurantSerializer

    def get_queryset(self) -> QuerySet:
        if self.action == 'list':
            return self.queryset.with_dishes()
        return self.queryset

    @action(detail=False, methods=['get'], url_path='filter/by_category')
    def filter_by_category(self, *args: Any, **kwargs: Any) -> Response:
        options = filters.get_filter_options(name='category', text='Категория', choices=filters.get_category_options())
        return Response({'options': options})

    @action(detail=False, methods=['get'], url_path='filter/by_num_of_reviews')
    def filter_by_num_of_reviews(self, *args: Any, **kwargs: Any) -> Response:
        options = filters.get_filter_options(name='num_of_reviews', text='Количество оценок', choices=enums.NumOfReviewsEnum.choices)
        return Response({'options': options})

    @action(detail=False, methods=['get'], url_path='filter/by_ranking')
    def filter_by_ranking(self, *args: Any, **kwargs: Any) -> Response:
        options = filters.get_filter_options(name='ranking', text='Рейтинг', choices=enums.RankingEnum.choices)
        return Response({'options': options})

    @action(detail=True, methods=['post'], url_path='scrape_menu')
    def scrape_menu(self, request: Request, pk: int) -> Response:
        restaurant = self.get_object()
        tasks.scrape_menu_task.delay(restaurant.id)
        return Response(
            data={'status': 'success', 'message': 'Menu scraping task added to queue'},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['post'], url_path='scrape_restaurant')
    def scrape_restaurant(self, request: Request, pk: int) -> Response:
        restaurant = self.get_object()
        tasks.scrape_restaurant_task.delay(restaurant.id)
        return Response(
            data={'status': 'success', 'message': 'Restaurant scraping task added to queue'},
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(tags=['dishes'])
@extend_schema_view(
    create=extend_schema(description='Create dish.'),
    destroy=extend_schema(description='Delete dish by ID.'),
    filter_by_price=extend_schema(description='Options to filter dishes by price.'),
    filter_by_station=extend_schema(description='Options to filter dishes by station.'),
    list=extend_schema(
        description='List dishes.',
        parameters=[
            OpenApiParameter(
                name='name',
                description='Filter dishes by name (word or phrase) — with similar results.',
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample('Example 1', value=''),
                    OpenApiExample('Example 2', value='суп'),
                    OpenApiExample('Example 3', value='котлета по-киевски'),
                ],
            ),
            OpenApiParameter(
                name='text',
                description='Filter dishes by text using name, comment and tags.name fields — exact match.',
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample('Example 1', value=''),
                    OpenApiExample('Example 2', value='суп'),
                    OpenApiExample('Example 3', value='котлета по-киевски'),
                ],
            ),
        ]
    ),
    partial_update=extend_schema(description='Partially update dish by ID.'),
    retrieve=extend_schema(description='Get dish by ID.'),
    update=extend_schema(description='Update dish by ID.'),
)
class DishViewSet(viewsets.ModelViewSet):
    filterset_class = filters.DishFilterSet
    model = models.Dish
    queryset = model.objects.select_related('restaurant').order_by('pk')
    serializer_class = serializers.DishSerializer

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        params = self.request.query_params
        name = params.get('name')
        text = params.get('text')

        if name and text:
            raise ValidationError({'detail': 'Please specify either the "name" or "text" parameter, but not both.'})
        if name:
            query = DishElasticQueryManager.query_match_by_name(name)
            queryset = DishElasticQueryManager().perform_search(query, name)
        if text:
            query = DishElasticQueryManager.query_multi_match(text)
            queryset = DishElasticQueryManager().perform_search(query, text)

        return queryset

    @action(detail=False, methods=['get'], url_path='filter/by_price')
    def filter_by_price(self, *args: Any, **kwargs: Any) -> Response:
        options = filters.get_filter_options(name='price', text='Цена', choices=enums.PriceEnum.choices)
        return Response({'options': options})

    @action(detail=False, methods=['get'], url_path='filter/by_station')
    def filter_by_station(self, *args: Any, **kwargs: Any) -> Response:
        options = filters.get_filter_options(
            name='station', text='Станция метро', choices=filters.get_station_options(order_by='name'),
        )
        return Response({'options': options})
