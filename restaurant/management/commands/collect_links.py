import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.services import DriverManager, LinkCollector

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class Command(BaseCommand):
    help = 'Collects restaurant links.'

    def handle(self, *args: Any, **options: Any) -> None:
        driver_manager = DriverManager()
        driver = driver_manager.init()
        info_logger.info('Driver initialized.')
        try:
            LinkCollector(driver, driver_manager.timeout).run()
            self.stdout.write('Restaurant links collected successfully.')
        except Exception as e:
            error_logger.error(f'Failed to collect restaurant links: {e}')
        finally:
            driver_manager.quit()
