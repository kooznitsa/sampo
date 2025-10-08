import logging

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from restaurant.models import Restaurant
from restaurant.services import BaseCrawler
from restaurant.services.parsers import MenuParser
from restaurant.v1.serializers import DishSerializer

info_logger = logging.getLogger('info_logger')
error_logger = logging.getLogger('error_logger')


class MenuScraper(BaseCrawler):

    def __init__(self, restaurant: Restaurant) -> None:
        self.parser = MenuParser()
        self.restaurant = restaurant
        self.url = restaurant.menu_url

    def run(self) -> None:
        self._init_driver()
        info_logger.info('Driver initialized.')

        try:
            self.driver.get(self.url)
            wait = WebDriverWait(self.driver, self.timeout)
            try:
                wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Меню') or contains(@class, 'menu') or contains(@class, 'section')]"))
                )
            except Exception as e:
                error_logger.error(f'Error finding menu: {e}')

            self.parse_menu_html()

        finally:
            self.driver.quit()

    def parse_menu_html(self) -> list[dict]:
        results = []
        cards = self.driver.find_elements(By.CSS_SELECTOR, self.parser.card_item)
        info_logger.info(f'Found {len(cards)} cards via Selenium selector "{self.parser.card_item}"')

        updated_at_els = self.driver.find_elements(By.CSS_SELECTOR, self.parser.updated_at)
        updated_at = None
        if updated_at_els:
            text = updated_at_els[0].text.strip()
            updated_at = self.parser.get_updated_at(text)
        info_logger.info(f'Updated at {updated_at}')

        for card in cards:
            inner = card.get_attribute('innerHTML') or ''
            soup = BeautifulSoup(inner, 'html.parser')
            data = self._parse_card(soup)
            info_logger.info(data)
            results.append(data | {'menu_update_at': updated_at})
            # TODO: write to DB
        return results

    def _parse_card(self, soup: BeautifulSoup) -> dict:
        weight_data = self.parser.get_weight(soup)
        return {
            'name': self.parser.get_name(soup),
            'price': self.parser.get_price(soup),
            'weight': weight_data.get('value') if weight_data else None,
            'weight_unit': weight_data.get('unit') if weight_data else None,
            'quantity': self.parser.get_quantity(soup),
            'comment': self.parser.get_description(soup),
        }

    def _write_data_to_db(self, data: dict) -> None:
        menu_update_date = data.pop('menu_update_at') if 'menu_update_at' in data else None

        if name := data.get('name'):
            serializer = DishSerializer(data=data)
            if serializer.is_valid():
                try:
                    obj = serializer.save()
                    info_logger.info(f'Saved dish ID={obj.id}, name={name}, {self.restaurant=}')
                except Exception as e:
                    error_logger.error(f'Error while creating dish with {name=} and {self.restaurant=}: {e}.')
            else:
                error_logger.error(serializer.errors)

        if menu_update_date:
            self.restaurant.menu_update_date = menu_update_date
            self.restaurant.save()
