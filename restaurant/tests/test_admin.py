from django.test import RequestFactory, tag, TestCase

from unittest.mock import patch, MagicMock

from restaurant.admin import DishAdmin
from restaurant.elastic import DishElasticQueryManager
import restaurant.models as models
import restaurant.tests.factories as factories


@tag('admin')
class TestAdmin(TestCase):

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

    @patch.object(DishElasticQueryManager, 'perform_search')
    @patch.object(DishElasticQueryManager, 'query_multi_match')
    def test_admin_search_uses_elasticsearch(self, mock_query_multi: MagicMock, mock_perform_search: MagicMock) -> None:
        for name in self.dish_names:
            factories.DishFactory.create(restaurant=models.Restaurant.objects.first(), name=name)

        num_of_returned_objects = 4

        mock_query_multi.return_value = MagicMock(name='mocked_elastic_query')
        mock_perform_search.return_value = models.Dish.objects.all()[:num_of_returned_objects]

        request = RequestFactory().get('/admin/restaurant/dish/?q=котлета+по-киевски')
        admin = DishAdmin(models.Dish, None)
        queryset, use_distinct = admin.get_search_results(request, models.Dish.objects.all(), self.search_text)

        self.assertEqual(queryset.count(), num_of_returned_objects)
        self.assertFalse(use_distinct)
