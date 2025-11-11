from typing import Any

from django.db.models.query import QuerySet

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analysis, analyzer

from restaurant.models import Dish, Tag

russian_stop = analysis.token_filter(
    'russian_stop', type='stop', stopwords='_russian_',
)
russian_stemmer = analysis.token_filter(
    'russian_stemmer', type='stemmer', language='russian',
)

russian_analyzer = analyzer(
    'russian_morphology',
    type='custom',
    tokenizer='standard',
    char_filter='html_strip',
    filter=[
        'lowercase',
        russian_stop,
        russian_stemmer,
    ],
)


@registry.register_document
class DishDocument(Document):
    restaurant = fields.ObjectField(properties={
        'id': fields.IntegerField(),
        'name': fields.TextField(),
        'category': fields.ObjectField(properties={'name': fields.TextField()}),
    })
    name = fields.TextField(required=True, analyzer=russian_analyzer)

    class Index:
        name = 'dishes'
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Dish
        related_models = [Tag]

        fields = [
            'id',
        ]

    def get_instances_from_related(self, related_instance: Any) -> QuerySet | None:
        if isinstance(related_instance, Tag):
            return Dish.objects.filter(tags=related_instance)
        return None
