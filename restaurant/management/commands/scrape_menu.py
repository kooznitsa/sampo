import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.models import Restaurant
from restaurant.services import MenuScraper

logger = logging.getLogger('info')


class Command(BaseCommand):
    help = 'Scrape restaurant menu.'

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            restaurant = Restaurant.objects.first()
            MenuScraper(restaurant).run()
            self.stdout.write(f'Menu of restaurant ID={restaurant.id} scraped successfully.')
        except Exception as e:
            logger.error(f'Failed to scrape restaurant menu: {e}')
