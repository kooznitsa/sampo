import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.services import LinkCollector

logger = logging.getLogger('info')


class Command(BaseCommand):
    help = 'Collects restaurant links.'

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            LinkCollector().run()
            self.stdout.write('Restaurant links collected successfully.')
        except Exception as e:
            logger.error(f'Failed to collect restaurant links: {e}')
