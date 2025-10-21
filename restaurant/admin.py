from typing import Any

from django.contrib import admin, messages
from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

import restaurant.models as models
import restaurant.tasks as tasks

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
    list_display = ('id', 'name', 'category', 'address', 'ranking', 'menu_url')
    search_fields = ('name', 'menu_url')
    search_help_text = 'Поиск по полям «Название ресторана» и «Сайт меню»'
    readonly_fields = ('menu_update_date',)

    actions = ['update_restaurant', 'update_menu']

    @admin.action(description='Обновить данные выбранных Ресторанов')
    def update_restaurant(self, request: WSGIRequest, queryset: QuerySet) -> None:
        successful_ids = []
        for restaurant in queryset:
            successful_ids.append(str(restaurant.id))
            tasks.scrape_restaurant_task.delay(restaurant.id)

        self.message_user(
            request,
            f'Рестораны поставлены в очередь для обновления данных: {", ".join(successful_ids)}',
            messages.SUCCESS,
        )

    @admin.action(description='Обновить меню выбранных Ресторанов')
    def update_menu(self, request: WSGIRequest, queryset: QuerySet) -> None:
        successful_ids = []
        for restaurant in queryset:
            successful_ids.append(str(restaurant.id))
            tasks.scrape_menu_task.delay(restaurant.id)

        self.message_user(
            request,
            f'Рестораны поставлены в очередь для обновления меню: {", ".join(successful_ids)}',
            messages.SUCCESS,
        )


@admin.register(models.Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'restaurant_link', 'weight', 'weight_unit', 'quantity')
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название блюда»'

    @admin.display(description='Ресторан')
    def restaurant_link(self, obj: models.Dish) -> Any | SafeString:
        url = reverse('admin:restaurant_restaurant_change', args=[obj.restaurant.id])
        return format_html(f'<a href="{url}">{obj.restaurant}</a>')
