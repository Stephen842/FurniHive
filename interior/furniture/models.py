from django.db import models
from django.utils.text import slugify

# Create your models here.

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
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    discount_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True)
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
