from django.test import tag, TestCase

import restaurant.models as models
import restaurant.v1.serializers as serializers
import restaurant.tests.factories as factories


@tag('restaurant', 'restaurant_serializer')
class RestaurantSerializerTestCase(TestCase):
    restaurant_name = 'Лапшичная №1'
    restaurant_address = 'Набережная канала Грибоедова'

    def setUp(self) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city)

    def test_restaurant_serializer_create(self) -> None:
        restaurant = factories.RestaurantFactory.as_payload(name=self.restaurant_name, address=self.restaurant_address)
        serializer = serializers.RestaurantSerializer(data=restaurant)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        created_restaurant = serializer.save()

        self.assertIsInstance(created_restaurant, models.Restaurant)
        self.assertIsNotNone(created_restaurant.id)
        self.assertEqual(created_restaurant.name, self.restaurant_name)
        self.assertEqual(created_restaurant.address, self.restaurant_address)
        self.assertIsNotNone(created_restaurant.category)
        self.assertIsNotNone(created_restaurant.city)
        self.assertIsNotNone(created_restaurant.phone_number)
        self.assertIsNotNone(created_restaurant.restaurant_url)
        self.assertIsNotNone(created_restaurant.menu_url)
        self.assertIsNotNone(created_restaurant.ranking)
        self.assertIsNotNone(created_restaurant.comment)

    def test_restaurant_serializer_update(self) -> None:
        restaurant = models.Restaurant.objects.first()
        data = {'name': self.restaurant_name, 'address': self.restaurant_address}
        serializer = serializers.RestaurantSerializer(instance=restaurant, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_restaurant = serializer.save()

        self.assertIsInstance(updated_restaurant, models.Restaurant)
        self.assertIsNotNone(updated_restaurant.id)
        self.assertEqual(updated_restaurant.name, self.restaurant_name)
        self.assertEqual(updated_restaurant.address, self.restaurant_address)
        self.assertIsNotNone(updated_restaurant.category)
        self.assertIsNotNone(updated_restaurant.city)
        self.assertIsNotNone(updated_restaurant.phone_number)
        self.assertIsNotNone(updated_restaurant.restaurant_url)
        self.assertIsNotNone(updated_restaurant.menu_url)
        self.assertIsNotNone(updated_restaurant.ranking)
        self.assertIsNotNone(updated_restaurant.comment)


@tag('dish', 'dish_serializer')
class DishSerializerTestCase(TestCase):
    dish_name = 'Суп'

    def setUp(self) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        restaurant = factories.RestaurantFactory.create(category=category, city=city)
        tag = factories.TagFactory.create()
        dish = factories.DishFactory.create(restaurant=restaurant)
        dish.tags.add(tag)

    def test_restaurant_serializer_create(self) -> None:
        restaurant = models.Restaurant.objects.first()
        dish = factories.DishFactory.as_payload(name=self.dish_name, restaurant=restaurant)
        serializer = serializers.DishSerializer(data=dish)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        created_dish = serializer.save()

        self.assertIsInstance(created_dish, models.Dish)
        self.assertIsNotNone(created_dish.id)
        self.assertEqual(created_dish.name, self.dish_name)
        self.assertIsNotNone(created_dish.price)
        self.assertIsNotNone(created_dish.restaurant)
        self.assertIsNotNone(created_dish.weight)
        self.assertIsNotNone(created_dish.quantity)
        self.assertIsNotNone(created_dish.comment)
        self.assertTrue(created_dish.tags)

    def test_dish_serializer_update(self) -> None:
        dish = models.Dish.objects.first()
        data = {'name': self.dish_name}
        serializer = serializers.DishSerializer(instance=dish, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        updated_dish = serializer.save()

        self.assertIsInstance(updated_dish, models.Dish)
        self.assertIsNotNone(updated_dish.id)
        self.assertEqual(updated_dish.name, self.dish_name)
        self.assertIsNotNone(updated_dish.price)
        self.assertIsNotNone(updated_dish.restaurant)
        self.assertIsNotNone(updated_dish.weight)
        self.assertIsNotNone(updated_dish.quantity)
        self.assertIsNotNone(updated_dish.comment)
        self.assertTrue(updated_dish.tags)
