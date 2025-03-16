from django.urls import path, include 
from . import views

urlpatterns = [
    path('', views.Store, name='store'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.Product_detail, name='product-detail'),
    path('category/<slug:category_slug>/', views.Category_products, name='category_products'),
]