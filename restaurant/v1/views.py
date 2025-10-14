from typing import Any

from django.shortcuts import get_object_or_404

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from restaurant.filters import DishFilterSet
from restaurant.tasks import scrape_menu_task
import restaurant.v1.serializers as serializers


@extend_schema(tags=['restaurants'])
@extend_schema_view(
    list=extend_schema(description='List all restaurants'),
    retrieve=extend_schema(description='Get restaurant by ID'),
    create=extend_schema(description='Create restaurant'),
    update=extend_schema(description='Update restaurant by ID'),
    partial_update=extend_schema(description='Partially update restaurant by ID'),
    destroy=extend_schema(description='Delete restaurant by ID'),
    scrape_menu=extend_schema(description='Scrape restaurant menu'),
)
class RestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RestaurantSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.select_related('category', 'city')

    @action(detail=True, methods=['post'], url_path='scrape_menu')
    def scrape_menu(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        restaurant = get_object_or_404(self.model, pk=kwargs['pk'])
        scrape_menu_task.delay(restaurant.id)
        return Response(
            {'status': 'success', 'message': 'Menu scraping task added to queue'},
            status=status.HTTP_202_ACCEPTED,
        )


@extend_schema(tags=['dishes'])
@extend_schema_view(
    list=extend_schema(description='List all dishes'),
    retrieve=extend_schema(description='Get dish by ID'),
    create=extend_schema(description='Create dish'),
    update=extend_schema(description='Update dish by ID'),
    partial_update=extend_schema(description='Partially update dish by ID'),
    destroy=extend_schema(description='Delete dish by ID'),
)
class DishViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.DishSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.select_related('restaurant')
    filterset_class = DishFilterSet
