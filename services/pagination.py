from django.core.paginator import Paginator


MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 10


def safe_paginate(queryset, request, default_per_page=DEFAULT_PAGE_SIZE, max_per_page=MAX_PAGE_SIZE):
    """Paginate a queryset with enforced size limits.

    Returns (page, paginator) tuple. Handles invalid page numbers gracefully.
    """
    page_number = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', default_per_page)

    try:
        per_page = int(per_page)
    except (ValueError, TypeError):
        per_page = default_per_page

    per_page = max(1, min(per_page, max_per_page))

    try:
        page_number = int(page_number)
    except (ValueError, TypeError):
        page_number = 1

    paginator = Paginator(queryset, per_page)

    if page_number < 1:
        page_number = 1
    elif page_number > paginator.num_pages and paginator.num_pages > 0:
        page_number = paginator.num_pages

    page = paginator.get_page(page_number)
    return page, paginator
