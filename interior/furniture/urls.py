from django.urls import path, include 
from . import views
from .views import Cart, CheckOut

urlpatterns = [
    path('', views.Store, name='store'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.Product_detail, name='product-detail'),
    path('category/<slug:category_slug>/', views.Category_products, name='category_products'),
    path('search/', views.search, name='search'),
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('logout/', views.logout, name='logout'),
    path("add-to-cart/", views.add_to_cart, name="add_to_cart"),
    path('cart/', Cart.as_view(), name='cart'),
    path('checkout/', CheckOut.as_view(), name='checkout'),
    #path('verify-payment/', VerifyPayment.as_view(), name='verify-payment'),
]