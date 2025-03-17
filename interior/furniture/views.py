from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count
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
    related = Product.objects.filter(category__in=product.category.all()).exclude(id=product.id).annotate(matching_categories=Count('category', filter=Q(category__in=product.category.all()))).filter(matching_categories__gt=0).distinct()

    context = {
        'category': category,
        'product': product,
        'related': related,
    }    
    return render(request, 'pages/product_detail.html', context)

def Category_products(request, category_slug):
    categories = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category)

    context = {
        'category': categories,
        'products': products,
    }
    return render(request, 'pages/category_products.html', context)

def search(request):
    query = request.GET.get('q')
    products = Product.objects.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
    categories = Category.objects.filter(name__icontains=query)
    
    context = {
        'query': query,
        'products': products,
        'categories': categories,
    }
    return render(request, 'pages/search_results.html', context)