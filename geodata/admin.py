from django.contrib import admin
from django.forms import ModelForm

import geodata.models as models


@admin.register(models.City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название города»'


class StationForm(ModelForm):

    class Meta:
        model = models.Station
        fields = '__all__'

    def clean(self) -> None:
        cleaned_data = super().clean()
        longitude = cleaned_data.get('longitude')
        latitude = cleaned_data.get('latitude')

        if longitude and not (28 <= longitude <= 32):
            self.add_error('longitude', 'Долгота должна быть в диапазоне 28–32')

        if latitude and not (58 <= latitude <= 62):
            self.add_error('latitude', 'Широта должна быть в диапазоне 58–62')


@admin.register(models.Station)
class StationAdmin(admin.ModelAdmin):
    form = StationForm
    list_display = ('id', 'name', 'line', 'latitude', 'longitude')
    list_filter = ('line',)
    list_editable = ('name', 'latitude', 'longitude')
    search_fields = ('name',)
    search_help_text = 'Поиск по полю «Название станции»'
