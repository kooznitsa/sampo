from typing import NoReturn

from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from restaurant.filters import DishFilterSet
import restaurant.v1.serializers as serializers


@extend_schema(tags=['restaurants'])
@extend_schema_view(
    list=extend_schema(description='List all restaurants'),
    retrieve=extend_schema(description='Get restaurant by ID'),
    create=extend_schema(description='Create restaurant'),
    update=extend_schema(description='Update restaurant by ID'),
    partial_update=extend_schema(description='Partially update restaurant by ID'),
    destroy=extend_schema(description='Delete restaurant by ID'),
)
class RestaurantViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.RestaurantSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.select_related('category', 'city')

    def perform_update(self, serializer: serializers.RestaurantSerializer) -> NoReturn:
        try:
            serializer.save()
        except IntegrityError as e:
            raise ValidationError({'error': str(e)})


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
