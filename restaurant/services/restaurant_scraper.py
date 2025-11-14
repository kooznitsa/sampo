import logging
import re

from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import restaurant.models as models
from restaurant.services.parsers import RestaurantParser
from restaurant.v1.serializers import RestaurantSerializer

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class RestaurantScraper:

    def __init__(self, driver: webdriver.Remote, timeout: int, url: str | None = None) -> None:
        self.parser = RestaurantParser()
        self.driver = driver
        self.timeout = timeout
        self.url = url

    def run(self) -> None:
        if self.url:
            self.driver.get(re.sub(r'/menu/?$', '/', self.url))
            self.wait()
            try:
                if self.driver.find_elements(By.CSS_SELECTOR, self.parser.something_wrong_tag):
                    error_logger.error(f'Failed to scrape restaurant data ({self.url}): URL not found.')
                    models.Restaurant.objects.filter(menu_url=self.url).update(is_active=False)
                else:
                    card = self.driver.find_element(By.CSS_SELECTOR, self.parser.one_card_tag)
                    if outer_html := card.get_attribute('outerHTML'):
                        soup = BeautifulSoup(outer_html, 'html.parser')
                        data = self.parse_card(soup) if soup else None
                        if data:
                            self.write_data_to_db(data)
                        else:
                            error_logger.error(f'Failed to scrape restaurant data ({self.url}): No data found.')
                    else:
                        error_logger.error(f'Failed to scrape restaurant data ({self.url}): No outerHTML attribute.')
            except Exception as e:
                error_logger.error(f'Failed to scrape restaurant data ({self.url}): {e}.')

    def wait(self) -> None:
        wait = WebDriverWait(self.driver, self.timeout)
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, self.parser.one_card_tag)))
        except Exception as e:
            error_logger.error(f'Error finding restaurant elements: {e}.', exc_info=True)

    def parse_card(self, tag: Tag) -> dict:
        name = self.parser.get_name(tag)
        address = self.parser.get_address(tag)
        phone = self.parser.get_phone(tag)
        ranking = self.parser.get_ranking(tag)
        num_of_reviews = self.parser.get_num_of_reviews(tag)
        link = self.url or self.parser.get_link(tag)
        longitude, latitude = self.parser.get_coordinates(self.driver)

        info_logger.info(f'{name=}, {address=}, {phone=}, {ranking=}, {num_of_reviews=}, {link=}, {longitude=}, {latitude=}')

        return {
            'name': name,
            'city': 'Санкт-Петербург',
            'address': address,
            'phone_number': phone,
            'ranking': ranking,
            'num_of_reviews': num_of_reviews,
            'menu_url': link,
            'longitude': longitude,
            'latitude': latitude,
        }

    def write_data_to_db(self, data: dict, category: str | None = None) -> None:
        name = data.get('name')
        address = data.get('address')
        menu_url = data.get('menu_url')

        if name and address and menu_url:
            if category:
                data |= {'category': category}
            serializer = RestaurantSerializer(data=data)
            if serializer.is_valid():
                obj = serializer.save()
                info_logger.info(f'Saved restaurant ID={obj.id}, name={obj.name}, {address=}.')
                obj.save_nearest_stations()
            else:
                error_logger.error(serializer.errors)
