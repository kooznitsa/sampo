import csv
from datetime import datetime
from typing import Any

from django.contrib import admin, messages
from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Value, When
from django.db.models.query import QuerySet
from django.forms import ModelForm, TextInput
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe, SafeString

from restaurant.elastic import DishElasticQueryManager
import restaurant.filters as filters
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


@admin.register(models.Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название тега»'


class RestaurantForm(ModelForm):

    class Meta:
        model = models.Restaurant
        fields = '__all__'
        widgets = {
            'address': TextInput(attrs={'size': 80}),
        }

    def clean(self) -> None:
        cleaned_data = super().clean()
        longitude = cleaned_data.get('longitude')
        latitude = cleaned_data.get('latitude')

        if longitude and not (28 <= longitude <= 32):
            self.add_error('longitude', 'Долгота должна быть в диапазоне 28–32')

        if latitude and not (58 <= latitude <= 62):
            self.add_error('latitude', 'Широта должна быть в диапазоне 58–62')


@admin.register(models.Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    actions = ('update_restaurant', 'update_menu', 'export_csv')
    actions_on_bottom = True
    change_list_template = 'change_list.html'
    date_hierarchy = 'updated_at'
    form = RestaurantForm
    list_display = (
        'id', 'name', 'category', 'address', 'ranking', 'num_of_reviews', 'menu_url', 'has_dishes',
        'has_coords', 'menu_update_date',
    )
    list_filter = ('category', 'is_active', filters.RestaurantRankingFilter, filters.RestaurantNumOfReviewsFilter)
    list_select_related = ('category', 'city')
    readonly_fields = ('menu_update_date', 'nearest_stations')
    search_fields = ('name', 'menu_url')
    search_help_text = 'Поиск по полям «Название ресторана» и «Сайт меню»'

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        queryset = super().get_queryset(request)
        if request.resolver_match.url_name == 'restaurant_restaurant_changelist':
            queryset = queryset.annotate(
                has_dishes=Exists(models.Dish.objects.filter(restaurant=OuterRef('pk'))),
                has_coords=Case(
                    When(Q(longitude__isnull=False), then=Value(True)),
                    default=Value(False),
                    output_field=BooleanField(),
                )
            ).distinct()
        return queryset

    @admin.display(description='Есть блюда', ordering='has_dishes', boolean=True)
    def has_dishes(self, obj: models.Restaurant) -> bool:
        return getattr(obj, 'has_dishes', False)

    @admin.display(description='Есть координаты', ordering='has_coords', boolean=True)
    def has_coords(self, obj: models.Restaurant) -> bool:
        return getattr(obj, 'has_coords', False)

    @admin.display(description='Ближайшие станции')
    def nearest_stations(self, obj: models.Restaurant) -> Any | SafeString:
        if not obj.nearest_stations:
            return mark_safe('<span>Координаты ресторана не найдены.</span>')
        return format_html_join(
            sep=mark_safe('<br>'),
            format_string='<li>{} ({}) — {} км</li>',
            args_generator=((i.station.name, i.station.line, '{0:.1f}'.format(i.distance_km)) for i in obj.nearest_stations)
        )

    @admin.action(description='Обновить данные выбранных Ресторанов')
    def update_restaurant(self, request: HttpRequest, queryset: QuerySet) -> None:
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
    def update_menu(self, request: HttpRequest, queryset: QuerySet) -> None:
        successful_ids = []
        for restaurant in queryset:
            successful_ids.append(str(restaurant.id))
            tasks.scrape_menu_task.delay(restaurant.id)

        self.message_user(
            request,
            f'Рестораны поставлены в очередь для обновления меню: {", ".join(successful_ids)}',
            messages.SUCCESS,
        )

    @admin.action(description='Экспортировать в CSV')
    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=restaurants_{datetime.today()}.csv'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Название', 'Категория', 'Город', 'Адрес', 'URL', 'Рейтинг', 'Дата обновления меню'])
        for i in queryset.select_related('category', 'city'):
            writer.writerow([i.id, i.name, i.category.name, i.city.name, i.address, i.menu_url, i.ranking, i.menu_update_date])
        return response


@admin.register(models.Dish)
class DishAdmin(admin.ModelAdmin):
    actions = ('export_csv',)
    actions_on_bottom = True
    autocomplete_fields = ('restaurant',)
    list_display = ('id', 'name', 'price', 'restaurant_link', 'weight', 'weight_unit', 'quantity')
    list_filter = (filters.DishAvailableFilter, filters.DishPriceFilter, filters.DishStationFilter)
    list_select_related = ('restaurant',)
    search_fields = ('name', 'restaurant__pk')
    search_help_text = 'Поиск по полям «Название блюда» и «ID ресторана»'

    def get_search_results(self, request: HttpRequest, queryset: QuerySet, search_term: str) -> tuple[QuerySet, bool]:
        if not search_term:
            return queryset, False

        if search_term.isnumeric():
            queryset = queryset.filter(restaurant__pk=search_term)
            return queryset, False

        query = DishElasticQueryManager.query_multi_match(search_term)
        queryset = DishElasticQueryManager().perform_search(query, search_term)
        return queryset, False

    @admin.display(description='Ресторан')
    def restaurant_link(self, obj: models.Dish) -> Any | SafeString:
        url = reverse('admin:restaurant_restaurant_change', args=[obj.restaurant.id])
        return format_html(f'<a href="{url}">{obj.restaurant}</a>')

    @admin.action(description='Экспортировать в CSV')
    def export_csv(self, request: HttpRequest, queryset: QuerySet) -> HttpResponse:
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=dishes_{datetime.today()}.csv'
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Название', 'Цена, ₽', 'Название ресторана', 'Адрес ресторана', 'Вес или объём',
            'Единица измерения веса или объёма', 'Количество, шт.',
        ])
        for i in queryset.select_related('restaurant'):
            writer.writerow(
                [i.id, i.name, i.price.amount, i.restaurant.name, i.restaurant.address, i.weight, i.weight_unit, i.quantity])
        return response
