from django.db import models


class WeightEnum(models.TextChoices):
    G = 'г', 'г'
    KG = 'кг', 'кг'
    ML = 'мл', 'мл'
    L = 'л', 'л'
