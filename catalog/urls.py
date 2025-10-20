from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("p/new/", views.product_create, name="product_create"),
    path("p/<slug:slug>/", views.product_detail, name="product_detail"),
    path("p/<slug:slug>/edit/", views.product_update, name="product_update"),
    path("p/<slug:slug>/delete/", views.product_delete, name="product_delete"),

    # Bag
    path("bag/", views.bag_detail, name="bag_detail"),
    path("bag/add/<str:sku>/", views.add_to_bag, name="add_to_bag"),
    path("bag/update/<str:sku>/", views.update_bag_qty, name="update_bag_qty"),
    path("bag/remove/<str:sku>/", views.remove_from_bag, name="remove_from_bag"),
]
