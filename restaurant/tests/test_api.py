import logging

from django.test import tag, TestCase

from rest_framework import status
from rest_framework.test import APIClient

import geodata.models as geodata_models
import restaurant.models as models
import restaurant.tests.factories as factories
from restaurant.tests.factories import DEFAULT_PASSWORD

logger = logging.getLogger('info_logger')

BASE_URL = '/api/v1/'


class AuthenticatedAPITestCase(TestCase):
    def setUp(self) -> None:
        self.client = APIClient()
        self.user = factories.UserFactory.create()
        self.password = DEFAULT_PASSWORD
        response = self.client.post(
            f'{BASE_URL}token/',
            {'username': self.user.username, 'password': self.password},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.access_token = response.data.get('access')
        self.assertIsNotNone(self.access_token)
        self.assertIsNotNone(response.data.get('refresh'))

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')


@tag('restaurant', 'restaurant_api')
class RestaurantApiTestCase(AuthenticatedAPITestCase):
    uri = 'restaurant/'
    restaurant_name = 'Лапшичная №1'
    menu_url = 'https://yandex.ru/maps/org/nola_jazz_bar/233512176817/menu/'
    payload = factories.RestaurantFactory.as_payload(menu_url=menu_url)
    wrong_ranking = 7.0
    nonexistent_id = 123

    def setUp(self) -> None:
        super().setUp()
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        restaurant = factories.RestaurantFactory.create(category=category, city=city)
        factories.DishFactory.create(restaurant=restaurant)

    def test_get_restaurant_detail(self) -> None:
        restaurant = models.Restaurant.objects.first()
        category = models.Category.objects.first()
        city = geodata_models.City.objects.first()
        response = self.client.get(f'{BASE_URL}{self.uri}{restaurant.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('category'), str(category))
        self.assertEqual(response.data.get('city'), str(city))

    def test_get_nonexistent_restaurant_detail_fails(self) -> None:
        response = self.client.get(f'{BASE_URL}{self.uri}{self.nonexistent_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_restaurant_list(self) -> None:
        response = self.client.get(f'{BASE_URL}{self.uri}')
        results = response.data.get('results')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)

    def test_create_restaurant(self) -> None:
        response = self.client.post(f'{BASE_URL}{self.uri}', self.payload)
        created_restaurant = models.Restaurant.objects.filter(menu_url=self.menu_url).first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('menu_url'), self.menu_url)
        self.assertIsNotNone(created_restaurant)

    def test_create_not_unique_restaurant(self) -> None:
        category = models.Category.objects.first()
        city = geodata_models.City.objects.first()
        factories.RestaurantFactory.create(category=category, city=city, menu_url=self.menu_url)
        response = self.client.post(f'{BASE_URL}{self.uri}', self.payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_restaurant_with_wrong_ranking_fails(self) -> None:
        payload = self.payload | {'ranking': self.wrong_ranking}
        response = self.client.post(f'{BASE_URL}{self.uri}', payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_restaurant(self) -> None:
        restaurant = models.Restaurant.objects.first()
        payload = self.payload | {'name': self.restaurant_name}
        response = self.client.put(f'{BASE_URL}{self.uri}{restaurant.pk}/', payload)
        updated_restaurant = models.Restaurant.objects.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.restaurant_name)
        self.assertEqual(updated_restaurant.name, self.restaurant_name)

    def test_update_restaurant_with_not_unique_fields(self) -> None:
        restaurant = models.Restaurant.objects.first()
        response = self.client.put(f'{BASE_URL}{self.uri}{restaurant.pk}/', self.payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partially_update_restaurant(self) -> None:
        restaurant = models.Restaurant.objects.first()
        response = self.client.patch(f'{BASE_URL}{self.uri}{restaurant.pk}/', {'name': self.restaurant_name})
        updated_restaurant = models.Restaurant.objects.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.restaurant_name)
        self.assertEqual(updated_restaurant.name, self.restaurant_name)

    def test_partially_update_restaurant_with_not_unique_fields(self) -> None:
        restaurant = models.Restaurant.objects.first()
        response = self.client.patch(
            f'{BASE_URL}{self.uri}{restaurant.pk}/',
            {'menu_url': self.menu_url},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partially_update_restaurant_with_wrong_ranking_fails(self) -> None:
        restaurant = models.Restaurant.objects.first()
        response = self.client.patch(f'{BASE_URL}{self.uri}{restaurant.pk}/', {'ranking': 7.0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_restaurant(self) -> None:
        restaurant = models.Restaurant.objects.first()
        response = self.client.delete(f'{BASE_URL}{self.uri}{restaurant.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(models.Restaurant.objects.first())

    def test_delete_nonexistent_restaurant_fails(self) -> None:
        response = self.client.delete(f'{BASE_URL}{self.uri}{self.nonexistent_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@tag('dish', 'dish_api')
class DishApiTestCase(AuthenticatedAPITestCase):
    uri = 'dish/'
    dish_name = 'Суп'
    payload = factories.DishFactory.as_payload(name=dish_name)
    nonexistent_id = 123

    def setUp(self) -> None:
        super().setUp()
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        restaurant = factories.RestaurantFactory.create(category=category, city=city)
        self.payload |= {'restaurant': restaurant.id}
        tag = factories.TagFactory.create()
        dish = factories.DishFactory.create(restaurant=restaurant)
        dish.tags.add(tag)

    def test_get_dish_detail(self) -> None:
        dish = models.Dish.objects.first()
        restaurant = models.Restaurant.objects.first()
        response = self.client.get(f'{BASE_URL}{self.uri}{dish.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('restaurant').get('name'), str(restaurant))

    def test_get_nonexistent_dish_detail_fails(self) -> None:
        response = self.client.get(f'{BASE_URL}{self.uri}{self.nonexistent_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_dish_list(self) -> None:
        response = self.client.get(f'{BASE_URL}{self.uri}')
        results = response.data.get('results')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(results)
        self.assertEqual(len(results), 1)

    def test_create_dish(self) -> None:
        response = self.client.post(f'{BASE_URL}{self.uri}', self.payload, format='json')
        created_dish = models.Dish.objects.filter(name=self.dish_name).first()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('name'), self.dish_name)
        self.assertIsNotNone(created_dish)
        self.assertEqual(response.data.get('tags')[0].get('name'), created_dish.tags.first().name)

    def test_create_dish_with_nonexistent_restaurant_fails(self) -> None:
        payload = self.payload | {'restaurant': self.nonexistent_id}
        response = self.client.post(f'{BASE_URL}{self.uri}', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_dish(self) -> None:
        dish = models.Dish.objects.first()
        response = self.client.put(f'{BASE_URL}{self.uri}{dish.pk}/', self.payload, format='json')
        updated_dish = models.Dish.objects.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.dish_name)
        self.assertEqual(updated_dish.name, self.dish_name)

    def test_update_dish_with_not_unique_fields(self) -> None:
        dish = models.Dish.objects.first()
        response = self.client.put(
            f'{BASE_URL}{self.uri}{dish.pk}/',
            self.payload | {'restaurant': dish.restaurant.id, 'weight': dish.weight},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partially_update_dish(self) -> None:
        dish = models.Dish.objects.first()
        response = self.client.patch(f'{BASE_URL}{self.uri}{dish.pk}/', {'name': self.dish_name})
        updated_dish = models.Dish.objects.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.dish_name)
        self.assertEqual(updated_dish.name, self.dish_name)

    def test_partially_update_dish_with_not_unique_fields(self) -> None:
        dish = models.Dish.objects.first()
        response = self.client.patch(
            f'{BASE_URL}{self.uri}{dish.pk}/',
            self.payload | {'restaurant': dish.restaurant.id, 'weight': dish.weight},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dish_tags(self) -> None:
        dish = models.Dish.objects.first()
        response = self.client.put(
            f'{BASE_URL}{self.uri}{dish.pk}/',
            self.payload | {'tags': [self.dish_name]},
            format='json',
        )
        updated_dish = models.Dish.objects.first()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('name'), self.dish_name)
        self.assertEqual(updated_dish.name, self.dish_name)
        self.assertEqual(updated_dish.tags.first().name, self.dish_name)

    def test_delete_dish(self) -> None:
        dish = models.Dish.objects.first()
        response = self.client.delete(f'{BASE_URL}{self.uri}{dish.pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertIsNone(models.Dish.objects.first())

    def test_delete_nonexistent_dish_fails(self) -> None:
        response = self.client.delete(f'{BASE_URL}{self.uri}{self.nonexistent_id}/')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
