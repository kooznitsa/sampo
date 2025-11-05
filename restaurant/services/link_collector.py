import logging
from typing import Generator

from bs4 import BeautifulSoup
from selenium import webdriver

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

                    category_url = f'{self.base_url}{category}?ll={lon}%2C{lat}&z=14'
                    info_logger.info(f'Started scraping category: {category}.')
                    self.driver.get(category_url)
                    self.scraper.wait()

                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    cards = soup.select(self.card_tag)
                    info_logger.info(f'Found {len(cards)} cards on page.')

                    for card in cards:
                        data = self.scraper.parse_card(card)
                        self.scraper.write_data_to_db(data, self.categories[category])

                count = 0

        except Exception as e:
            error_logger.error(e)

    def _generate_coordinates(self, step: float = 0.005) -> Generator:
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
