from django.db.models import QuerySet

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Bool

from restaurant.documents import DishDocument

SEARCH_SIZE = 2000


class DishElasticQueryManager:
    document_class = DishDocument

    @staticmethod
    def query_match_by_name(text: str) -> Q:
        """Full-text search by name field."""
        return Q(
            'bool',
            should=[Q('match', name=text)],
            minimum_should_match=1,
        )

    @staticmethod
    def query_multi_match(text: str) -> Q:
        """Full-text search by multiple text fields: name, comment, tags.name."""
        return Q(
            'multi_match',
            query=text,
            fields=['name', 'comment', 'tags.name'],
            type='cross_fields',  # other options: best_fields, phrase
            operator='and',  # all words from the query must be present
        )

    def perform_search(self, query: Bool, text: str) -> QuerySet:
        search = self.document_class.search().extra(size=SEARCH_SIZE).query(query)
        return search.to_queryset()
