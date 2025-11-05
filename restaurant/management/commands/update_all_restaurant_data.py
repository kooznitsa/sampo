import argparse
import logging
import random
import time
from typing import Any

from django.core.management.base import BaseCommand

import restaurant.models as models
from restaurant.services import DriverManager, RestaurantScraper

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class Command(BaseCommand):
    help = 'Update all restaurants\' data.'

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            'without_coords_only',
            type=int,
            choices=[0, 1],
            help='If without_coords_only=1, scrape only restaurants without coordinates.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        driver_manager = DriverManager()
        driver = driver_manager.init()

        without_coords_only = options['without_coords_only']
        restaurants = (
            models.Restaurant.objects.filter(longitude__isnull=True) if without_coords_only
            else models.Restaurant.objects.select_related('category', 'city')
        )

        try:
            urls = list(restaurants.values_list('menu_url', flat=True))
            for i, url in enumerate(urls, start=1):
                try:
                    info_logger.info(f'Start scraping {i}/{len(urls)}: {url}')
                    scraper = RestaurantScraper(driver, driver_manager.timeout, url)
                    scraper.run()
                    self.stdout.write(self.style.SUCCESS(f'Restaurant data for URL {url} scraped successfully.'))
                    delay = random.uniform(2, 5)
                    info_logger.info(f'Sleeping for {delay:.2f} seconds...')
                    time.sleep(delay)
                except Exception as e:
                    error_logger.error(f'Failed to scrape restaurant data ({url}): {e}', exc_info=True)
        finally:
            driver_manager.quit()
