from typing import Any

from django.db.models.query import QuerySet

from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import analysis, analyzer

from restaurant.models import Dish, Tag

russian_stop = analysis.token_filter('russian_stop', type='stop', stopwords='_russian_')
russian_stemmer = analysis.token_filter('russian_stemmer', type='stemmer', language='russian')
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
    tags = fields.ObjectField(properties={
        'name': fields.TextField(),
    })
    name = fields.TextField(required=True, analyzer=russian_analyzer)
    comment = fields.TextField(required=False, analyzer=russian_analyzer)
    search_text = fields.TextField(analyzer=russian_analyzer)

    class Index:
        name = 'dishes'
        # Recommended for production: 'number_of_replicas': 1
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0,
        }

    class Django:
        model = Dish
        related_models = [Tag]
        fields = ['id']

    def get_instances_from_related(self, related_instance: Any) -> QuerySet | None:
        if isinstance(related_instance, Tag):
            return self.Django.model.objects.filter(tags=related_instance)
        return None

    def prepare_search_text(self, instance: Dish) -> str:
        tag_names = ' '.join(tag.name for tag in instance.tags.all())
        return f'{instance.name} {instance.comment or ""} {tag_names}'
