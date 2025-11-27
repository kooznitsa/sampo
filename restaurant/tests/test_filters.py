import datetime
from unittest import mock

from django.test import tag, TestCase

from djmoney.money import Money

from geodata.models import Station
from geodata.tests.factories import StationFactory
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


@tag('filters', 'dish_filters', 'dish_stations_filter')
class TestDishStationsFilters(TestCase):

    def setUp(self) -> None:
        self.batch_size = 5
        self.category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()

        self.restaurant_stations = [
            {'name': 'Адмиралтейская', 'latitude': 59.935833, 'longitude': 30.315000},
            {'name': 'Невский проспект', 'latitude': 59.935000, 'longitude': 30.328333},
            {'name': 'Гостиный двор', 'latitude': 59.933611, 'longitude': 30.332778},
            {'name': 'Сенная площадь', 'latitude': 59.926944, 'longitude': 30.320278},
            {'name': 'Спасская', 'latitude': 59.926667, 'longitude': 30.319444},
        ]
        self.other_stations = [
            {'name': 'Московская', 'latitude': 59.851944, 'longitude': 30.321944},
            {'name': 'Чернышевская', 'latitude': 59.944444, 'longitude': 30.359722},
        ]
        for station in self.restaurant_stations + self.other_stations:
            StationFactory.create(name=station['name'], latitude=station['latitude'], longitude=station['longitude'])

        self.restaurant = factories.RestaurantFactory.create(
            city=city, category=self.category, latitude=59.938352, longitude=30.321111,
        )
        self.restaurant.save_nearest_stations()
        self.another_restaurant = factories.RestaurantFactory.create(
            city=city, category=self.category, latitude=59.869602, longitude=30.319100,
        )
        self.another_restaurant.save_nearest_stations()

        factories.DishFactory.create_batch(self.batch_size, restaurant=self.restaurant)
        factories.DishFactory.create_batch(self.batch_size - 1, restaurant=self.another_restaurant)
        self.queryset = models.Dish.objects.all()

    def test_filter_by_station(self) -> None:
        cases = (
            ('Адмиралтейская', self.batch_size),
            ('Московская', self.batch_size - 1),
            ('Чернышевская', 0),
        )
        for name, expected in cases:
            with self.subTest(name=name, expected=expected):
                filterset = DishFilterSet({'station': Station.objects.filter(name=name).first().id}, queryset=self.queryset)

                self.assertEqual(filterset.qs.count(), expected)


@tag('filters', 'dish_filters', 'dish_tags_filter')
class TestDishTagsFilters(TestCase):

    def setUp(self) -> None:
        dish_names = ('буйабес', 'гаспачо', 'шницель', 'лавандовый раф')
        restaurant = factories.RestaurantFactory.create(category=factories.CategoryFactory.create(), city=factories.CityFactory.create())
        self.dishes = [factories.DishFactory.create(restaurant=restaurant, name=dish_name) for dish_name in dish_names]

    def test_filter_by_tag(self) -> None:
        cases = (('суп', 2), ('мясо', 1), ('кофе', 1))
        for tag_name, expected in cases:
            with self.subTest(tag_name=tag_name, expected=expected):
                filterset = DishFilterSet({'tags': [models.Tag.objects.get(name=tag_name).id]}, queryset=models.Dish.objects.all())

                self.assertEqual(filterset.qs.count(), expected)

    def test_filter_by_multiple_tags(self) -> None:
        tags = [models.Tag.objects.get(name='мясо').id, models.Tag.objects.get(name='кофе').id]
        filterset = DishFilterSet({'tags': tags}, queryset=models.Dish.objects.all())

        self.assertEqual(filterset.qs.count(), 2)


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
