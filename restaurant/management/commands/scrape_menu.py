import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.exceptions import MenuNotFoundException
from restaurant.models import Restaurant
from restaurant.services import MenuScraper

logger = logging.getLogger('info')


class Command(BaseCommand):
    help = 'Scrape restaurant menu.'

    def handle(self, *args: Any, **options: Any) -> None:
        restaurant = Restaurant.objects.first()
        menu_url = restaurant.menu_url

        # if not menu_url.endswith('/menu/'):
        #     logger.error(f'Failed to scrape restaurant menu: {restaurant.menu_url}')
        #     continue

        try:
            MenuScraper(restaurant).run()
            self.stdout.write(f'Menu of restaurant ID={restaurant.id} scraped successfully.')
        except MenuNotFoundException:
            logger.error(f'Failed to scrape restaurant menu: {menu_url}')
        except Exception as e:
            logger.error(f'Failed to scrape restaurant menu: {e}')
