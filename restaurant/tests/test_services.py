from datetime import date, timedelta
from decimal import Decimal
import unittest
from unittest.mock import MagicMock, patch

from django.template.loader import render_to_string
from django.test import tag, TestCase
from django.utils import timezone

from bs4 import BeautifulSoup
from elasticsearch_dsl import connections

from restaurant.documents import DishDocument
from restaurant.elastic import DishElasticQueryManager
from restaurant.enums import WeightEnum
from restaurant.exceptions import MenuNotFoundException
import restaurant.models as models
import restaurant.services as services
import restaurant.services.parsers as parsers
import restaurant.tests.factories as factories


@tag('services', 'parsers')
class TestParsers(TestCase):

    def test_parse_date(self) -> None:
        year_today = timezone.now().year
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        cases = [
            ('Обновлено 3 октября.', date(year_today, 10, 3)),
            ('Обновлено 3 октября. Источник', date(year_today, 10, 3)),
            ('Обновлено сегодня.', today),
            ('Обновлено вчера.', yesterday),
            ('Updated: October 3.', date(year_today, 10, 3)),
            ('Updated today.', today),
            ('Updated yesterday.', yesterday),
            ('Обновлено 31 декабря', date(year_today - 1, 12, 31)),
        ]

        for date_string, expected in cases:
            with self.subTest(date_string=date_string, expected=expected):
                menu_update_date = parsers.DateParser().parse_date(date_string)
                self.assertEqual(menu_update_date, expected)

    def test_parse_price(self) -> None:
        decimal_10 = Decimal('10')
        decimal_1000 = Decimal('1000')
        decimal_10_000 = Decimal('10000')

        cases = [
            ('10 ₽', decimal_10),
            ('1000 ₽', decimal_1000),
            ('10 000 ₽', decimal_10_000),

            ('10₽', decimal_10),
            ('1000₽', decimal_1000),
            ('10 000₽', decimal_10_000),

            ('1 000 ₽', decimal_1000),
            ('10000 ₽', decimal_10_000),

            ('1000₽', decimal_1000),
            ('10000₽', decimal_10_000),

            ('10.0 ₽', decimal_10),
            ('1000.0 ₽', decimal_1000),
            ('10 000.0 ₽', decimal_10_000),

            ('10,0 ₽', decimal_10),
            ('1000,0 ₽', decimal_1000),
            ('10 000,0 ₽', decimal_10_000),

            ('10.0₽', decimal_10),
            ('1000.0₽', decimal_1000),
            ('10 000.0₽', decimal_10_000),

            ('10,0₽', decimal_10),
            ('1000,0₽', decimal_1000),
            ('10 000,0₽', decimal_10_000),

            ('10.0 ₽', decimal_10),
            ('1000.0 ₽', decimal_1000),

            ('1,000.0 ₽', decimal_1000),
            ('10,000.0 ₽', decimal_10_000),

            ('1,000 ₽', decimal_1000),
            ('10,000 ₽', decimal_10_000),

            ('1,000₽', decimal_1000),
            ('10,000₽', decimal_10_000),
        ]

        for price_string, expected in cases:
            with self.subTest(price_string=price_string, expected=expected):
                price = parsers.PriceParser().parse_price(price_string)
                self.assertEqual(price, {'amount': expected, 'currency': 'RUB'})

    def test_parse_weight(self) -> None:
        cases = [
            ('100 г', WeightEnum.G),
            ('100 гр', WeightEnum.G),
            ('100 грамм', WeightEnum.G),
            ('100 g', WeightEnum.G),
            ('100 кг', WeightEnum.KG),
            ('100 kg', WeightEnum.KG),
            ('100 л', WeightEnum.L),
            ('100 l', WeightEnum.L),
            ('100 мл', WeightEnum.ML),
            ('100 ml', WeightEnum.ML),

            ('100 г.', WeightEnum.G),
            ('100 гр.', WeightEnum.G),
            ('100 грамм.', WeightEnum.G),
            ('100 g.', WeightEnum.G),
            ('100 кг.', WeightEnum.KG),
            ('100 kg.', WeightEnum.KG),
            ('100 л.', WeightEnum.L),
            ('100 l.', WeightEnum.L),
            ('100 мл.', WeightEnum.ML),
            ('100 ml.', WeightEnum.ML),

            ('100г', WeightEnum.G),
            ('100гр', WeightEnum.G),
            ('100грамм', WeightEnum.G),
            ('100g', WeightEnum.G),
            ('100кг', WeightEnum.KG),
            ('100kg', WeightEnum.KG),
            ('100л', WeightEnum.L),
            ('100l', WeightEnum.L),
            ('100мл', WeightEnum.ML),
            ('100ml', WeightEnum.ML),

            ('100г.', WeightEnum.G),
            ('100гр.', WeightEnum.G),
            ('100грамм.', WeightEnum.G),
            ('100g.', WeightEnum.G),
            ('100кг.', WeightEnum.KG),
            ('100kg.', WeightEnum.KG),
            ('100л.', WeightEnum.L),
            ('100l.', WeightEnum.L),
            ('100мл.', WeightEnum.ML),
            ('100ml.', WeightEnum.ML),

            ('Дальневосточный гребешок 100 гр', WeightEnum.G),
            ('Дальневосточный гребешок 100 г', WeightEnum.G),
            ('Дальневосточный гребешок 100гр', WeightEnum.G),
            ('Дальневосточный гребешок 100г', WeightEnum.G),
            ('Дальневосточный гребешок 100 гр.', WeightEnum.G),
            ('Дальневосточный гребешок 100 г.', WeightEnum.G),
            ('Дальневосточный гребешок 100гр.', WeightEnum.G),
            ('Дальневосточный гребешок 100г.', WeightEnum.G),
        ]

        for weight_string, expected in cases:
            with self.subTest(weight_string=weight_string, expected=expected):
                price = parsers.DishAmountParser().parse_weight(weight_string)
                self.assertEqual(price, {'value': 100.0, 'unit': expected.value})

    def test_parse_quantity(self) -> None:
        cases = [
            ('1 штука', 1),
            ('100 шт', 100),
            ('100 шт.', 100),
            ('100 штук', 100),
            ('1 pcs', 1),
            ('1 pcs.', 1),
            ('1 pc', 1),
            ('1 pc.', 1),
            ('1штука', 1),
            ('100шт', 100),
            ('100шт.', 100),
            ('100штук', 100),
            ('1pcs', 1),
            ('1pcs.', 1),
            ('1pc', 1),
            ('1pc.', 1),

            ('Устрица Розовая Джоли 1 шт', 1),
            ('Устрица Розовая Джоли 1 шт.', 1),
            ('Устрица Розовая Джоли 1шт', 1),
            ('Устрица Розовая Джоли 1шт.', 1),
            ('Устрица Розовая Джоли 1штука', 1),
            ('Устрица Розовая Джоли 100 штук', 100),
            ('Устрица Розовая Джоли 1pc', 1),
            ('Устрица Розовая Джоли 1pc.', 1),
            ('Устрица Розовая Джоли 1 pc', 1),
            ('Устрица Розовая Джоли 1 pc.', 1),
            ('Устрица Розовая Джоли 100pcs', 100),
            ('Устрица Розовая Джоли 100pcs.', 100),
            ('Устрица Розовая Джоли 100 pcs', 100),
            ('Устрица Розовая Джоли 100 pcs.', 100),
        ]

        for quantity_string, expected in cases:
            with self.subTest(quantity_string=quantity_string, expected=expected):
                price = parsers.DishAmountParser().parse_quantity(quantity_string)
                self.assertEqual(price, expected)

    def test_parse_url(self) -> None:
        cases = [
            'https://yandex.ru/maps/org/microlot_coffee_to_go/168356715006/menu/',
            'https://yandex.ru/maps/org/microlot_coffee_to_go/168356715006/gallery/',
            'https://yandex.ru/maps/org/microlot_coffee_to_go/168356715006/',
            'https://yandex.ru/maps/org/microlot_coffee_to_go/168356715006/reviews/',
        ]
        expected = 'https://yandex.ru/maps/org/microlot_coffee_to_go/168356715006/menu/'

        for url_string in cases:
            with self.subTest(url_string=url_string):
                price = parsers.UrlParser().parse_url(url_string)
                self.assertEqual(price, expected)


