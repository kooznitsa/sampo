import factory
from factory import fuzzy

from geodata.enums import StationLineEnum


class StationFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')
    line = StationLineEnum.L1
    latitude = fuzzy.FuzzyFloat(59.0, 60.0, precision=6)
    longitude = fuzzy.FuzzyFloat(30.0, 32.0, precision=6)

    class Meta:
        model = 'geodata.Station'
        django_get_or_create = ('name',)
