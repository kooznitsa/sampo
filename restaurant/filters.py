import django_filters


class DishFilterSet(django_filters.FilterSet):
    restaurant = django_filters.NumberFilter(label='Restaurant ID', field_name='restaurant', lookup_expr='exact')
