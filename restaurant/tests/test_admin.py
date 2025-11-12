from django.test import RequestFactory, tag, TestCase

from restaurant.admin import DishAdmin
import restaurant.models as models
import restaurant.tests.factories as factories


@tag('admin')
class TestAdmin(TestCase):
    dish_names = (
        'котлета по-киевски', 'котлеты по-киевски', 'КОТЛЕТА ПО КИЕВСКИ', 'киевская котлета',
        'котлета из Киева', 'пожарская котлета', 'котлета с сыром',
    )
    search_text = 'котлета по-киевски'

    def setUp(self) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city)

    def test_admin_search_uses_elasticsearch(self) -> None:
        for name in self.dish_names:
            factories.DishFactory.create(restaurant=models.Restaurant.objects.first(), name=name)

        request = RequestFactory().get('/admin/restaurant/dish/?q=котлета+по-киевски')
        admin = DishAdmin(models.Dish, None)
        queryset, _ = admin.get_search_results(request, models.Dish.objects.all(), self.search_text)

        self.assertEqual(queryset.count(), 4)
