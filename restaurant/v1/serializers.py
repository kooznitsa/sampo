from decimal import Decimal
import logging
from typing import Any

from django.db import transaction

from djmoney.money import Money
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

import geodata.models as geodata_models
import restaurant.models as models

info_logger = logging.getLogger('info_logger')


class MoneyField(serializers.Field):
    def to_representation(self, value: Money) -> dict[str, str | Decimal]:
        return {'amount': value.amount, 'currency': str(value.currency)}

    def to_internal_value(self, data: dict[str, str | float]) -> Money:
        try:
            return Money(amount=data['amount'], currency=data['currency'])
        except (KeyError, TypeError):
            raise serializers.ValidationError("Price must be in format {'amount': <number>, 'currency': <str>}")


class SlugRelatedFieldWithCreate(SlugRelatedField):
    """SlugRelatedField that finds object by its slug or creates it.
    """
    def to_internal_value(self, data: Any) -> Any:
        queryset = self.get_queryset()
        obj, created = queryset.get_or_create(**{self.slug_field: str(data)})
        return obj


class RestaurantSerializer(serializers.ModelSerializer):
    category = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.Category.objects.all(), required=False)
    city = SlugRelatedFieldWithCreate(slug_field='name', queryset=geodata_models.City.objects.all())
    nearest_stations = serializers.SerializerMethodField(source='get_nearest_stations')
    ranking = serializers.FloatField(min_value=0, max_value=5)

    class Meta:
        model = models.Restaurant
        fields = (
            'id', 'name', 'category', 'city', 'address', 'phone_number', 'restaurant_url', 'menu_url', 'ranking',
            'num_of_reviews', 'longitude', 'latitude', 'comment', 'nearest_stations',
        )
        extra_kwargs: dict = {
            'menu_url': {
                'validators': [],
            }
        }

    def validate_longitude(self, value: float | None) -> float | None:
        if value and not (28 <= value <= 32):
            raise serializers.ValidationError('Longitude must be in range 28-32')
        return value

    def validate_latitude(self, value: float | None) -> float | None:
        if value and not (58 <= value <= 62):
            raise serializers.ValidationError('Latitude must be in range 58-62')
        return value

    @transaction.atomic
    def create(self, validated_data: dict) -> models.Restaurant:
        lookup = {
            'menu_url': validated_data.get('menu_url'),
        }
        restaurant, created = models.Restaurant.objects.update_or_create(defaults=validated_data, **lookup)
        return restaurant

    @transaction.atomic
    def update(self, instance: models.Restaurant, validated_data: dict) -> models.Restaurant:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def get_nearest_stations(self, instance: models.Restaurant) -> list[dict] | None:
        if stations := instance.nearest_stations:
            return [
                {
                    'name': station.name,
                    'line': station.line,
                    'distance': distance,
                } for station, distance in stations
            ]
        return None


class RestaurantShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Restaurant
        fields = ('id', 'name', 'address')


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Tag
        fields = ('id', 'name',)


class DishSerializer(serializers.ModelSerializer):
    price = MoneyField()
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=models.Restaurant.objects.only('id', 'name', 'address'),
        write_only=True,
    )
    tags = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.Tag.objects.all(), many=True, required=False)

    class Meta:
        model = models.Dish
        fields = ('id', 'name', 'price', 'restaurant', 'weight', 'weight_unit', 'quantity', 'comment', 'tags')

    def to_representation(self, instance: models.Dish) -> dict:
        rep = super().to_representation(instance)
        rep['restaurant'] = RestaurantShortSerializer(instance.restaurant, context=self.context).data
        rep['tags'] = TagSerializer(instance.tags.all(), many=True, context=self.context).data
        return rep

    def create(self, validated_data: dict) -> models.Dish:
        tags = validated_data.pop('tags', [])

        lookup = {
            'name': validated_data.get('name'),
            'restaurant': validated_data.get('restaurant'),
            'weight': validated_data.get('weight'),
        }

        dish, created = models.Dish.objects.update_or_create(defaults=validated_data, **lookup)

        if tags:
            dish.tags.set(tags)

        return dish

    def get_unique_together_validators(self) -> list:
        """Override method to disable unique together checks."""
        return []
