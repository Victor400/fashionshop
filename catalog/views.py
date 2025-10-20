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


# ---------- Public: list & detail ----------
def product_list(request):
    qs = Product.objects.select_related("brand", "category").all()

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
            messages.success(request, f'Product “{product.name}” created.')
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
            messages.success(request, f'Product “{product.name}” updated.')
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
        messages.success(request, f'Product “{name}” deleted.')
        return redirect("catalog:product_list")

    return render(request, "catalog/product_confirm_delete.html", {"p": product})


# ================================
# Bag (session cart)
# ================================
def _cart(request):
    """Return (and create if missing) the session cart dict."""
    return request.session.setdefault("cart", {})


def bag_detail(request):
    """
    Show current session bag with rows and subtotal.
    """
    cart = _cart(request)
    skus = list(cart.keys())
    products = {p.sku: p for p in Product.objects.filter(sku__in=skus)}
    rows, subtotal = [], Decimal("0.00")

    for sku, qty in cart.items():
        p = products.get(sku)
        if not p:
            continue
        unit = Decimal(p.price)
        q = int(qty)
        line = unit * q
        rows.append(
            {
                "product": p,
                "sku": sku,
                "qty": q,
                "unit": unit,
                "line": line,
            }
        )
        subtotal += line

    ctx = {
        "rows": rows,
        "subtotal": subtotal.quantize(Decimal("0.01")),
        "is_empty": len(rows) == 0,
    }
    return render(request, "catalog/bag.html", ctx)


@require_http_methods(["POST"])
def add_to_bag(request, sku):
    """
    Add one item to the bag and show the bag page.
    """
    p = get_object_or_404(Product, sku=sku, is_active=True)

    # Optional stock check
    if getattr(p, "stock", 1) <= 0:
        messages.warning(request, "That item is currently out of stock.")
        return redirect("catalog:product_detail", slug=p.slug)

    cart = _cart(request)
    cart[sku] = int(cart.get(sku, 0)) + 1
    request.session.modified = True

    messages.success(request, f'Added “{p.name}” to your bag.')
    return redirect("catalog:bag_detail")


@require_http_methods(["POST"])
def update_bag_qty(request, sku):
    """
    Set exact quantity (remove if <= 0).
    """
    cart = _cart(request)
    try:
        qty = int(request.POST.get("qty", "1"))
    except ValueError:
        qty = 1

    if qty <= 0:
        cart.pop(sku, None)
        messages.info(request, "Item removed.")
    else:
        cart[sku] = qty
        messages.success(request, "Quantity updated.")

    request.session.modified = True
    return redirect("catalog:bag_detail")


@require_http_methods(["POST"])
def remove_from_bag(request, sku):
    cart = _cart(request)
    if sku in cart:
        cart.pop(sku)
        request.session.modified = True
        messages.info(request, "Item removed.")
    return redirect("catalog:bag_detail")
