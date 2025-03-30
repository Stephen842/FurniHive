from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model, login as auth_login, authenticate, logout as auth_logout
from django.contrib.auth.hashers import  make_password
from django.db.models import Q, Count
from django.views import View
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.templatetags.static import static
import requests
from django.conf import settings
from django.contrib import messages
import uuid
from .models import MyUsers, Product, Category, CartItem, Order, OrderItem
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

    featured_products = Product.objects.filter(featured=True).order_by('?')[:16]
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
        shipping_cost = 2 # Assuming shipping is a fixed cost

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



@method_decorator(login_required, name='dispatch')
class CheckOut(View):
    def get_cart_details(self, user):
        # Retrieve cart items and calculate subtotal.
        cart_items = CartItem.objects.filter(user=user)
        cart_details, subtotal = [], 0

        for item in cart_items:
            # Ensure product price is properly handled
            price = item.product.price
            if isinstance(price, str):  # Check if it's a string before replacing
                price = int(price.replace(',', ''))
            elif isinstance(price, (int, float)):  # Ensure it's a valid number
                price = int(price)
            else:
                raise ValueError(f"Unexpected price format: {price}")  # Handle unexpected cases

            product_price = price * item.quantity
            subtotal += product_price
            cart_details.append({
                'product_id': item.product.id,
                'product_name': item.product.name,
                'quantity': item.quantity,
                'product_image': item.product.image_0.url if item.product.image_0 and hasattr(item.product.image_0, 'url') else None,
                'product_price': product_price,
            })

        return cart_items, cart_details, subtotal

    def get(self, request):
        '''Render the checkout page with cart details.'''

        cart_items, cart_details, subtotal = self.get_cart_details(request.user)
        shipping_cost = 2
        total = subtotal + shipping_cost

        context = {
            'cart_items': cart_details,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total,
            'title': 'Order Confirmation',
        }
        return render(request, 'pages/checkout.html', context)

    def post(self, request):
        '''Initiate payment and store details in session.'''
        name, email, phone, country, state, city, zipcode = (
            request.POST.get('name'),
            request.POST.get('email'),
            request.POST.get('phone'),
            request.POST.get('country'),
            request.POST.get('state'),
            request.POST.get('city'),
            request.POST.get('zipcode'),
        )
        if not state or not phone:
            messages.error(request, 'State and phone are required.')
            return redirect('checkout')
        
        user = request.user
        shipping_cost = 2
        cart_items, cart_details, subtotal = self.get_cart_details(user)

        if not cart_items.exists():
            messages.error(request, 'Your Cart is Empty.')
            return redirect('store')
        
        order_price = subtotal + shipping_cost

        '''Store order details in session before payment'''
        request.session['pending_order'] = {
            'user_id': user.id,
            'name': name,
            'email': email,
            'phone': phone,
            'state': state,
            'country': country,
            'city': city,
            'zipcode': zipcode,
            'cart_items': cart_details,
            'total_price': order_price,
        }

        # Flutterwave Payment Data
        payload = {
            'tx_ref': uuid.uuid4().hex[:10].upper(),
            'amount': order_price,
            'currency': 'USD',
            'redirect_url': request.build_absolute_uri(reverse('verify-payment')),  # Verify payment after success
            'payment_options': 'card, ussd, banktransfer',
            'customer': {
                'email': user.email,
                'phonenumber': phone,
                'name': user.get_full_name()
            },
            'customizations':{
                'title': 'Fast & Secure Payment – FurniHive',
                'description': 'Your order is almost complete! Proceed with a secure payment.',
                'logo': request.build_absolute_uri(static('furnihive.png'))
            }
        }

        headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.post(
                'https://api.flutterwave.com/v3/payments',
                json=payload,
                headers=headers,
                timeout=15  # Add timeout to avoid infinite waiting
            )
            response.raise_for_status()  # Raise an error for HTTP 4xx/5xx

            res_data = response.json()  # Convert response to JSON

            if res_data.get('status') == 'success':
                return redirect(res_data['data']['link'])  # Redirect to payment page
            else:
                messages.error(request, 'Payment failed. Try again.')
                return redirect('payment-failed')

        except requests.exceptions.Timeout:
            messages.error(request, 'Payment request timed out. Please try again.')
            return redirect('checkout')

        except requests.exceptions.ConnectionError:
            messages.error(request, 'Network error. Please check your internet connection.')
            return redirect('checkout')

        except requests.exceptions.HTTPError as e:
            messages.error(request, f'Payment gateway error: {e}')
            return redirect('checkout')

        except requests.exceptions.RequestException as e:
            messages.error(request, f'An unexpected error occurred: {e}')
            return redirect('checkout')


