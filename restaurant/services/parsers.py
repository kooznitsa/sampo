from decimal import Decimal
import re

from bs4 import BeautifulSoup
from bs4.element import Tag


class RestaurantListParser:

    def __init__(self) -> None:
        self.base_url = 'https://yandex.ru'
        self.card_tag = 'div.search-business-snippet-view'
        self.name_tag = 'div.search-business-snippet-view__title'
        self.address_tag = 'a.search-business-snippet-view__address'
        self.ranking_tag = 'span.business-rating-badge-view__rating-text'
        self.link_tag = 'a[href*="/maps/org/"]'

    def get_name(self, card: Tag) -> str | None:
        el = card.select_one(self.name_tag)
        return el.get_text(strip=True) if el else None

    def get_address(self, card: Tag) -> str | None:
        el = card.select_one(self.address_tag)
        return el.get_text(strip=True) if el else None

    def get_ranking(self, card: Tag) -> float:
        el = card.select_one(self.ranking_tag)
        return float(el.get_text(strip=True).replace(',', '.')) if el else 0.0

    def get_link(self, card: Tag) -> str | None:
        el = card.select_one(self.link_tag)
        return f"{self.base_url}{el['href']}".replace('reviews', 'menu') if el else None


class MenuParser:

    def __init__(self) -> None:
        self.card_item = 'div.related-item-photo-view, div.business-full-items-grouped-view__item, div.product-card'
        self.dish_name = 'div.related-item-photo-view__title, div.related-item-list-view__title'
        self.dish_price = 'span.related-product-view__price, div.related-item-list-view__price'
        self.dish_volume = 'span.related-product-view__volume, span.related-item-list-view__volume'
        self.dish_description = 'div.related-item-photo-view__description, span.related-item-list-view__description'
        self.updated_at = 'div.business-full-items-grouped-view__info'

        self.space = '[\u00A0\u202F\u2009]'
        self.price_pattern = r'₽|rub\.?|р\.?|руб\.?'
        self.weight_pattern = 'г|гр|грамм|g|кг|kg|л|l|мл|ml'
        self.quantity_pattern = r'шт\.?|штук|штука|pcs\.?|pc\.?'

    def get_name(self, soup: BeautifulSoup) -> str | None:
        return self._parse_card_element(soup, self.dish_name)

    def get_price(self, soup: BeautifulSoup) -> Decimal | None:
        pattern = fr'(\d{1,3}(?:{self.space}\d{3})*(?:[.,]\d+)?|\d+)(?=\s*(?:{self.price_pattern})?)'  # noqa: E231
        result = self._parse_card_element(soup, self.dish_price, pattern)
        return Decimal(result.replace(',', '.')) if result else None

    def get_weight(self, soup: BeautifulSoup) -> dict | None:
        if el := soup.select_one(self.dish_volume):
            text = el.get_text(strip=True)
            text = re.sub(fr'{self.space}', ' ', text).strip().lower()
            pattern = fr'(\d+(?:[.,]\d+)?)\s*({self.weight_pattern}\.?)'
            match = re.search(pattern, text)
            if match:
                try:
                    value = float(match.group(1).replace(',', '.'))
                    unit = match.group(2)
                    return {'value': value, 'unit': unit}
                except Exception:
                    return None
        return None

    def get_quantity(self, soup: BeautifulSoup) -> int | None:
        pattern = fr'(\d+(?:[.,]\d+)?)\s*({self.quantity_pattern})\b'
        result = self._parse_card_element(soup, self.dish_volume, pattern)
        return int(result) if result else None

    def get_description(self, soup: BeautifulSoup) -> str | None:
        return self._parse_card_element(soup, self.dish_description)

    def get_updated_at(self, text: str) -> str | None:
        pattern = r'(?:Обновлено|Updated:?)\s+((?:\d{1,2}\s+\w+|вчера|сегодня)|(?:\w+\s+\d{1,2}|yesterday|today))'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None

    def _parse_card_element(self, soup: BeautifulSoup, tag_name: str, pattern: str | None = None) -> str | None:
        if el := soup.select_one(tag_name):
            text = el.get_text(strip=True)
            if pattern:
                text = re.sub(fr'{self.space}', ' ', text).strip().lower()
                match = re.search(pattern, text)
                return match.group(1) if match else None
            else:
                return text
        return None
