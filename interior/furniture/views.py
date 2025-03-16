from django.shortcuts import render, get_object_or_404
from .models import Product, Category

# Create your views here.

def Store(request):
    categories = Category.objects.all()

    featured_products = Product.objects.filter(featured=True).order_by('?')[:12]
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'title': 'FurniHive – Redefining Interior Luxury'
    } 

    return render(request, 'pages/home1.html', context)


def Product_detail(request, category_slug, product_slug):
    product = get_object_or_404(Product, slug=product_slug, category__slug=category_slug)
    category = get_object_or_404(Category, slug=category_slug)

    context = {
        'category': category,
        'product': product,
    }    
    return render(request, 'pages/product_detail.html', context)

def Category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)

    context = {
        'category': category,
        'products': products,
    }
    return render(request, 'pages/category_products.html', context)