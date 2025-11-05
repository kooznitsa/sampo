from django.db import models

from geodata.enums import StationLineEnum


class City(models.Model):
    name = models.CharField(verbose_name='Название города', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self) -> str:
        return self.name


class Station(models.Model):
    name = models.CharField(verbose_name='Название станции', max_length=100, unique=True)
    line = models.CharField(verbose_name='Линия метро', choices=StationLineEnum.choices, default=StationLineEnum.L1, max_length=2)
    latitude = models.FloatField(verbose_name='Широта', null=True, blank=True)
    longitude = models.FloatField(verbose_name='Долгота', null=True, blank=True)

    class Meta:
        verbose_name = 'Станция метро'
        verbose_name_plural = 'Станции метро'

    def __str__(self) -> str:
        return self.name
