from django.db.models import QuerySet

from elasticsearch_dsl import Q
from elasticsearch_dsl.query import Bool

from restaurant.documents import DishDocument

SEARCH_SIZE = 2000


class ElasticsearchQueryManager:
    document_class = DishDocument

    @staticmethod
    def query_dishes_containing_word(word: str) -> Bool:
        return Q(
            'bool',
            should=[Q('match', name=word)],
            minimum_should_match=1,
        )

    def perform_search(self, query: Bool, tag: str) -> tuple[int, QuerySet]:
        search = self.document_class.search().extra(size=SEARCH_SIZE).query(query)
        return search.to_queryset()
