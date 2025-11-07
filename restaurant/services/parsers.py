from datetime import date, timedelta
from decimal import Decimal
import re

from django.utils import timezone

from bs4.element import Tag
from selenium import webdriver
from selenium.webdriver.common.by import By

from restaurant.enums import WeightEnum

SPACE = '[ \u00A0\u202F\u2009]'


class RestaurantParser:

    def __init__(self) -> None:
        self.base_url = 'https://yandex.ru'
        self.one_card_tag = 'div.business-card-view__main-wrapper'
        self.name_tag = 'div.search-business-snippet-view__title, h1.orgpage-header-view__header'
        self.address_tag = 'a.search-business-snippet-view__address, a.business-contacts-view__address-link'
        self.phone_tag = 'div.orgpage-phones-view__phone-number'
        self.ranking_tag = 'span.business-rating-badge-view__rating-text'
        self.num_of_reviews_tag = 'div.business-header-rating-view__text'
        self.link_tag = 'a[href*="/maps/org/"]'
        self.something_wrong_tag = 'div.something-wrong-view'
        self.coordinates_attr = 'data-coordinates'

    def get_name(self, tag: Tag) -> str | None:
        el = tag.select_one(self.name_tag)
        return el.get_text(strip=True) if el else None

    def get_address(self, tag: Tag) -> str | None:
        el = tag.select_one(self.address_tag)
        return el.get_text(strip=True) if el else None

    def get_phone(self, tag: Tag) -> str | None:
        el = tag.select_one(self.phone_tag)
        return el.get_text(strip=True) if el else None

    def get_ranking(self, tag: Tag) -> float:
        el = tag.select_one(self.ranking_tag)
        return float(el.get_text(strip=True).replace(',', '.')) if el else 0.0

    def get_num_of_reviews(self, tag: Tag) -> int:
        el = tag.select_one(self.num_of_reviews_tag)
        num = re.sub(r'\D', '', el.get_text(strip=True)) if el else 0
        return int(num) if num else 0

    def get_link(self, tag: Tag) -> str | None:
        el = tag.select_one(self.link_tag)
        return UrlParser().parse_url(str(el['href'])) if el else None

    def get_coordinates(self, driver: webdriver.Remote) -> tuple[float | None, float | None]:
        coords_elem = driver.find_element(By.CSS_SELECTOR, f'div[{self.coordinates_attr}]')
        if coord_str := coords_elem.get_attribute(self.coordinates_attr):
            try:
                longitude, latitude = coord_str.split(',')
                return float(longitude), float(latitude)
            except Exception:
                return None, None
        return None, None


class MenuParser:

    def __init__(self) -> None:
        self.card_item = 'div.related-item-photo-view, div.business-full-items-grouped-view__item, div.product-card'
        self.dish_name = 'div.related-item-photo-view__title, div.related-item-list-view__title'
        self.dish_price = 'span.related-product-view__price, div.related-item-list-view__price'
        self.dish_volume = 'span.related-product-view__volume, span.related-item-list-view__volume'
        self.dish_description = 'div.related-item-photo-view__description, span.related-item-list-view__description'
        self.updated_at = 'div.business-full-items-grouped-view__info'

    def get_name(self, tag: Tag) -> str | None:
        if el := tag.select_one(self.dish_name):
            return el.get_text(strip=True)
        return None

    def get_price(self, tag: Tag) -> dict | None:
        if el := tag.select_one(self.dish_price):
            text = el.get_text(strip=True)
            return PriceParser().parse_price(text)
        return None

    def get_weight(self, tag: Tag) -> dict | None:
        result = None
        if el := tag.select_one(self.dish_volume):
            text = el.get_text(strip=True)
            result = DishAmountParser().parse_weight(text)
            if not result:
                name = self.get_name(tag)
                result = DishAmountParser().parse_weight(name) if name else None
        return result

    def get_quantity(self, tag: Tag) -> int | None:
        result = None
        if el := tag.select_one(self.dish_volume):
            text = el.get_text(strip=True)
            result = DishAmountParser().parse_quantity(text)
            if not result:
                name = self.get_name(tag)
                result = DishAmountParser().parse_quantity(name) if name else None
        return result

    def get_description(self, tag: Tag) -> str | None:
        if el := tag.select_one(self.dish_description):
            return el.get_text(strip=True)
        return None

    def get_updated_at(self, text: str) -> date | None:
        return DateParser().parse_date(text)


