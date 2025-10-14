import enum

from django.db import models


class WeightEnum(models.TextChoices, enum.Enum):
    G = 'г', 'г'
    KG = 'кг', 'кг'
    ML = 'мл', 'мл'
    L = 'л', 'л'
