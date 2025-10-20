# catalog/views.py
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from .forms import ProductForm
from .models import Product


# ---------- Public: list & detail ----------
def product_list(request):
    qs = Product.objects.select_related("brand", "category").all()

    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(sku__icontains=q) |
            Q(brand__name__icontains=q)
        )

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


# ---------- Staff guard ----------
def _require_staff(request):
    if not (request.user.is_authenticated and request.user.is_staff):
        raise PermissionDenied("You must be staff to manage products.")


# ---------- Staff: create ----------
def product_create(request):
    _require_staff(request)

    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"Product “{product.name}” created.")
            return redirect("catalog:product_detail", slug=product.slug)
        messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()

    return render(request, "catalog/product_form.html", {"form": form})


# ---------- Staff: update ----------
def product_update(request, slug):
    _require_staff(request)

    product = get_object_or_404(Product, slug=slug)
    form = ProductForm(request.POST or None, instance=product)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, f"Product “{product.name}” updated.")
            return redirect("catalog:product_detail", slug=product.slug)
        messages.error(request, "Please correct the errors below.")

    return render(
        request,
        "catalog/product_form.html",
        {"form": form, "is_edit": True, "p": product},
    )


# ---------- Staff: delete ----------
def product_delete(request, slug):
    _require_staff(request)

    product = get_object_or_404(Product, slug=slug)

    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"Product “{name}” deleted.")
        return redirect("catalog:product_list")

    # GET = show confirmation
    return render(request, "catalog/product_confirm_delete.html", {"p": product})

#---------- Public: add to bag -----------
@require_http_methods(["GET", "POST"])
def add_to_bag(request, sku):
    # Only add active & in-stock products
    p = get_object_or_404(Product.objects.select_related("brand", "category"),
                          sku=sku, is_active=True)

    if getattr(p, "stock", 1) <= 0:
        messages.warning(request, "That item is currently out of stock.")
        return redirect(reverse("catalog:product_detail", args=[p.slug]))

    bag = request.session.get("cart", {})
    bag[sku] = int(bag.get(sku, 0)) + 1
    request.session["cart"] = bag
    request.session.modified = True

    messages.success(request, f"Added “{p.name}” to your bag.")

    # go back to where the user came from (or product detail)
    next_url = request.GET.get("next") or reverse("catalog:product_detail", args=[p.slug])
    return redirect(next_url)
