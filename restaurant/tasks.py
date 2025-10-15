import logging

from django.shortcuts import get_object_or_404

from celery import shared_task
from celery import Task

from restaurant.exceptions import MenuNotFoundException
from restaurant.models import Restaurant
from restaurant.services import DriverManager, MenuScraper

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def scrape_menu_task(self: Task, restaurant_id: int) -> dict | None:
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)

    driver_manager = DriverManager()
    driver = driver_manager.init()

    try:
        if not restaurant.menu_url or not restaurant.menu_url.endswith('/menu/'):
            raise MenuNotFoundException('Menu not found')
        MenuScraper(restaurant, driver, driver_manager.timeout).run()
        driver_manager.quit()
        return {'status': 'success'}
    except (MenuNotFoundException, Exception) as e:
        error_logger.error(f'Scraping menu for restaurant ID={restaurant_id} failed: {e}')
    return None
