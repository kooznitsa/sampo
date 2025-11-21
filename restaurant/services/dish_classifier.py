import re
from typing import Collection

from pymorphy3 import MorphAnalyzer

import restaurant.constants as constants
from restaurant.models import Dish

CATEGORIES = {
    'вино': constants.WINE,
    'грузинская кухня': constants.GEORGIAN,
    'итальянская кухня': constants.ITALIAN,
    'кофе': constants.COFFEE,
    'морепродукты': constants.SEAFOOD,
    'мясо': constants.MEAT,
    'пиво': constants.BEER,
    'пицца': constants.PIZZA,
    'русская кухня': constants.RUSSIAN,
    'рыба': constants.FISH,
    'суп': constants.SOUP,
    'японская кухня': constants.JAPANESE,
}


class DishClassifier:

    def __init__(self, dish: Dish) -> None:
        self.dish = dish
        self.morph = MorphAnalyzer()

    def prepare_words(self) -> list:
        string = f'{self.dish.name} {self.dish.comment or ""}'.lower()
        return re.findall(r'[а-яёa-z]+', string)

    def lemmatize(self, words: list[str] | Collection[str]) -> set:
        return {self.morph.parse(word)[0].normal_form for word in words}

    def classify_dish(self) -> set:
        words = self.prepare_words()
        lemmas = self.lemmatize(words)
        return {category for category in CATEGORIES if bool(lemmas & self.lemmatize(CATEGORIES[category]))}
