from django.db.models.query import QuerySet

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter,
    OpenApiRequest, OpenApiResponse,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from restaurant.elastic import ElasticsearchQueryManager
from restaurant.filters import DishFilterSet
import restaurant.tasks as tasks
import restaurant.v1.serializers as serializers


@extend_schema(tags=['restaurants'])
@extend_schema_view(
    list=extend_schema(description='List all restaurants.'),
    retrieve=extend_schema(description='Get restaurant by ID.'),
    create=extend_schema(description='Create restaurant.'),
    update=extend_schema(description='Update restaurant by ID.'),
    partial_update=extend_schema(description='Partially update restaurant by ID.'),
    destroy=extend_schema(description='Delete restaurant by ID.'),
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
)
class RestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RestaurantSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.select_related('category', 'city').order_by('pk')

    def get_queryset(self) -> QuerySet:
        if self.action == 'list':
            return self.queryset.with_dishes()
        return self.queryset

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
    list=extend_schema(
        description='List dishes.',
        parameters=[
            OpenApiParameter(
                name='name',
                description='Filter dishes by name (word or phrase).',
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample('Example 1', value='суп'),
                    OpenApiExample('Example 2', value='котлета по-киевски'),
                ],
            ),
        ]
    ),
    retrieve=extend_schema(description='Get dish by ID.'),
    create=extend_schema(description='Create dish.'),
    update=extend_schema(description='Update dish by ID.'),
    partial_update=extend_schema(description='Partially update dish by ID.'),
    destroy=extend_schema(description='Delete dish by ID.'),
)
class DishViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DishSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.select_related('restaurant').order_by('pk')
    filterset_class = DishFilterSet

    def get_queryset(self) -> QuerySet:
        queryset = super().get_queryset()

        if word := self.request.query_params.get('name'):
            query = ElasticsearchQueryManager.query_dishes_containing_word(word)
            queryset = ElasticsearchQueryManager().perform_search(query, word)

        return queryset
