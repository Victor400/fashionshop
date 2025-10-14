from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category


def product_list(request):
    qs = Product.objects.select_related("brand", "category").all()

    q = request.GET.get("q")
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(brand__name__icontains=q))

    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(category__slug=cat)

    sort = request.GET.get("sort")
    direction = request.GET.get("direction")
    allowed_fields = {"price": "price", "name": "name"}
    sort_field = allowed_fields.get(sort)
    if sort_field:
        qs = qs.order_by(f"-{sort_field}" if direction == "desc" else sort_field)

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "active_cat": cat,
        "sort": sort or "",
        "direction": direction or "",
    }
    return render(request, "catalog/product_list.html", context)


def product_detail(request, slug):
    p = get_object_or_404(
        Product.objects.select_related("brand", "category"),
        slug=slug,
    )
    return render(request, "catalog/product_detail.html", {"p": p})
