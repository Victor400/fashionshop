from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product

def product_list(request):
    qs = Product.objects.filter(is_active=True)

    # category filter (?cat=<category-slug>)
    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(category__slug=cat)

    # search (?q=...)
    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(brand__name__icontains=q)
        )

    qs = qs.order_by("-id")  # newest first
    ctx = {"products": qs, "active_cat": cat, "q": q}
    return render(request, "catalog/product_list.html", ctx)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "catalog/product_detail.html", {"p": product})
