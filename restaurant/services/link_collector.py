import logging
from typing import Generator

from bs4 import BeautifulSoup
from selenium import webdriver

import restaurant.models as models
from restaurant.services import RestaurantScraper

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class LinkCollector:
    base_url = 'https://yandex.ru/maps/2/saint-petersburg/category/'
    spb_coordinates = {'lat_min': 59.8, 'lat_max': 60.1, 'lon_min': 30.1, 'lon_max': 30.5}
    categories = {
        'coffee_shop': 'Кофейня', 'restaurant': 'Ресторан', 'fast_food': 'Быстрое питание', 'pub': 'Бар',
        'confectionary': 'Кондитерская',
    }
    card_tag = 'div.search-business-snippet-view'
    zoom = 14  # 0 to 22

    def __init__(self, driver: webdriver.Remote, timeout: int) -> None:
        self.driver = driver
        self.timeout = timeout
        self.scraper = RestaurantScraper(driver, timeout)

    def run(self) -> None:
        coords = list(self._generate_coordinates())
        coords_num = len(coords)
        info_logger.info(f'Generated {coords_num} coordinates.')
        count = 0

        try:
            for category in self.categories.keys():
                for lon, lat in coords:
                    count += 1
                    info_logger.info(f'Started scraping data for coordinates #{count} out of {coords_num}: {lon} - {lat}.')

                    category_url = f'{self.base_url}{category}?ll={lon}%2C{lat}&z={self.zoom}'
                    info_logger.info(f'Started scraping category: {category}.')
                    self.driver.get(category_url)
                    self.scraper.wait()

                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    cards = soup.select(self.card_tag)
                    info_logger.info(f'Found {len(cards)} cards on page.')

                    for card in cards:
                        data = self.scraper.parse_card(card)
                        menu_url = data.get('menu_url')
                        if models.Restaurant.objects.filter(menu_url=menu_url).exists():
                            pass
                        else:
                            self.scraper.write_data_to_db(data, self.categories[category])

                count = 0

        except Exception as e:
            error_logger.error(e)

    def _generate_coordinates(self, step: float = 0.0005) -> Generator:
        """Generate Saint Petersburg coordinates.

        Args:
            step (float): The grid step that depends on the desired point density. For example:
                - step=0.01: approximately 1.1 km between points.
                - step=0.005: approximately 550 m between points.
        """
        lat_min = self.spb_coordinates['lat_min']
        lat_max = self.spb_coordinates['lat_max']
        lon_min = self.spb_coordinates['lon_min']
        lon_max = self.spb_coordinates['lon_max']

        lat = lat_min
        while lat < lat_max:
            lon = lon_min
            while lon < lon_max:
                yield lon, lat
                lon += step
            lat += step
