import logging
from typing import Any

from django.core.management.base import BaseCommand

from restaurant.models import Dish
from restaurant.services import DishClassifier

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class Command(BaseCommand):
    help = 'Create dish tags.'

    def handle(self, *args: Any, **options: Any) -> None:
        for dish in Dish.objects.select_related('restaurant').filter(tags__isnull=True):
            try:
                tag_names = DishClassifier(dish).classify_dish()
                dish.create_tags(tag_names)
                self.stdout.write(f'Tags for {dish} added successfully.')
            except Exception as e:
                error_logger.error(f'Error while creating dish tags: {e}', exc_info=True)
