from typing import Any, TypeVar

from django.db import models as django_models, transaction

from djmoney.money import Money
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

import restaurant.models as models

_T = TypeVar('_T', bound=django_models.Model)


class MoneyField(serializers.Field):
    def to_representation(self, value: Money) -> dict[str, str | float]:
        return {'amount': value.amount, 'currency': str(value.currency)}

    def to_internal_value(self, data: dict[str, str | float]) -> Money:
        try:
            return Money(amount=data['amount'], currency=data['currency'])
        except (KeyError, TypeError):
            raise serializers.ValidationError("Price must be in format {'amount': <number>, 'currency': <str>}")


class SlugRelatedFieldWithCreate(SlugRelatedField):
    """SlugRelatedField that finds object by its slug or creates it.
    """
    def to_internal_value(self, data: Any) -> _T:
        queryset = self.get_queryset()
        obj, created = queryset.get_or_create(**{self.slug_field: str(data)})
        return obj


class RestaurantSerializer(serializers.ModelSerializer):
    category = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.Category.objects.all())
    city = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.City.objects.all())
    ranking = serializers.IntegerField(min_value=0, max_value=5)

    class Meta:
        model = models.Restaurant
        fields = ('id', 'name', 'category', 'city', 'address', 'phone_number', 'restaurant_url', 'menu_url', 'ranking')

    @transaction.atomic
    def create(self, validated_data) -> models.Restaurant:
        return models.Restaurant.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance, validated_data) -> models.Restaurant:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RestaurantShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Restaurant
        fields = ('id', 'name', 'address')


class DishSerializer(serializers.ModelSerializer):
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=models.Restaurant.objects.only('id', 'name', 'address'),
        write_only=True,
    )
    restaurant_detail = RestaurantShortSerializer(source='restaurant', read_only=True)
    price = MoneyField()

    class Meta:
        model = models.Dish
        fields = ('id', 'name', 'price', 'restaurant', 'restaurant_detail', 'weight_grams', 'quantity')
