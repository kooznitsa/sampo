import logging

from django.test import TestCase

import restaurant.models as models
import restaurant.tests.factories as factories

logger = logging.getLogger('info_logger')


class CategoryModelTestCase(TestCase):
    def setUp(self) -> None:
        factories.CategoryFactory.create()

    def test_get_category(self) -> None:
        category = models.Category.objects.first()

        self.assertIsNotNone(category)


class RestaurantModelTestCase(TestCase):
    def setUp(self) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city)

    def test_get_restaurant(self) -> None:
        restaurant = models.Restaurant.objects.first()
        category = models.Category.objects.first()
        city = models.City.objects.first()

        self.assertEqual(restaurant.category, category)
        self.assertEqual(restaurant.city, city)


class DishModelTestCase(TestCase):
    def setUp(self) -> None:
        restaurant = factories.RestaurantFactory.create()
        dish = factories.DishFactory.create(restaurant=restaurant)
        tags = factories.TagFactory.create_batch(3)
        dish.tags.add(*tags)

    def test_get_dish(self) -> None:
        dish = models.Dish.objects.first()
        restaurant = models.Restaurant.objects.first()

        self.assertEqual(dish.restaurant, restaurant)

    def test_get_dish_tags(self) -> None:
        tags = models.Tag.objects.all()
        dish = models.Dish.objects.first()

        self.assertEqual(tags.count(), dish.tags.count())
        self.assertEqual(set(tags), set(dish.tags.all()))
