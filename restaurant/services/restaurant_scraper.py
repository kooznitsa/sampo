import logging

from bs4 import BeautifulSoup
from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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
            self.driver.get(self.url.replace('/menu/', ''))
            self.wait()
            try:
                card = self.driver.find_element(By.CSS_SELECTOR, self.parser.one_card_tag)
                if outer_html := card.get_attribute('outerHTML'):
                    soup = BeautifulSoup(outer_html, 'html.parser')
                    data = self.parse_card(soup) if soup else None
                    if data:
                        self.write_data_to_db(data)
                    else:
                        error_logger.error(f'Failed to scrape restaurant data ({self.url}): No data found')
                else:
                    error_logger.error(f'Failed to scrape restaurant data ({self.url}): No outerHTML attribute')
            except Exception as e:
                error_logger.error(f'Failed to scrape restaurant data ({self.url}): {e}')

    def wait(self) -> None:
        wait = WebDriverWait(self.driver, self.timeout)
        try:
            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(text(), 'Обзор') or contains(text(), 'Меню')]"))
            )
        except Exception as e:
            error_logger.error(f'Error finding restaurant elements: {e}')

    def parse_card(self, card: Tag) -> dict:
        name = self.parser.get_name(card)
        address = self.parser.get_address(card)
        ranking = self.parser.get_ranking(card)
        link = self.url or self.parser.get_link(card)
        info_logger.info(f'{name=}, {address=}, {ranking=}, {link=}')
        return {
            'name': name,
            'city': 'Санкт-Петербург',
            'address': address,
            'ranking': ranking,
            'menu_url': link,
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
            else:
                error_logger.error(serializer.errors)
