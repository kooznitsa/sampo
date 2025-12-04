import datetime
from unittest.mock import patch, MagicMock

from django.contrib import admin
from django.test import RequestFactory, tag, TestCase
from django.urls import reverse

from djmoney.money import Money
from rest_framework import status

from authentication.tests.factories import DEFAULT_PASSWORD, UserFactory
from restaurant.admin import DishAdmin
from restaurant.elastic import DishElasticQueryManager
import restaurant.models as models
import restaurant.tests.factories as factories


@tag('admin', 'all_admin')
class TestAdmin(TestCase):

    def setUp(self) -> None:
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)

    def test_search_fields(self) -> None:
        for model_class, admin_class in admin.site._registry.items():
            with self.subTest(model_class._meta.model_name):
                path = reverse(f'admin:{model_class._meta.app_label}_{model_class._meta.model_name}_changelist')
                response = self.client.get(path + '?q=foo')

                self.assertEqual(response.status_code, status.HTTP_200_OK)


@tag('admin', 'dish_admin')
class TestDishSearchAdmin(TestCase):

    def setUp(self) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city)

        self.dish_names = (
            'котлета по-киевски', 'котлеты по-киевски', 'КОТЛЕТА ПО КИЕВСКИ', 'киевская котлета',
            'котлета из Киева', 'пожарская котлета', 'котлета с сыром',
        )
        self.search_text = 'котлета по-киевски'
        self.request_factory = RequestFactory()

        for name in self.dish_names:
            factories.DishFactory.create(restaurant=models.Restaurant.objects.first(), name=name)

    @patch.object(DishElasticQueryManager, 'perform_search')
    @patch.object(DishElasticQueryManager, 'query_multi_match')
    def test_admin_search_uses_elasticsearch(self, mock_query_multi: MagicMock, mock_perform_search: MagicMock) -> None:
        num_of_returned_objects = 4
        mock_query_multi.return_value = MagicMock(name='mocked_elastic_query')
        mock_perform_search.return_value = models.Dish.objects.all()[:num_of_returned_objects]

        request = self.request_factory.get('/admin/restaurant/dish/?q=котлета+по-киевски')
        admin = DishAdmin(models.Dish, None)
        queryset, use_distinct = admin.get_search_results(request, models.Dish.objects.all(), self.search_text)

        self.assertEqual(queryset.count(), num_of_returned_objects)
        self.assertFalse(use_distinct)


@tag('admin', 'dish_admin', 'dish_admin_actions')
class TestDishActionsAdmin(TestCase):

    def setUp(self) -> None:
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        self.dish = factories.DishFactory.create(name='буйабес')

    def test_delete_action(self) -> None:
        data = {'action': 'delete', '_selected_action': [self.dish.id]}
        change_url = reverse('admin:restaurant_dish_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_export_csv_action(self) -> None:
        data = {'action': 'export_csv', '_selected_action': [self.dish.id]}
        change_url = reverse('admin:restaurant_dish_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_tags_action(self) -> None:
        data = {'action': 'create_tags', '_selected_action': [self.dish.id]}
        change_url = reverse('admin:restaurant_dish_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('суп' in self.dish.tags.values_list('name', flat=True))


@tag('admin', 'dish_admin', 'dish_admin_filters')
class TestDishFiltersAdmin(TestCase):

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
        self.queryset_available = models.Dish.objects.available()
        self.request_factory = RequestFactory()
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)

    def test_availability_filter(self) -> None:
        url = reverse('admin:restaurant_dish_changelist')
        response = self.client.get(url, {'is_available': True})
        queryset = response.context['cl'].queryset

        self.assertEqual(queryset.count(), self.queryset_available.count())

    def test_price_filter(self) -> None:
        url = reverse('admin:restaurant_dish_changelist')
        response = self.client.get(url, {'price': '10_000'})
        queryset = response.context['cl'].queryset

        self.assertEqual(queryset.count(), self.batch_size)


@tag('admin', 'restaurant_admin', 'restaurant_admin_actions')
class TestRestaurantActionsAdmin(TestCase):

    def setUp(self) -> None:
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)
        self.restaurant = factories.RestaurantFactory.create()

    def test_delete_action(self) -> None:
        data = {'action': 'delete_selected', '_selected_action': [self.restaurant.id], 'post': 'yes'}
        change_url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(models.Restaurant.objects.filter(pk=self.restaurant.id).exists())

    def test_export_csv_action(self) -> None:
        data = {'action': 'export_csv', '_selected_action': [self.restaurant.id]}
        change_url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_restaurant_action(self) -> None:
        data = {'action': 'update_restaurant', '_selected_action': [self.restaurant.id]}
        change_url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_menu_action(self) -> None:
        data = {'action': 'update_menu', '_selected_action': [self.restaurant.id]}
        change_url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @tag('new')
    def test_create_stations_action(self) -> None:
        data = {'action': 'create_stations', '_selected_action': [self.restaurant.id], 'post': 'yes'}
        change_url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.post(change_url, data, follow=True)

        self.assertEqual(response.status_code, status.HTTP_200_OK)


@tag('admin', 'restaurant_admin', 'restaurant_admin_filters')
class TestRestaurantFiltersAdmin(TestCase):

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
        self.request_factory = RequestFactory()
        self.user = UserFactory.create()
        self.client.login(username=self.user.username, password=DEFAULT_PASSWORD)

    def test_category_filter(self) -> None:
        url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.get(url, {'category__id__exact': self.category.id})
        queryset = response.context['cl'].queryset

        self.assertEqual(queryset.count(), 1)

    def test_is_active_filter(self) -> None:
        url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.get(url, {'is_active__exact': True})
        queryset = response.context['cl'].queryset

        self.assertEqual(queryset.count(), self.batch_size)

    def test_ranking_filter(self) -> None:
        url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.get(url, {'ranking': '2.0-3.0'})
        queryset = response.context['cl'].queryset

        self.assertEqual(queryset.count(), self.batch_size)

    def test_num_of_reviews_filter(self) -> None:
        url = reverse('admin:restaurant_restaurant_changelist')
        response = self.client.get(url, {'num_of_reviews': '0-100'})
        queryset = response.context['cl'].queryset

        self.assertEqual(queryset.count(), self.batch_size)
