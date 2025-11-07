from typing import Any

import factory
from factory import fuzzy

from django.contrib.auth.models import User

from restaurant.enums import WeightEnum

DEFAULT_PASSWORD = 'defaultpassword'


class CategoryFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')

    class Meta:
        model = 'restaurant.Category'
        django_get_or_create = ('name',)


class CityFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')

    class Meta:
        model = 'geodata.City'
        django_get_or_create = ('name',)


class TagFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')

    class Meta:
        model = 'restaurant.Tag'
        django_get_or_create = ('name',)


class RestaurantFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)
    city = factory.SubFactory(CityFactory)
    address = factory.Faker('address')
    phone_number = factory.Faker('numerify', text='##############')
    restaurant_url = factory.Faker('url')
    menu_url = factory.Faker('url')
    ranking = fuzzy.FuzzyFloat(0.0, 5.0, precision=1)
    num_of_reviews = fuzzy.FuzzyInteger(0, 1000)
    latitude = fuzzy.FuzzyFloat(59.0, 60.0, precision=6)
    longitude = fuzzy.FuzzyFloat(30.0, 32.0, precision=6)
    comment = factory.Faker('text')
    is_active = True

    class Meta:
        model = 'restaurant.Restaurant'
        django_get_or_create = ('menu_url',)

    @classmethod
    def as_payload(cls, **kwargs: Any) -> dict[str, Any]:
        obj = cls.build(**kwargs)
        return {
            'name': obj.name,
            'category': obj.category.name,
            'city': obj.city.name,
            'address': obj.address,
            'phone_number': obj.phone_number,
            'restaurant_url': obj.restaurant_url,
            'menu_url': obj.menu_url,
            'ranking': obj.ranking,
            'num_of_reviews': obj.num_of_reviews,
            'latitude': obj.latitude,
            'longitude': obj.longitude,
            'comment': obj.comment,
            'is_active': obj.is_active,
        }


class DishFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')
    price = fuzzy.FuzzyDecimal(200.0, 5000.0, precision=2)
    restaurant = factory.SubFactory(RestaurantFactory)
    weight = fuzzy.FuzzyFloat(100.0, 1000.0, precision=1)
    weight_unit = WeightEnum.G
    quantity = fuzzy.FuzzyInteger(1, 100)
    comment = factory.Faker('text')

    class Meta:
        model = 'restaurant.Dish'
        django_get_or_create = ('name', 'restaurant', 'weight')

    @factory.post_generation
    def tags(self, create: bool, extracted: Any, **kwargs: dict[str, Any]) -> None:
        if not create:
            return
        if extracted:
            for tag in extracted:
                self.tags.add(tag)
        else:
            self.tags.add(TagFactory())

    @classmethod
    def as_payload(cls, **kwargs: Any) -> dict[str, Any]:
        obj = cls.build(**kwargs)
        tags = kwargs.pop('tags', [TagFactory()])
        return {
            'name': obj.name,
            'price': {'amount': float(obj.price.amount), 'currency': str(obj.price.currency)},
            'restaurant': obj.restaurant.id,
            'weight': obj.weight,
            'weight_unit': obj.weight_unit,
            'quantity': obj.quantity,
            'comment': obj.comment,
            'tags': [str(tag) for tag in tags],
        }


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Faker('user_name')
    email = factory.Faker('email')
    password = factory.PostGenerationMethodCall('set_password', DEFAULT_PASSWORD)

    class Meta:
        model = User
        django_get_or_create = ('username',)
