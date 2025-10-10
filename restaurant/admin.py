from typing import Any

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

import restaurant.models as models

admin.site.site_header = 'Административная панель Sampo'
admin.site.site_title = 'Административная панель Sampo'


@admin.register(models.Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название категории»'


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название города»'


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название тега»'


@admin.register(models.Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'address', 'phone_number', 'ranking')
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название ресторана»'
    readonly_fields = ('menu_update_date',)


@admin.register(models.Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'restaurant_link', 'weight', 'weight_unit', 'quantity')
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название блюда»'

    @admin.display(description='Ресторан')
    def restaurant_link(self, obj: models.Dish) -> Any | SafeString:
        url = reverse('admin:restaurant_restaurant_change', args=[obj.restaurant.id])
        return format_html(f'<a href="{url}">{obj.restaurant}</a>')
