from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.hashers import  make_password
from django.db.models import Q, Count
from .models import Product, Category
from .forms import UserForm, SigninForm

# Create your views here.
        
def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.password = make_password(customer.password)
            customer.save()
            return redirect('store')
    else:
        form = UserForm()

    context = {
        'form': form,
        'title': 'Sign Up to explore our features',
    }
    
    return render(request, 'pages/signup.html', context)



def signin(request):
    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data['identifier']
            password = form.cleaned_data['password']

            # Authenticate user
            user = authenticate(request, username=identifier, password=password)
            if user:
                auth_login(request, user)
                return redirect('store')
            else:
                form.add_error(None, "Invalid credentials. Please try again.")

    else:
        form = SigninForm()

    context = {
        'form': form,
        'title': 'Sign In to Continue Shopping',
    }

    return render(request, 'pages/signin.html', context)

# Handles user logout while keeping session data intact.
def logout(request):
    auth_logout(request)
    return redirect('store') 




def Store(request):
    categories = Category.objects.all()

    featured_products = Product.objects.filter(featured=True).order_by('?')[:12]
    context = {
        'categories': categories,
        'featured_products': featured_products,
        'title': 'FurniHive – Redefining Interior Luxury'
    } 

    return render(request, 'pages/home.html', context)


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
    products = Product.objects.filter(category=categories)

    context = {
        'category': categories,
        'products': products,
    }
    return render(request, 'pages/category_products.html', context)

def search(request):
    query = request.GET.get('q')
    products = Product.objects.filter(Q(name__icontains=query) | Q(category__name__icontains=query)).distinct()
    categories = Category.objects.filter(name__icontains=query)
    
    context = {
        'query': query,
        'products': products,
        'categories': categories,
    }
    return render(request, 'pages/search_results.html', context)