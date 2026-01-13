# views.py
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from ..models import GsmChoice
from ..serializers import GsmChoiceSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated , AllowAny

class GsmChoicePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_gsm_numbers(request):
    """
    POST endpoint for searching GSM numbers
    
    Request Body (JSON):
    {
        "circle_code": 50,           # Required
        "filter_by": "begins_with",  # Optional (can be null)
        "query": "98"                # Optional (can be null or empty)
    }
    """
    # Get parameters from request body
    circle_code = request.data.get('circle_code')
    filter_by = request.data.get('filter_by')
    query = request.data.get('query', '').strip()
    
    # Validate required circle_code
    if not circle_code:
        return Response(
            {
                'error': 'circle_code is required',
                'detail': 'Please provide circle_code in request body'
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate filter_by if provided
    valid_filters = [
        'begins_with', 'does_not_begin_with', 
        'ends_with', 'does_not_end_with', 
        'contains', 'does_not_contain'
    ]
    
    if filter_by and filter_by not in valid_filters:
        return Response(
            {
                'error': 'Invalid filter_by value',
                'detail': f'filter_by must be one of: {", ".join(valid_filters)}',
                'provided': filter_by
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check cache
    page = request.query_params.get('page', '1')
    cache_key = _get_cache_key(circle_code, filter_by, query, page)
    cached_response = cache.get(cache_key)
    if cached_response:
        return Response(cached_response)
    
    # Build queryset
    queryset = GsmChoice.objects.filter(
        circle_code=circle_code,
        status=9   # ONLY free numbers
    ).order_by('gsmno')
        
    # Apply filters if provided
    if filter_by and query:
        if filter_by == 'begins_with':
            queryset = queryset.filter(gsmno__startswith=query)
        elif filter_by == 'does_not_begin_with':
            queryset = queryset.exclude(gsmno__startswith=query)
        elif filter_by == 'ends_with':
            queryset = queryset.filter(gsmno__endswith=query)
        elif filter_by == 'does_not_end_with':
            queryset = queryset.exclude(gsmno__endswith=query)
        elif filter_by == 'contains':
            queryset = queryset.filter(gsmno__contains=query)
        elif filter_by == 'does_not_contain':
            queryset = queryset.exclude(gsmno__contains=query)
    
    # 🔹 Convert to values_list BEFORE pagination
    queryset = queryset.values_list('gsmno', flat=True)
    queryset = queryset.order_by('?')

    # Paginate
    paginator = GsmChoicePagination()
    page = paginator.paginate_queryset(queryset, request)

    # Paginated response
    return paginator.get_paginated_response(list(page))


def _get_cache_key(circle_code, filter_by, query, page):
    """Generate cache key from parameters"""
    import hashlib
    
    params_str = f"circle={circle_code}&filter={filter_by}&query={query}&page={page}"
    hash_obj = hashlib.md5(params_str.encode())
    return f"gsmchoice_{hash_obj.hexdigest()}"