class DateParser:
    pattern = re.compile(r"""
        (?:Обновлено|Updated:?)        # "Обновлено" (RU) or "Updated" (EN), with or without colon
        \s+                            # one or more spaces
        (                              # start of capturing group (date/word itself)
            (\d{1,2}\s+\w+)            # RU: "3 октября" (number + word)
            | (\w+\s+\d{1,2})          # EN: "October 3" (word + number)
            | (вчера|сегодня)          # RU: keywords "вчера" / "сегодня"
            | (yesterday|today)        # EN: keywords "yesterday" / "today"
        )                              # end of capturing group
    """, re.VERBOSE | re.IGNORECASE)
    months_ru = 'января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря'
    months_en = 'january|february|march|april|may|june|july|august|september|october|november|december'

    def parse_date(self, text: str) -> date | None:
        words = text.lower().split()
        if any(i in words for i in ['сегодня', 'сегодня.', 'today', 'today.']):
            return timezone.now().date()
        elif any(i in words for i in ['вчера', 'вчера.', 'yesterday', 'yesterday.']):
            return timezone.now().date() - timedelta(days=1)
        else:
            return self._dehumanize_date(text)

    def _dehumanize_date(self, text: str) -> date | None:
        if match := re.search(self.pattern, text):
            day, month = match.group(1).split()
            if not day.isnumeric():
                day, month = month, day

            try:
                month = self.months_ru.split('|').index(month.lower()) + 1
            except ValueError:
                month = self.months_en.split('|').index(month.lower()) + 1

            year = date.today().year
            result_date = date(year=year, month=month, day=int(day))

            if result_date > date.today():
                result_date = date(year=year - 1, month=month, day=int(day))

            return result_date
        return None


class PriceParser:

    def parse_price(self, text: str) -> dict | None:
        if text is None:
            return None

        pattern = re.compile(fr"""
            (?P<number>
                (\d{{1,3}}(?:,\d{{3}})+(?:\.\d+)?)       # 1,000 or 1,000.00  -> comma as thousands sep, dot as decimal
                |                                        # OR
                (\d{{1,3}}(?:{SPACE}\d{{3}})+(?:,\d+)?)  # 1 000 or 1 000,0   -> space-like as thousands sep, comma as decimal
                |                                        # OR
                (\d+(?:[.,]\d+)?)                        # 1000, 10.0, 10,0   -> plain integer or plain decimal with dot/comma
            )
            (?=
                \s*(₽|rub\.?|р\.?|руб\.?)                # currency after optional spaces
                |                                        # OR
                \s*(?!\d)                                # no more digits after optional spaces
            )
        """, re.VERBOSE | re.IGNORECASE)

        if match := re.search(pattern, text.strip()):
            amount = self._convert_price_to_decimal(match.group('number'))
            return {'amount': amount, 'currency': 'RUB'}
        return None

    @staticmethod
    def _convert_price_to_decimal(text: str | None) -> Decimal | None:
        if not text:
            return None

        # 1) Remove space-like thousands separators
        text = re.sub(SPACE, '', text)

        # 2) Handle comma vs dot
        if ',' in text and '.' in text:
            # both present -> assume commas are thousands separators (e.g. "1,000.0")
            text = text.replace(',', '')
        elif ',' in text:
            # only commas present -> decide if it's grouping (thousands) or decimal:
            # if comma is followed by groups of 3 digits (e.g. ",000" or ",000,") -> grouping
            if re.search(r',\d{3}(?:,|$)', text):
                text = text.replace(',', '')
            else:
                # otherwise treat comma as decimal separator
                text = text.replace(',', '.')

        text = text.strip()
        # final sanity check: if empty or contains invalid chars, return None
        if not re.fullmatch(r'\d+(?:\.\d+)?', text):
            return None
        return Decimal(text)


class DishAmountParser:
    weight_pattern = 'г|гр|грамм|g|кг|kg|л|l|мл|ml'
    quantity_pattern = r'шт\.?|штук|штука|pcs\.?|pc\.?'

    def parse_weight(self, text: str) -> dict | None:
        pattern = fr'(\d+(?:[.,]\d+)?)\s*({self.weight_pattern}\.?)'
        text = re.sub(fr'{SPACE}', ' ', text).strip().lower()
        match = re.search(pattern, text)
        if match:
            try:
                value = float(match.group(1).replace(',', '.'))
                return {'value': value, 'unit': self._normalize_weight_unit(match.group(2))}
            except Exception:
                return None
        return None

    @staticmethod
    def _normalize_weight_unit(unit: str) -> WeightEnum | None:
        match unit.lower().replace('.', ''):
            case 'г' | 'гр' | 'грамм' | 'g':
                return WeightEnum.G
            case 'кг' | 'kg':
                return WeightEnum.KG
            case 'л' | 'l':
                return WeightEnum.L
            case 'мл' | 'ml':
                return WeightEnum.ML
            case _:
                return None

    def parse_quantity(self, text: str) -> int | None:
        pattern = fr'(\d+(?:[.,]\d+)?)\s*({self.quantity_pattern})\b'
        text = re.sub(fr'{SPACE}', ' ', text).strip().lower()
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None


class UrlParser:

    def parse_url(self, url: str) -> str | None:
        pattern = re.compile(r'/maps/org(/[^/]+/\d+/)')
        match = pattern.search(url)
        return f'https://yandex.ru/maps/org{match.group(1)}menu/' if match else None
