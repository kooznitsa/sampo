from decimal import Decimal
from typing import Any

from django.db import transaction

from djmoney.money import Money
from rest_framework import serializers
from rest_framework.relations import SlugRelatedField

import restaurant.models as models


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
    category = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.Category.objects.all())
    city = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.City.objects.all())
    ranking = serializers.FloatField(min_value=0, max_value=5)

    class Meta:
        model = models.Restaurant
        fields = (
            'id', 'name', 'category', 'city', 'address', 'phone_number', 'restaurant_url', 'menu_url', 'ranking',
            'comment',
        )

    @transaction.atomic
    def create(self, validated_data: dict) -> models.Restaurant:
        return models.Restaurant.objects.create(**validated_data)

    @transaction.atomic
    def update(self, instance: models.Restaurant, validated_data: dict) -> models.Restaurant:
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class RestaurantShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Restaurant
        fields = ('id', 'name', 'address')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Tag
        fields = ('id', 'name',)


class DishSerializer(serializers.ModelSerializer):
    restaurant = serializers.PrimaryKeyRelatedField(
        queryset=models.Restaurant.objects.only('id', 'name', 'address'),
        write_only=True,
    )
    price = MoneyField()
    tags = SlugRelatedFieldWithCreate(slug_field='name', queryset=models.Tag.objects.all(), many=True)

    class Meta:
        model = models.Dish
        fields = ('id', 'name', 'price', 'restaurant', 'weight_grams', 'quantity', 'comment', 'tags')

    def to_representation(self, instance: models.Dish) -> dict:
        rep = super().to_representation(instance)
        rep['restaurant'] = RestaurantShortSerializer(instance.restaurant, context=self.context).data
        rep['tags'] = TagSerializer(instance.tags.all(), many=True, context=self.context).data
        return rep