@tag('services', 'scrapers', 'restaurant_scraper')
class TestRestaurantScraper(unittest.TestCase):
    restaurant_data = {
        'name': 'Nola Jazz Bar',
        'city': 'Санкт-Петербург',
        'address': 'Волынский пер., 2, Санкт-Петербург',
        'phone_number': '+7 (981) 916-79-33',
        'ranking': 5.0,
        'num_of_reviews': 894,
        'latitude': 59.938352,
        'longitude': 30.321111,
        'menu_url': 'https://yandex.ru/maps/org/nola_jazz_bar/233512176817/menu/',
    }
    category = 'Ресторан'
    timeout = 5
    template = 'yandex/restaurant_card.html'
    template_list = 'yandex/restaurant_card_from_list.html'
    template_something_wrong = 'yandex/something_wrong.html'

    @patch('restaurant.services.restaurant_scraper.BeautifulSoup')
    @patch.object(services.RestaurantScraper, 'write_data_to_db')
    @patch.object(services.RestaurantScraper, 'parse_card')
    def test_calls_parser_and_writer(self, mock_parse: MagicMock, mock_write_db: MagicMock, mock_soup: MagicMock) -> None:
        mock_driver = MagicMock()
        mock_card = MagicMock()
        mock_card.get_attribute.return_value = '<div>OK</div>'
        mock_driver.find_elements.return_value = None
        mock_driver.find_element.return_value = mock_card

        scraper = services.RestaurantScraper(driver=mock_driver, timeout=self.timeout, url=str(self.restaurant_data['menu_url']))
        mock_parse.return_value = self.restaurant_data

        scraper.run()

        mock_driver.get.assert_called_once_with('https://yandex.ru/maps/org/nola_jazz_bar/233512176817/')
        mock_parse.assert_called_once()
        mock_write_db.assert_called_once_with(mock_parse.return_value)

    @patch('restaurant.services.restaurant_scraper.error_logger')
    def test_run_logs_error_when_no_outer_html(self, mock_logger: MagicMock) -> None:
        mock_driver = MagicMock()
        mock_card = MagicMock()
        mock_card.get_attribute.return_value = None
        mock_driver.find_elements.return_value = None
        mock_driver.find_element.return_value = mock_card

        scraper = services.RestaurantScraper(driver=mock_driver, timeout=self.timeout, url=str(self.restaurant_data['menu_url']))
        scraper.run()

        mock_logger.error.assert_any_call(
            f'Failed to scrape restaurant data ({self.restaurant_data["menu_url"]}): No outerHTML attribute.'
        )

    @patch('restaurant.services.restaurant_scraper.WebDriverWait')
    def test_wait_uses_webdriver_wait(self, mock_wait: MagicMock) -> None:
        mock_driver = MagicMock()
        scraper = services.RestaurantScraper(driver=mock_driver, timeout=self.timeout)
        scraper.wait()

        mock_wait.assert_called_once_with(mock_driver, self.timeout)
        mock_wait.return_value.until.assert_called_once()

    @patch('restaurant.services.restaurant_scraper.RestaurantParser')
    def test_parse_card_returns_expected_dict(self, mock_parser: MagicMock) -> None:
        mp = mock_parser.return_value
        mp.get_name.return_value = self.restaurant_data['name']
        mp.get_address.return_value = self.restaurant_data['address']
        mp.get_phone.return_value = self.restaurant_data['phone_number']
        mp.get_ranking.return_value = self.restaurant_data['ranking']
        mp.get_num_of_reviews.return_value = self.restaurant_data['num_of_reviews']
        mp.get_coordinates.return_value = self.restaurant_data['longitude'], self.restaurant_data['latitude']
        mp.get_link.return_value = self.restaurant_data['menu_url']

        scraper = services.RestaurantScraper(driver=MagicMock(), timeout=self.timeout, url=str(self.restaurant_data['menu_url']))
        for template in (self.template, self.template_list):
            with self.subTest(template=template):
                html = render_to_string(self.template, context=self.restaurant_data)
                soup = BeautifulSoup(html, 'html.parser')
                result = scraper.parse_card(soup)

                self.assertEqual(result, self.restaurant_data)

                mp.get_name.assert_called_once_with(soup)
                mp.get_address.assert_called_once_with(soup)
                mp.get_phone.assert_called_once_with(soup)
                mp.get_ranking.assert_called_once_with(soup)
                mp.get_num_of_reviews.assert_called_once_with(soup)
                mp.reset_mock()

    @patch('restaurant.services.restaurant_scraper.error_logger')
    @patch('restaurant.services.restaurant_scraper.info_logger')
    @patch('restaurant.services.restaurant_scraper.RestaurantSerializer')
    def test_write_data_to_db_parameterized(
            self,
            mock_serializer_cls: MagicMock,
            mock_info_logger: MagicMock,
            mock_error_logger: MagicMock,
    ) -> None:
        scraper = services.RestaurantScraper(driver=MagicMock(), timeout=self.timeout)
        mock_serializer = mock_serializer_cls.return_value

        test_cases = [
            {
                'name': 'валидные данные',
                'data': self.restaurant_data.copy(),
                'is_valid': True,
                'expected_info': True,
                'expected_error': False,
                'expected_save': True,
            },
            {
                'name': 'невалидный сериализатор',
                'data': self.restaurant_data.copy(),
                'is_valid': False,
                'expected_info': False,
                'expected_error': True,
                'expected_save': False,
            },
            {
                'name': 'отсутствует name',
                'data': self.restaurant_data | {'name': None},
                'is_valid': True,
                'expected_info': False,
                'expected_error': False,
                'expected_save': False,
            },
        ]

        for case in test_cases:
            with self.subTest(case=case['name']):
                mock_serializer_cls.reset_mock()
                mock_info_logger.reset_mock()
                mock_error_logger.reset_mock()

                mock_serializer.is_valid.return_value = case['is_valid']
                mock_serializer.errors = {'name': ['Required field']}
                mock_serializer.save.return_value.id = 1
                mock_serializer.save.return_value.name = case['data'].get('name')  # type: ignore[attr-defined]

                scraper.write_data_to_db(case['data'])  # type: ignore[arg-type]

                if case['data'].get('name') and case['data'].get('address') and case['data'].get('menu_url'):  # type: ignore[attr-defined]
                    mock_serializer_cls.assert_called_once_with(data=case['data'])
                    mock_serializer.is_valid.assert_called_once()
                else:
                    mock_serializer_cls.assert_not_called()

                if case['expected_info']:
                    mock_info_logger.info.assert_called()
                else:
                    mock_info_logger.info.assert_not_called()

                if case['expected_error']:
                    mock_error_logger.error.assert_called_once_with({'name': ['Required field']})
                else:
                    mock_error_logger.error.assert_not_called()

                if case['expected_save']:
                    mock_serializer.save.assert_called_once()
                else:
                    mock_serializer.save.assert_not_called()

    @patch('restaurant.services.restaurant_scraper.error_logger')
    def test_run_logs_exception_on_selenium_error(self, mock_logger: MagicMock) -> None:
        mock_driver = MagicMock()
        mock_driver.find_elements.return_value = None
        mock_driver.find_element.side_effect = Exception('Element not found')

        scraper = services.RestaurantScraper(driver=mock_driver, timeout=self.timeout, url=str(self.restaurant_data['menu_url']))
        scraper.run()

        mock_logger.error.assert_called()
        assert 'Element not found' in mock_logger.error.call_args[0][0]

    @patch('restaurant.services.restaurant_scraper.info_logger')
    @patch('restaurant.services.restaurant_scraper.RestaurantParser')
    def test_parse_card_logs_info(self, mock_parser: MagicMock, mock_logger: MagicMock) -> None:
        mp = mock_parser.return_value
        mp.get_name.return_value = self.restaurant_data['name']
        mp.get_address.return_value = self.restaurant_data['address']
        mp.get_phone.return_value = self.restaurant_data['phone_number']
        mp.get_ranking.return_value = self.restaurant_data['ranking']
        mp.get_num_of_reviews.return_value = self.restaurant_data['num_of_reviews']
        mp.get_coordinates.return_value = self.restaurant_data['longitude'], self.restaurant_data['latitude']
        mp.get_link.return_value = self.restaurant_data['menu_url']

        scraper = services.RestaurantScraper(driver=MagicMock(), timeout=self.timeout, url=str(self.restaurant_data['menu_url']))
        soup = BeautifulSoup('<div></div>', 'html.parser')
        scraper.parse_card(soup)

        mock_logger.info.assert_called_once()

    @patch('restaurant.services.restaurant_scraper.BeautifulSoup')
    @patch.object(services.RestaurantScraper, 'write_data_to_db')
    @patch.object(services.RestaurantScraper, 'parse_card')
    def test_parse_something_wrong_page(self, mock_parse: MagicMock, mock_write_db: MagicMock, mock_soup: MagicMock) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city, menu_url=self.restaurant_data['menu_url'])

        mock_driver = MagicMock()
        mock_card = MagicMock()
        mock_card.get_attribute.return_value = render_to_string(self.template_something_wrong)
        mock_driver.find_elements.return_value = '<div>Something wrong</div>'
        mock_driver.find_element.return_value = mock_card

        scraper = services.RestaurantScraper(driver=mock_driver, timeout=self.timeout, url=str(self.restaurant_data['menu_url']))
        scraper.run()

        mock_driver.get.assert_called_once_with('https://yandex.ru/maps/org/nola_jazz_bar/233512176817/')
        mock_parse.assert_not_called()
        mock_write_db.assert_not_called()

        updated_restaurant = models.Restaurant.objects.filter(menu_url=self.restaurant_data['menu_url']).first()
        self.assertEqual(updated_restaurant.is_active, False)


