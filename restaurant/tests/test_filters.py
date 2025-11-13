import datetime
from unittest import mock

from django.test import tag, TestCase

from djmoney.money import Money

from restaurant.filters import DishFilterSet, RestaurantFilterSet
import restaurant.models as models
import restaurant.tests.factories as factories


@tag('filters', 'dish_filters')
class TestDishFilters(TestCase):

    def setUp(self) -> None:
        self.category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        menu_update_date = datetime.date(2025, 10, 1)
        self.restaurant = factories.RestaurantFactory.create(category=self.category, city=city, menu_update_date=menu_update_date)
        another_restaurant = factories.RestaurantFactory.create(category=self.category, city=city, menu_update_date=menu_update_date)

        self.dish = factories.DishFactory.create(restaurant=self.restaurant, price=Money(100, 'RUB'))
        self.batch_size = 5
        self.dishes = factories.DishFactory.create_batch(self.batch_size, restaurant=another_restaurant, price=Money(10_500, 'RUB'))
        self.queryset = models.Dish.objects.all()

    def test_filter_by_restaurant(self) -> None:
        dishes = models.Dish.objects.filter(restaurant=self.restaurant)
        excluded_dishes = models.Dish.objects.exclude(restaurant=self.restaurant)

        self.assertEqual(dishes.count(), 1)
        self.assertEqual(excluded_dishes.count(), self.batch_size)

    def test_filter_by_availability(self) -> None:
        available_dishes = models.Dish.objects.available()
        mocked_unavailable_updated_at = datetime.datetime(2025, 9, 1, tzinfo=datetime.timezone.utc)
        with mock.patch('django.utils.timezone.now', mock.Mock(return_value=mocked_unavailable_updated_at)):
            self.dish.updated_at = mocked_unavailable_updated_at
            self.dish.save(update_fields=['updated_at'])

        self.assertEqual(available_dishes.count(), self.batch_size)
        self.assertEqual(self.queryset.count() - available_dishes.count(), 1)

    def test_filter_by_price(self) -> None:
        another_filterset = DishFilterSet({'price': '10_000'}, queryset=self.queryset)
        for price in ('1-100', '100-200'):
            with self.subTest(price=price):
                filterset = DishFilterSet({'price': price}, queryset=self.queryset)

                self.assertIn(self.dish, filterset.qs)
                self.assertNotIn(self.dish, another_filterset.qs)
                self.assertEqual(filterset.qs.count(), 1)

    def test_filter_by_higher_price(self) -> None:
        filterset = DishFilterSet({'price': '10_000'}, queryset=self.queryset)

        self.assertEqual(filterset.qs.count(), self.batch_size)


@tag('filters', 'restaurant_filters')
class TestRestaurantFilters(TestCase):

    def setUp(self) -> None:
        self.category = factories.CategoryFactory.create()
        self.another_category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        self.restaurant = factories.RestaurantFactory.create(
            category=self.category, city=city, is_active=False, ranking=5.0, num_of_reviews=1000,
        )
        self.batch_size = 5
        self.restaurants = factories.RestaurantFactory.create_batch(
            self.batch_size, category=self.another_category, city=city, is_active=True, ranking=3.0,
            num_of_reviews=1,
        )
        self.queryset = models.Restaurant.objects.all()

    def test_filter_by_category(self) -> None:
        filterset = RestaurantFilterSet({'category': self.category.id}, queryset=self.queryset)
        another_filterset = RestaurantFilterSet({'category': self.another_category.id}, queryset=self.queryset)

        self.assertEqual(filterset.qs.count(), 1)
        self.assertIn(self.restaurant, filterset.qs)
        self.assertEqual(another_filterset.qs.count(), self.batch_size)
        self.assertNotIn(self.restaurant, another_filterset.qs)

    def test_filter_by_is_active(self) -> None:
        filterset = RestaurantFilterSet({'is_active': False}, queryset=self.queryset)
        another_filterset = RestaurantFilterSet({'is_active': True}, queryset=self.queryset)

        self.assertEqual(filterset.qs.count(), 1)
        self.assertIn(self.restaurant, filterset.qs)
        self.assertEqual(another_filterset.qs.count(), self.batch_size)
        self.assertNotIn(self.restaurant, another_filterset.qs)

    def test_filter_by_ranking(self) -> None:
        for ranking in ('4.0-5.0', '5.0'):
            with self.subTest(ranking=ranking):
                filterset = RestaurantFilterSet({'ranking': ranking}, queryset=self.queryset)

                self.assertEqual(filterset.qs.count(), 1)
                self.assertIn(self.restaurant, filterset.qs)

    def test_filter_by_num_of_reviews(self) -> None:
        for num_of_reviews in ('100-1000', '1000-10_000'):
            with self.subTest(num_of_reviews=num_of_reviews):
                filterset = RestaurantFilterSet({'num_of_reviews': num_of_reviews}, queryset=self.queryset)

                self.assertEqual(filterset.qs.count(), 1)
                self.assertIn(self.restaurant, filterset.qs)
