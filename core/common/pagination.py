from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """표준 페이지네이션 클래스"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