class VerifyPayment(View):
    def get(self, request):
        '''Verify payment with flutterwave and create order only if successful.'''
        transaction_id = request.GET.get('transaction_id')

        if not transaction_id:
            messages.error(request, 'Invalid payment attempt.')
            return redirect('checkout')
        
        '''Fetch transaction status from Flutterwave'''
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {
            'Authorization': f'Bearer {settings.FLUTTERWAVE_SECRET_KEY}'
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            res_data = response.json()

            if res_data.get('status') == 'success' and res_data['data']['status'] == 'successful':
                '''Retrieve order details from session'''
                pending_order = request.session.get('pending_order')

                if not pending_order:
                    messages.error(request, 'Order session expired. Please try again.')
                    return redirect('checkout')
                
                '''Get user'''
                user = MyUsers.objects.get(id=pending_order['user_id'])

                '''Check if order already exists(To avoid duplication)'''
                existing_order = Order.objects.filter(order_id=res_data['data']['tx_ref']).exists()
                if existing_order:
                    messages.warning(request, 'Your order has already been processed.')
                    return redirect('order-confirm', order_id=res_data['data']['tx_ref'])

                '''Create order'''
                order = Order.objects.create(
                    user=user,
                    price=pending_order['total_price'],
                    country=pending_order['country'],
                    state=pending_order['state'],
                    city=pending_order['city'],
                    zipcode=pending_order['zipcode'],
                    name=pending_order['name'],
                    email=pending_order['email'],
                    phone=pending_order['phone'],
                    order_id=res_data['data']['tx_ref'],
                    paid=True
                )

                '''Create order items'''
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product_id=item['product_id'], quantity=item['quantity'])
                    for item in pending_order['cart_items']
                ])

                '''Clear session data after successful order creation'''
                del request.session['pending_order']

                messages.success(request, 'Payment successful! Your order has been placed.')
                return redirect('order-confirm', order_id=order.order_id)
            
            else:
                messages.error(request, 'Payment verification failed. Try again.')
                return redirect('payment-failed')
            
        except requests.Timeout:
            messages.error(request, 'Payment verification timed out. Please try again.')
            return redirect('payment-failed')
          
        except requests.RequestException as e:
            messages.error(request, f'Error verifying payment: {str(e)}')
            return redirect('payment-failed')


@login_required
def Order_confirm(request, order_id):
    status = request.GET.get('status')  # Get the status from the URL
    tx_ref = request.GET.get('tx_ref')  # Get transaction reference

    # Retrieve the order details from the database
    order = Order.objects.filter(order_id=order_id).first()

    context = {
        'title': 'Payment Successful – Your Order is Confirmed!',
        'order_id': order_id,
        'status': status,  # Pass payment status
        'tx_ref': tx_ref,  # Pass transaction reference
        'order': order  # Pass the order object if needed
    }

    if status == 'cancelled':
        return redirect('payment-failed')  # Redirect to a payment cancelled page

    # Proceed with normal order confirmation if not cancelled
    return render(request, 'pages/order_confirm.html', context)

@login_required
def Payment_failed(request):
    context = {
        'title': 'Oops! Payment Unsuccessful',
    }
    return render(request, 'pages/payment-cancel.html', context)


@method_decorator(login_required, name='dispatch')
class OrderView(View):
    def get(self, request):

        # Get orders directly from the database linked to the logged-in user
        orders = OrderItem.objects.filter(order__my_user=request.user).order_by('-id')

        if not orders.exists():
            messages.info(request, 'You have no orders yet.')

        # Calculate subtotal by summing all the prices
        subtotal = sum(float(order.product.price) * order.quantity for order in orders)

        shipping_cost = 2
        total = subtotal + shipping_cost

         # Attach computed total price to each order item
        for order in orders:
            order.total_price = float(order.product.price) * order.quantity


        context = {
                'orders': orders,
                'title': 'Summary of Your Purchase',
                'subtotal': subtotal,
                'shipping_cost': shipping_cost,
                'total': total,

        }
        return render(request, 'pages/orders.html', context)


def error_404(request, exception):
    context = {
        'status_code': 404,
        'error_message': 'Page Not Found',
        'title': "Oops! The page you're looking for isn't available.",
    }
    return render(request, 'pages/404.html', context, status=404)

def error_500(request):
    context = {
        'status_code': 500,
        'error_message': 'Internal Server Error',
        'title': '500 - Server Error',
    }
    return render(request, 'pages/500.html', context, status=500)
