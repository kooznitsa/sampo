import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.models import Restaurant

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class Command(BaseCommand):
    help = 'Generate and save restaurants\' nearest stations.'

    def handle(self, *args: Any, **options: Any) -> None:
        for restaurant in Restaurant.objects.select_related('category', 'city'):
            if not restaurant.nearest_stations.exists():
                try:
                    restaurant.save_nearest_stations()
                    self.stdout.write(f'Nearest stations for {restaurant} generated successfully.')
                except Exception as e:
                    error_logger.error(f'Error while generating nearest stations: {e}', exc_info=True)
