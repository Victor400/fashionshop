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
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Product, Category

def product_list(request):
    qs = Product.objects.filter(is_active=True)

    # filters
    cat = request.GET.get("cat")
    if cat:
        qs = qs.filter(category__slug=cat)

    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(brand__name__icontains=q)
        )

    # sorting (?sort=price_asc|price_desc)
    sort = request.GET.get("sort")
    if sort == "price_asc":
        qs = qs.order_by("price")
    elif sort == "price_desc":
        qs = qs.order_by("-price")
    else:
        qs = qs.order_by("-id")  # newest first

    # pagination
    paginator = Paginator(qs, 12)  # 12 per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # categories for simple filter UI
    cats = Category.objects.order_by("display_name").values("slug", "display_name")

    ctx = {
        "page_obj": page_obj,
        "total": qs.count(),
        "cats": cats,
        "active_cat": cat,
        "q": q,
        "sort": sort,
    }
    return render(request, "catalog/product_list.html", ctx)

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "catalog/product_detail.html", {"p": product})
