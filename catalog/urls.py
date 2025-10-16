# catalog/urls.py
from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("p/new/", views.product_create, name="product_create"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("p/<slug:slug>/edit/", views.product_update, name="product_update"),
    path("p/<slug:slug>/delete/", views.product_delete, name="product_delete"),
    path("bag/add/<slug:sku>/", views.add_to_bag, name="add_to_bag"), 
]
