from datetime import date, timedelta
from decimal import Decimal

from django.test import tag, TestCase
from django.utils import timezone

from restaurant.enums import WeightEnum
import restaurant.services.parsers as parsers


@tag('services', 'regex')
class TestRegex(TestCase):

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
