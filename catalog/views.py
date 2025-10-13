from django.shortcuts import render
from django.db.models import F
from .models import Product

def product_list(request):
    qs = (
        Product.objects.all()
        .select_related("brand", "category")
    )

    # optional filters you already use
    q = request.GET.get("q")
    if q:
        qs = qs.filter(name__icontains=q)

    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(category__slug=cat)

    # --- SORTING ---
    sort = request.GET.get("sort")         # e.g. "price" or "name"
    direction = request.GET.get("direction")  # "asc" or "desc"

    # whitelist allowed fields (avoid arbitrary order_by injection)
    allowed_fields = {
        "price": "price",
        "name": "name",
        # add more allowed sort fields as needed
    }

    sort_field = allowed_fields.get(sort)
    if sort_field:
        if direction == "desc":
            sort_key = f"-{sort_field}"
        else:
            sort_key = sort_field
        qs = qs.order_by(sort_key)

    # paginate as you already do
    from django.core.paginator import Paginator
    paginator = Paginator(qs, 12)  # 12 per page or your number
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "active_cat": cat,
        "sort": sort or "",
        "direction": direction or "",
    }
    return render(request, "catalog/product_list.html", context)
