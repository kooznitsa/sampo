import logging
import random
import time
from typing import Generator

from django.db import IntegrityError

from bs4 import BeautifulSoup
from bs4.element import Tag

from restaurant.services import BaseCrawler
from restaurant.services.parsers import RestaurantListParser
from restaurant.v1.serializers import RestaurantSerializer

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class LinkCollector(BaseCrawler):
    base_url = 'https://yandex.ru/maps/2/saint-petersburg/category/'
    spb_coordinates = {'lat_min': 59.8, 'lat_max': 60.1, 'lon_min': 30.1, 'lon_max': 30.5}
    categories = {'coffee_shop': 'Кофейня', 'restaurant': 'Ресторан', 'fast_food': 'Быстрое питание', 'pub': 'Бар'}

    def __init__(self) -> None:
        self.parser = RestaurantListParser()

    def run(self) -> None:
        coords = list(self._generate_coordinates())
        coords_num = len(coords)
        info_logger.info(f'Generated {coords_num} coordinates.')
        count = 0

        try:
            self._init_driver()
            info_logger.info('Driver initialized.')

            for category in self.categories.keys():
                for lon, lat in coords:
                    count += 1
                    info_logger.info(f'Started scraping data for coordinates #{count} out of {coords_num}: {lon} - {lat}.')

                    category_url = f'{self.base_url}{category}?ll={lon}%2C{lat}&z=14'
                    info_logger.info(f'Started scraping category: {category}.')
                    self.driver.get(category_url)

                    last_height = self.driver.execute_script('return document.body.scrollHeight')
                    while True:
                        self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                        time.sleep(random.uniform(2, 5))
                        new_height = self.driver.execute_script('return document.body.scrollHeight')
                        if new_height == last_height:
                            break
                        last_height = new_height

                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    cards = soup.select(self.parser.card_tag)
                    info_logger.info(f'Found {len(cards)} cards on page.')

                    for card in cards:
                        data = self._parse_card(card)
                        self._write_restaurant_data_to_db(self.categories[category], *data)

                count = 0

            self.driver.quit()

        except Exception as e:
            error_logger.error(e)

    def _parse_card(self, card: Tag) -> tuple[str | None, str | None, float, str | None]:
        name = self.parser.get_name(card)
        address = self.parser.get_address(card)
        ranking = self.parser.get_ranking(card)
        link = self.parser.get_link(card)
        info_logger.info(f'{name=}, {address=}, {ranking=}, {link=}')
        return name, address, ranking, link

    @staticmethod
    def _write_restaurant_data_to_db(category: str, name: str | None, address: str | None, ranking: float, link: str | None) -> None:
        if name and address:
            data = {
                'name': name,
                'category': category,
                'city': 'Санкт-Петербург',
                'address': address,
                'ranking': ranking,
                'menu_url': link,
            }

            serializer = RestaurantSerializer(data=data)
            if serializer.is_valid():
                try:
                    obj = serializer.save()
                    info_logger.info(f'Saved restaurant ID={obj.id}, name={obj.name}, {address=}')
                except IntegrityError:
                    error_logger.error(f'Restaurant with {name=} and {address=} already exists.')
            else:
                error_logger.error(serializer.errors)

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
