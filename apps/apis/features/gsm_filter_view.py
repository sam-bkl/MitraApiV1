# views.py
import hashlib

from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.utils import timezone
from ..models import GsmChoice
from django.db.models import Q

class GsmChoicePagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_gsm_numbers(request):
    """
    POST endpoint for searching GSM numbers
    """

    # -----------------------------
    # Input
    # -----------------------------
    circle_code = request.data.get('circle_code')
    filter_by = request.data.get('filter_by')
    query = request.data.get('query', '').strip()

    if not circle_code:
        return Response(
            {"error": "circle_code is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    valid_filters = [
        'begins_with', 'does_not_begin_with',
        'ends_with', 'does_not_end_with',
        'contains', 'does_not_contain'
    ]

    if filter_by and filter_by not in valid_filters:
        return Response(
            {"error": "Invalid filter_by value"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # -----------------------------
    # Cache (PER USER!)
    # -----------------------------
    page_no = request.query_params.get('page', '1')
    cache_key = _get_cache_key(
        request.user.username,
        circle_code,
        filter_by,
        query,
        page_no
    )

    cached = cache.get(cache_key)
    if cached:
        return Response(cached)

    # -----------------------------
    # Base queryset
    # -----------------------------
    # qs = GsmChoice.objects.filter(
    #     circle_code=circle_code,
    #     status=9   # only FREE numbers
    # )
    now_ts = timezone.now()
    qs = (
        GsmChoice.objects.using("read")
        .filter(
            status=9,
            circle_code=int(circle_code)
        )
        .filter(
            Q(reserve_end_date__isnull=True) |
            Q(reserve_end_date__lt=now_ts)
        )
    )

    # -----------------------------
    # Filters
    # -----------------------------
    if filter_by and query:
        if filter_by == 'begins_with':
            qs = qs.filter(gsmno__startswith=query)
        elif filter_by == 'does_not_begin_with':
            qs = qs.exclude(gsmno__startswith=query)
        elif filter_by == 'ends_with':
            qs = qs.filter(gsmno__endswith=query)
        elif filter_by == 'does_not_end_with':
            qs = qs.exclude(gsmno__endswith=query)
        elif filter_by == 'contains':
            qs = qs.filter(gsmno__contains=query)
        elif filter_by == 'does_not_contain':
            qs = qs.exclude(gsmno__contains=query)

    # -----------------------------
    # Convert to values_list
    # -----------------------------
    qs = qs.values_list('gsmno', flat=True)

    # -----------------------------
    # Seeded deterministic offset
    # -----------------------------
    total = qs.count()
    paginator = GsmChoicePagination()
    page_size = paginator.page_size
    page = int(page_no)

    seed_str = f"{request.user.username}-{circle_code}-{filter_by}-{query}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest(), 16)

    if total > 0:
        base_offset = seed % max(total - page_size + 1, 1)
        offset = base_offset + (page - 1) * page_size
    else:
        offset = 0

    # Slice ONCE (no DRF slicing later)
    page_qs = list(qs[offset: offset + page_size])

    # -----------------------------
    # Build response (DRF style)
    # -----------------------------
    response_data = {
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": page_qs
    }

    cache.set(cache_key, response_data, timeout=60)  # cache 1 min
    return Response(response_data)


def _get_cache_key(username, circle_code, filter_by, query, page):
    """
    Cache key MUST include username
    """
    raw = f"user={username}&circle={circle_code}&filter={filter_by}&query={query}&page={page}"
    return "gsmchoice_" + hashlib.md5(raw.encode()).hexdigest()
