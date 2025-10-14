from django.db import models

from djmoney.models.fields import MoneyField

from restaurant.enums import WeightEnum
from restaurant.mixins import DateTimeMixin


class Category(models.Model):
    name = models.CharField(verbose_name='Название категории', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self) -> str:
        return self.name


class City(models.Model):
    name = models.CharField(verbose_name='Название города', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'

    def __str__(self) -> str:
        return self.name


class Tag(models.Model):
    name = models.CharField(verbose_name='Название тега', max_length=100, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self) -> str:
        return self.name


class Restaurant(DateTimeMixin):
    name = models.CharField(verbose_name='Название ресторана', max_length=100)
    category = models.ForeignKey('Category', verbose_name='Категория', on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey('City', verbose_name='Город', on_delete=models.CASCADE)
    address = models.CharField(verbose_name='Адрес', max_length=255)
    phone_number = models.CharField(verbose_name='Номер телефона', max_length=10, null=True, blank=True)
    restaurant_url = models.URLField(verbose_name='Сайт ресторана', null=True, blank=True)
    menu_url = models.URLField(verbose_name='Сайт меню', null=True, blank=True)
    ranking = models.FloatField(verbose_name='Рейтинг', default=0.0)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)
    menu_update_date = models.DateField(verbose_name='Дата обновления меню', null=True, blank=True)

    class Meta:
        verbose_name = 'Ресторан'
        verbose_name_plural = 'Рестораны'
        unique_together = [['name', 'address']]

    def __str__(self) -> str:
        return self.name


class Dish(DateTimeMixin):
    name = models.CharField(verbose_name='Название блюда', max_length=255)
    price = MoneyField(verbose_name='Цена', max_digits=8, decimal_places=2, default_currency='RUB')
    restaurant = models.ForeignKey('Restaurant', verbose_name='Ресторан', on_delete=models.CASCADE)
    weight = models.FloatField(verbose_name='Вес или объём', null=True, blank=True)
    weight_unit = models.CharField(
        verbose_name='Единица измерения веса или объёма',
        choices=WeightEnum.choices, default=WeightEnum.G,
        max_length=2, null=True, blank=True,
    )
    quantity = models.PositiveIntegerField(verbose_name='Количество в штуках', null=True, blank=True)
    comment = models.TextField(verbose_name='Комментарий', null=True, blank=True)
    tags = models.ManyToManyField('Tag', verbose_name='Теги', related_name='dishes', blank=True)

    class Meta:
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Блюда'
        unique_together = [['name', 'restaurant']]

    def __str__(self) -> str:
        return self.name