@tag('services', 'scrapers', 'menu_scraper')
class TestMenuScraper(unittest.TestCase):
    menu_data = {
        'name': 'Буйабес 1 шт.',
        'price': 890.0,
        'weight': 450.0,
        'weight_unit': 'г',
        'quantity': 1,
        'comment': 'марсельская уха с треской, креветкой, мидиями и соусом Руй на крутонах',
    }
    menu_url = 'https://yandex.ru/maps/org/nola_jazz_bar/233512176817/menu/'
    timeout = 5
    template = 'yandex/dish_card.html'
    template_list = 'yandex/restaurant_card_from_list.html'

    def setUp(self) -> None:
        super().setUp()
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city, menu_url=self.menu_url)
        self.restaurant = models.Restaurant.objects.filter(menu_url=self.menu_url).first()

    @patch('restaurant.services.restaurant_scraper.BeautifulSoup')
    @patch.object(services.MenuScraper, 'write_data_to_db')
    @patch.object(services.MenuScraper, 'parse_card')
    def test_calls_parser_and_writer(self, mock_parse: MagicMock, mock_write_db: MagicMock, mock_soup: MagicMock) -> None:
        mock_driver = MagicMock()
        mock_card = MagicMock()
        mock_card.get_attribute.return_value = '<div>OK</div>'
        mock_card.text = 'Обновлено 5 октября 2025'
        mock_driver.find_elements.return_value = [mock_card]

        scraper = services.MenuScraper(restaurant=self.restaurant, driver=mock_driver, timeout=self.timeout)
        mock_parse.return_value = self.menu_data.copy()

        scraper.run()

        mock_driver.get.assert_called_once_with(self.restaurant.menu_url)
        mock_parse.assert_called_once()
        mock_write_db.assert_called_once_with(mock_parse.return_value)

    @patch('restaurant.services.menu_scraper.MenuParser')
    def test_parse_card_returns_expected_dict(self, mock_parser: MagicMock) -> None:
        mp = mock_parser.return_value
        mp.get_name.return_value = self.menu_data['name']
        mp.get_price.return_value = self.menu_data['price']
        mp.get_weight.return_value = {'value': self.menu_data['weight'], 'unit': self.menu_data['weight_unit']}
        mp.get_quantity.return_value = self.menu_data['quantity']
        mp.get_description.return_value = self.menu_data['comment']

        scraper = services.MenuScraper(restaurant=self.restaurant, driver=MagicMock(), timeout=self.timeout)
        html = render_to_string(self.template, context=self.menu_data)
        soup = BeautifulSoup(html, 'html.parser')
        result = scraper.parse_card(soup)

        self.assertEqual(result, self.menu_data)

        mp.get_name.assert_called_once_with(soup)
        mp.get_price.assert_called_once_with(soup)
        mp.get_weight.assert_called_once_with(soup)
        mp.get_quantity.assert_called_once_with(soup)
        mp.get_description.assert_called_once_with(soup)

    @patch('restaurant.services.menu_scraper.error_logger')
    @patch('restaurant.services.menu_scraper.info_logger')
    @patch('restaurant.services.menu_scraper.DishSerializer')
    def test_write_data_to_db_parameterized(
            self,
            mock_serializer_cls: MagicMock,
            mock_info_logger: MagicMock,
            mock_error_logger: MagicMock,
    ) -> None:
        scraper = services.MenuScraper(restaurant=self.restaurant, driver=MagicMock(), timeout=self.timeout)
        mock_serializer = mock_serializer_cls.return_value

        test_cases = [
            {
                'name': 'валидные данные',
                'data': self.menu_data.copy(),
                'is_valid': True,
                'expected_info': True,
                'expected_error': False,
                'expected_save': True,
            },
            {
                'name': 'невалидный сериализатор',
                'data': self.menu_data.copy(),
                'is_valid': False,
                'expected_info': False,
                'expected_error': True,
                'expected_save': False,
            },
            {
                'name': 'отсутствует name',
                'data': self.menu_data | {'name': None},
                'is_valid': True,
                'expected_info': False,
                'expected_error': False,
                'expected_save': False,
            },
        ]

        for case in test_cases:
            with self.subTest(case=case['name']):
                mock_serializer_cls.reset_mock()
                mock_info_logger.reset_mock()
                mock_error_logger.reset_mock()

                mock_serializer.is_valid.return_value = case['is_valid']
                mock_serializer.errors = {'name': ['Required field']}
                mock_serializer.save.return_value.id = 1
                mock_serializer.save.return_value.name = case['data'].get('name')  # type: ignore[attr-defined]

                scraper.write_data_to_db(case['data'])

                if case['data'].get('name'):  # type: ignore[attr-defined]
                    mock_serializer_cls.assert_called_once_with(data=case['data'])
                    mock_serializer.is_valid.assert_called_once()
                else:
                    mock_serializer_cls.assert_not_called()

                if case['expected_info']:
                    mock_info_logger.info.assert_called()
                else:
                    mock_info_logger.info.assert_not_called()

                if case['expected_error']:
                    mock_error_logger.error.assert_called_once_with({'name': ['Required field']})
                else:
                    mock_error_logger.error.assert_not_called()

                if case['expected_save']:
                    mock_serializer.save.assert_called_once()
                else:
                    mock_serializer.save.assert_not_called()

    @patch('restaurant.services.menu_scraper.error_logger')
    def test_run_logs_exception_on_selenium_error(self, mock_logger: MagicMock) -> None:
        mock_driver = MagicMock()
        mock_driver.find_element.side_effect = MenuNotFoundException(f'Menu not found for URL {self.restaurant.menu_url}')

        scraper = services.MenuScraper(restaurant=self.restaurant, driver=mock_driver, timeout=self.timeout)
        scraper.run()

        mock_logger.error.assert_called()
        assert f'Menu not found for URL {self.restaurant.menu_url}' in mock_logger.error.call_args[0][0]

    @patch('restaurant.services.menu_scraper.info_logger')
    @patch('restaurant.services.menu_scraper.MenuParser')
    def test_parse_card_logs_info(self, mock_parser: MagicMock, mock_logger: MagicMock) -> None:
        mp = mock_parser.return_value
        mp.get_name.return_value = self.menu_data['name']
        mp.get_price.return_value = self.menu_data['price']
        mp.get_weight.return_value = {'value': self.menu_data['weight'], 'amount': self.menu_data['weight_unit']}
        mp.get_quantity.return_value = self.menu_data['quantity']

        scraper = services.MenuScraper(restaurant=self.restaurant, driver=MagicMock(), timeout=self.timeout)
        soup = BeautifulSoup('<div></div>', 'html.parser')
        scraper.parse_card(soup)

        mock_logger.info.assert_called_once()


