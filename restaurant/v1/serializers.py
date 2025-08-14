from decimal import Decimal
from typing import Any, NoReturn

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import NotFound, ErrorDetail

import restaurant.models as models


class RestaurantSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    city = serializers.CharField(source='city.name')

    class Meta:
        model = models.Restaurant
        fields = ('id', 'name', 'category', 'city', 'address', 'phone_number', 'restaurant_url', 'menu_url', 'ranking')
        validators = []  # turn off UniqueTogetherValidator

    def validate_ranking(self, value) -> NoReturn | float:
        if value not in range(0, 6):
            raise serializers.ValidationError('Ranking must be between 0 and 5')
        return value

    @transaction.atomic
    def create(self, validated_data: dict[str, Any]) -> models.Restaurant:
        category_name = validated_data.pop('category').get('name')
        city_name = validated_data.pop('city').get('name')

        category, _ = models.Category.objects.get_or_create(name=category_name)
        city, _ = models.City.objects.get_or_create(name=city_name)

        restaurant, _ = models.Restaurant.objects.update_or_create(
            name=validated_data.pop('name'),
            address=validated_data.pop('address'),
            defaults={'category': category, 'city': city, **validated_data},
        )
        return restaurant

    @transaction.atomic
    def update(self, instance: models.Restaurant, validated_data: dict[str, Any]) -> models.Restaurant:
        category_name = validated_data.pop('category', {}).get('name')
        city_name = validated_data.pop('city', {}).get('name')

        if category_name:
            category, _ = models.Category.objects.get_or_create(name=category_name)
            instance.category = category

        if city_name:
            city, _ = models.City.objects.get_or_create(name=city_name)
            instance.city = city

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class RestaurantShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Restaurant
        fields = ('id', 'name', 'address')


class DishSerializer(serializers.ModelSerializer):
    restaurant = serializers.IntegerField(source='restaurant.id')
    price = serializers.SerializerMethodField(source='get_price')

    class Meta:
        model = models.Dish
        fields = ('id', 'name', 'price', 'restaurant', 'weight_grams', 'quantity')

    def get_price(self, obj: models.Dish) -> dict[str, Decimal | str]:
        return {'amount': obj.price.amount, 'currency': str(obj.price.currency)}

    def create(self, validated_data: dict[str, Any]) -> models.Dish:
        restaurant_id = validated_data.pop('restaurant').get('id')
        try:
            restaurant = models.Restaurant.objects.get(pk=restaurant_id)
        except models.Restaurant.DoesNotExist:
            raise NotFound({
                'restaurant': ErrorDetail(f'Restaurant with ID={restaurant_id} was not found.', code='not_found')
            })
        return models.Dish.objects.create(restaurant=restaurant, **validated_data)

    def update(self, instance: models.Dish, validated_data: dict[str, Any]) -> models.Dish:
        restaurant_id = validated_data.pop('restaurant', {}).get('id')

        if restaurant_id:
            if restaurant := models.Restaurant.objects.filter(pk=restaurant_id).first():
                instance.restaurant = restaurant
            else:
                raise NotFound({
                    'restaurant': ErrorDetail(f'Restaurant with ID={restaurant_id} was not found.', code='not_found')
                })

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance
