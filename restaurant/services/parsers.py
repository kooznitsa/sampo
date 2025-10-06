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