@tag('services', 'scrapers', 'link_collector')
class TestLinkCollector(unittest.TestCase):
    restaurant_data = {
        'name': 'Nola Jazz Bar',
        'city': 'Санкт-Петербург',
        'address': 'Волынский пер., 2, Санкт-Петербург',
        'phone_number': '+7 (981) 916-79-33',
        'ranking': 5.0,
        'num_of_reviews': 894,
        'latitude': 59.938352,
        'longitude': 30.321111,
        'menu_url': 'https://yandex.ru/maps/org/nola_jazz_bar/233512176817/menu/',
    }
    timeout = 5

    @patch('restaurant.services.link_collector.BeautifulSoup')
    @patch.object(services.RestaurantScraper, 'write_data_to_db')
    @patch.object(services.RestaurantScraper, 'parse_card')
    def test_calls_scraper(self, mock_parse: MagicMock, mock_write_db: MagicMock, mock_soup_cls: MagicMock) -> None:
        mock_driver = MagicMock()
        mock_driver.page_source = '<html></html>'

        mock_soup = MagicMock()
        mock_card = MagicMock()
        mock_soup.select.return_value = [mock_card]
        mock_soup_cls.return_value = mock_soup

        mock_parse.return_value = self.restaurant_data

        link_collector = services.LinkCollector(driver=mock_driver, timeout=self.timeout)
        link_collector.categories = {'restaurant': 'Ресторан'}

        with patch.object(link_collector, '_generate_coordinates', return_value=[(30.3, 59.9)]):
            link_collector.run()

        mock_driver.get.assert_called_once()
        mock_parse.assert_called_once_with(mock_card)
        mock_write_db.assert_called_once_with(mock_parse.return_value, 'Ресторан')


