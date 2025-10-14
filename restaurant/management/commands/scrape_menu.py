import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.exceptions import MenuNotFoundException
from restaurant.models import Restaurant
from restaurant.services import DriverManager, MenuScraper

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class Command(BaseCommand):
    help = 'Scrape restaurant menus.'

    def handle(self, *args: Any, **options: Any) -> None:
        driver_manager = DriverManager()
        driver = driver_manager.init()
        info_logger.info('Driver initialized.')

        for restaurant in Restaurant.objects.order_by('pk'):
            menu_url = restaurant.menu_url
            restaurant_id = restaurant.id

            if not menu_url:
                error_logger.error(f'Failed to scrape restaurant menu ({menu_url}, ID={restaurant_id}): menu not found.')
                continue

            if not menu_url.endswith('/menu/'):
                error_logger.error(f'Failed to scrape restaurant menu ({menu_url}, ID={restaurant_id}): URL does not end with "/menu/".')
                continue

            try:
                MenuScraper(restaurant, driver, driver_manager.timeout).run()
                self.stdout.write(f'Menu of restaurant ID={restaurant_id} scraped successfully.')
            except MenuNotFoundException:
                error_logger.error(f'Failed to scrape restaurant menu ({menu_url}, ID={restaurant_id}): menu not found.')
            except Exception as e:
                error_logger.error(f'Failed to scrape restaurant menu ({menu_url}, ID={restaurant_id}): {e}')

        driver_manager.quit()
