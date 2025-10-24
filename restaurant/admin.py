from typing import Any

from django.contrib import admin, messages
from django.core.handlers.wsgi import WSGIRequest
from django.db import models as django_models
from django.db.models import Exists, OuterRef
from django.db.models.query import QuerySet
from django.forms import TextInput
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
    list_display = ('id', 'name', 'category', 'address', 'ranking', 'menu_url', 'has_dishes')
    search_fields = ('name', 'menu_url')
    search_help_text = 'Поиск по полям «Название ресторана» и «Сайт меню»'
    readonly_fields = ('menu_update_date',)
    list_filter = ('category',)
    date_hierarchy = 'updated_at'
    list_select_related = ('category', 'city')
    actions = ('update_restaurant', 'update_menu')
    actions_on_bottom = True
    formfield_overrides = {
        django_models.CharField: {'widget': TextInput(attrs={'size': 80})},
    }

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

    def get_queryset(self, request: WSGIRequest) -> QuerySet:
        queryset = super().get_queryset(request)
        if request.resolver_match.url_name == 'restaurant_restaurant_changelist':
            queryset = queryset.annotate(
                has_dishes=Exists(models.Dish.objects.filter(restaurant=OuterRef('pk'))),
            ).distinct()
        return queryset

    @admin.display(description='Есть блюда', ordering='has_dishes', boolean=True)
    def has_dishes(self, obj: models.Restaurant) -> bool:
        return getattr(obj, 'has_dishes', False)


@admin.register(models.Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'restaurant_link', 'weight', 'weight_unit', 'quantity')
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название блюда»'
    autocomplete_fields = ('restaurant',)

    @admin.display(description='Ресторан')
    def restaurant_link(self, obj: models.Dish) -> Any | SafeString:
        url = reverse('admin:restaurant_restaurant_change', args=[obj.restaurant.id])
        return format_html(f'<a href="{url}">{obj.restaurant}</a>')