@tag('services', 'elasticsearch', 'elasticsearch_dish')
class TestElasticsearchDish(TestCase):
    dish_names = (
        'котлета по-киевски', 'котлеты по-киевски', 'КОТЛЕТА ПО КИЕВСКИ', 'киевская котлета',
        'котлета из Киева', 'пожарская котлета', 'котлета с сыром',
    )
    search_text = 'котлета по-киевски'

    def setUp(self) -> None:
        category = factories.CategoryFactory.create()
        city = factories.CityFactory.create()
        factories.RestaurantFactory.create(category=category, city=city)

    def test_search_by_name_returns_all_dishes(self) -> None:
        for name in self.dish_names:
            factories.DishFactory.create(restaurant=models.Restaurant.objects.first(), name=name)

        query = DishElasticQueryManager.query_match_by_name(self.search_text)
        queryset = DishElasticQueryManager().perform_search(query, self.search_text)

        self.assertEqual(queryset.count(), len(self.dish_names))

    def test_search_by_multiple_fields_returns_exact_matches(self) -> None:
        restaurant = models.Restaurant.objects.first()
        tag_name, comment, *names = self.dish_names
        tag_obj = factories.TagFactory.create(name=tag_name)
        dish = factories.DishFactory.create(restaurant=restaurant)
        dish.tags.add(tag_obj)
        factories.DishFactory.create(restaurant=restaurant, comment=comment)
        for name in names:
            factories.DishFactory.create(restaurant=restaurant, name=name)

        query = DishElasticQueryManager.query_multi_match(self.search_text)
        queryset = DishElasticQueryManager().perform_search(query, self.search_text)

        self.assertEqual(queryset.count(), 4)

    def test_document_indexing(self) -> None:
        dish = factories.DishFactory.create(restaurant=models.Restaurant.objects.first(), name=self.search_text)
        DishDocument().update(dish)

        es = connections.get_connection()
        result = es.get(index=DishDocument._index._name, id=dish.pk)

        self.assertEqual(result['_source']['name'], self.search_text)
