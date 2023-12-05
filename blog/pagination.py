from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class DynamicPageSizePagination(PageNumberPagination):
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_page_size(self, request):
        page_size = super().get_page_size(request)
        if page_size:
            return min(int(page_size), self.max_page_size)
        return self.page_size
