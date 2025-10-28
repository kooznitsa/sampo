from datetime import timedelta
import logging

from django.test import tag, TestCase
from django.utils import timezone

import restaurant.models as models
import restaurant.tests.factories as factories

logger = logging.getLogger('info_logger')


@tag('category', 'models', 'category_model')
class CategoryModelTestCase(TestCase):
    def setUp(self) -> None:
        factories.CategoryFactory.create()

    def test_get_category(self) -> None:
        category = models.Category.objects.first()

        self.assertIsNotNone(category)


@tag('restaurant', 'models', 'restaurant_model')
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


@tag('dish', 'models', 'dish_model')
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

    def test_get_available_dish(self) -> None:
        dish = models.Dish.objects.first()
        dish.updated_at = timezone.now()
        dish.save()
        restaurant = models.Restaurant.objects.first()
        restaurant.menu_update_date = timezone.now().date() - timedelta(days=1)
        restaurant.save()

        available_dish = models.Dish.objects.available().filter(pk=dish.pk)
        self.assertTrue(available_dish.exists())

    def test_get_unavailable_dish(self) -> None:
        dish = models.Dish.objects.first()
        dish.updated_at = timezone.now()
        dish.save()
        restaurant = models.Restaurant.objects.first()
        restaurant.menu_update_date = timezone.now().date() + timedelta(days=1)
        restaurant.save()

        available_dish = models.Dish.objects.available().filter(pk=dish.pk)
        self.assertFalse(available_dish.exists())
