from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from utils.exceptions import success

class DynamicPageSizePagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(success({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        }))
