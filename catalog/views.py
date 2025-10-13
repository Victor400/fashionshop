from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import Product

def product_list(request):
    qs = Product.objects.filter(is_active=True).order_by("-id")  # newest first
    return render(request, "catalog/product_list.html", {"products": qs})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, "catalog/product_detail.html", {"p": product})
