from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from phonenumber_field.modelfields import PhoneNumberField
from django_countries.fields import CountryField

# Create your models here.

'''This is for my Custom User model '''

class UsersManager(BaseUserManager):
    def create_user(self, email, name, username, phone, country, password=None):
        if not email:
            raise ValueError('Enter Email address')
        if not name:
            raise ValueError('Enter Full name')
        if not username:
            raise ValueError('Enter Username')
        if not phone:
            raise ValueError('Enter Phone Number')
        if not country:
            raise ValueError('Enter Country')

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            username=username,
            phone=phone,
            country=country,
        )
        user.set_password(password)  # Hash the password
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, username, phone, country, password=None):
        user = self.create_user(
            email=email,
            name=name,
            username=username,
            phone=phone,
            country=country,
            password=password,
        )
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class MyUsers(AbstractBaseUser, PermissionsMixin):  # Add PermissionsMixin here
    name = models.CharField(max_length=100, blank=False)
    username = models.CharField(max_length=100, unique=True, blank=False)
    email = models.EmailField(unique=True, blank=False)
    phone = models.CharField(max_length=25, unique=True, blank=False, null=False)
    country = CountryField(blank_label='Select Country',)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = UsersManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'username', 'country', 'phone']

    def save(self, *args, **kwargs):
        """Ensure username and email are stored in lowercase"""
        self.email = self.email.lower()
        self.username = self.username.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_full_name(self):
        """Return the user's full name"""
        return self.name

    def get_short_name(self):
        """Return the short name (username in this case)"""
        return self.username
    
    class Meta:
        verbose_name_plural = 'My Users'


'''This is for the category aspect of this project with a name field to be used in categorizing product '''

class Category(models.Model):
    name = models.CharField(max_length=50, db_index=True)
    slug = models.SlugField(unique=True, blank=True, null=True)  # Slug for category

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'

    @staticmethod
    def get_all_categories():
        return Category.objects.all()


'''
    this is for the product, which contain all neccessary details to be added to the product
    it include a static method where one can retrieve a product by it ID, category Id and to retrieve all product'
'''

class Product(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, blank=True, null=True)  # SEO-friendly URL
    price = models.IntegerField(default=0)
    discount_price = models.IntegerField(blank=True, null=True)
    category = models.ManyToManyField(Category, related_name='products')
    description = models.TextField()
    condition = models.CharField(max_length=20, blank=True, null=True)
    color = models.CharField(max_length=20, blank=True, null=True)
    material = models.CharField(max_length=50, blank=True, null=True)
    dimensions = models.CharField(max_length=100, blank=True, null=True)
    weight = models.CharField(max_length=50, blank=True, null=True)
    brand = models.CharField(max_length=50, blank=True, null=True)
    stock_availability = models.BooleanField(default=True)
    usage_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=[('indoor', 'Indoor'), ('outdoor', 'Outdoor'), ('both', 'Both')]
    )
    style = models.CharField(max_length=50, blank=True, null=True)
    assembly_required = models.BooleanField(default=False)
    warranty = models.CharField(max_length=50, blank=True, null=True)
    featured = models.BooleanField(default=False)

    # Image fields
    image_0 = models.ImageField(upload_to='products/')
    image_1 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_2 = models.ImageField(upload_to='products/', blank=True, null=True)
    image_3 = models.ImageField(upload_to='products/', blank=True, null=True)


    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Generate a unique slug using category and product name"""
        if not self.slug:
            base_slug = slugify(f"{self.category.name}-{self.name}") if self.category else slugify(self.name)
            unique_slug = base_slug
            counter = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug

        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name_plural = 'Products'

    #To retrieve product by its ID
    @staticmethod
    def get_products_by_id(ids):
        return Product.objects.filter(id__in=ids).distinct()

    #To get retrieve product stored in the database
    @staticmethod
    def get_all_products():
        return Product.objects.all()

    #To retrieve product using category ID
    @staticmethod
    def get_all_products_by_categoryid(category_id=None):
        if category_id:
            return Product.objects.filter(category=category_id)
        return Product.get_all_products()


class CartItem(models.Model):
    user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, null=True, blank=True, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    shipping = models.CharField(
        max_length=100,
        choices=[
            ('standard', 'Standard Delivery - $2 (3-5 business days)'),
        ],
        default='standard'
    )

    @property
    def total_price(self):
        # Assuming product price is stored as a string with commas, we convert to integer
        return int(self.product.price.replace(',', '')) * self.quantity

    def __str__(self):
        return f"Cart for {self.user} {self.product} (x{self.quantity}) - {self.get_shipping_display() if self.user else 'No user'}"


#This is for the order model, where users fill the neccessary products they are ordering for and then the orders are been submitted
class Order(models.Model):
    my_user = models.ForeignKey(MyUsers, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(Product, related_name="orders")
    order_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()
    state = models.CharField(max_length=50)
    phone = PhoneNumberField(region='US')
    country = CountryField(blank_label='Select Country',)
    name = models.CharField(max_length=50)
    email = models.EmailField()
    city = models.CharField(max_length=50)
    zipcode = models.CharField(max_length=20, blank=True)
    date = models.DateField(auto_now_add=True)
    paid = models.BooleanField(default=False)



    def placeOrder(self):
        self.save()

    #To retrieve an order using User ID
    @staticmethod
    def get_orders_by_user(user_id):
        return Order.objects.filter(my_user=user_id).order_by('-date')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()  # Store quantity per product

    def __str__(self):
        return f"{self.product.name} (x{self.quantity}) in Order {self.order.order_id}"
