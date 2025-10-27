# catalog/views.py
from decimal import Decimal
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_http_methods

from .forms import ProductForm
from .models import Product


def product_list(request):
    # Only show active products that have a usable slug
    qs = (
        Product.objects
        .select_related("brand", "category")
        .filter(is_active=True)
        .exclude(slug__isnull=True)
        .exclude(slug__exact="")
        .order_by("name")   # default stable ordering (fixes pagination warning)
    )

    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(sku__icontains=q)
            | Q(brand__name__icontains=q)
        )

    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(category__slug=cat)

    sort = request.GET.get("sort")
    direction = request.GET.get("direction")
    allowed = {"price": "price", "name": "name"}
    field = allowed.get(sort)
    if field:
        qs = qs.order_by(f"-{field}" if direction == "desc" else field)

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    ctx = {
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "active_cat": cat,
        "sort": sort or "",
        "direction": direction or "",
    }
    return render(request, "catalog/product_list.html", ctx)


def product_detail(request, slug):
    p = get_object_or_404(
        Product.objects.select_related("brand", "category"),
        slug=slug,
        is_active=True,
    )
    return render(request, "catalog/product_detail.html", {"p": p})
