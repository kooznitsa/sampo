import argparse
import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.services import DriverManager, RestaurantScraper

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class Command(BaseCommand):
    help = 'Scrape restaurant data.'

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            'url',
            type=str,
            help='URL of the restaurant page to scrape',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        driver_manager = DriverManager()
        driver = driver_manager.init()

        url = options['url']

        try:
            RestaurantScraper(driver, driver_manager.timeout, url).run()
            self.stdout.write(f'Restaurant data for URL {url} scraped successfully.')
        except Exception as e:
            error_logger.error(f'Failed to scrape restaurant data ({url}): {e}')
        finally:
            driver_manager.quit()
