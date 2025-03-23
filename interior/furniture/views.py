from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.hashers import  make_password
from django.db.models import Q, Count
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import Product, Category, CartItem
from .forms import UserForm, SigninForm, CartItemForm

# Create your views here.
        
def signup(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            form.save() # Password is already hashed in the form
            return redirect(request.GET.get('next', 'store'))
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

            # Try authenticating by username or email
            user = authenticate(request, username=identifier, password=password)
            
            if user:
                auth_login(request, user)
                return redirect(request.GET.get('next', 'store'))
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


# Function to add to Cart via AJAX API endpoint
@csrf_exempt
def add_to_cart(request):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'message': 'You must be logged in to add items to the cart.'}, status=401)

    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
    
    product_id = request.POST.get('product_id')
    action = request.POST.get('action')

    if not product_id:
        return JsonResponse({'success': False, 'message': 'Missing product ID.'}, status=400)

    if action not in ['add', 'remove']:
        return JsonResponse({'success': False, 'message': 'Invalid action.'}, status=400)

    # Get the product (handle the case if the product does not exist)
    user = request.user
    product = get_object_or_404(Product, id=product_id)

    # Retrieve or create a cart item
    cart_item, created = CartItem.objects.get_or_create(user=user, product=product)

    if action == 'add':
        cart_item.quantity += 1
        cart_item.save()
        message = 'Product added to cart!'

    elif action == 'remove':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
            message = 'Product quantity decreased!'
            
        else:
            cart_item.delete()
            message = 'Product removed from cart!'

    cart_count = CartItem.objects.filter(user=user).count()

    return JsonResponse({'success': True, 'message': message,  'cart_count': cart_count})

@method_decorator(login_required, name='dispatch')
class Cart(View):
    def calculate_cart_totals(self, cart_items):
        '''Helper function to process cart items and calculate totals'''

        featured_products = Product.objects.filter(featured=True).order_by('?')[:8]
        subtotal = 0
        shipping_cost = 2500 # Assuming shipping is a fixed cost

        cart_details = []
        for item in cart_items:
            try:
                product_price = int(float(item.product.price)) if item.product.price else 0
            except (TypeError, ValueError):
                product_price = 0

            total_price = product_price * item.quantity
            subtotal += total_price

            cart_details.append({
                'product': item.product,
                'quantity': item.quantity,
                'total_price': total_price,
            })
        total = subtotal + shipping_cost

        return cart_details, subtotal, total, featured_products
    
    def get(self, request):
        '''Handles displaying cart items'''

        cart_items = CartItem.objects.filter(user=request.user)
        cart_details, subtotal, total, featured_products = self.calculate_cart_totals(cart_items)

        context = {
            'title': 'Your Shopping Cart',
            'cart_items': cart_details,
            'subtotal': subtotal,
            'total': total,
            'featured_products':featured_products,
            'form': CartItemForm()
        }
        return render(request, 'pages/cart.html', context)
    

    def post(self, request):
        '''Handles adding to cart items'''

        form = CartItemForm(request.POST)
        if form.is_valid():
            cart_item = form.save(commit=False)
            cart_item.user = request.user
            cart_item.save()
            return redirect('cart')  # Redirect to avoid resubmission on refresh

        cart_items = CartItem.objects.filter(user=request.user)
        cart_details, subtotal, total, featured_products = self.calculate_cart_totals(cart_items)

        context = {
            'title': 'Your Shopping Cart',
            'cart_items': cart_details,
            'subtotal': subtotal,
            'total': total,
            'featured_products': featured_products,
            'form': form,
        }
        return render(request, 'pages/cart.html', context)
