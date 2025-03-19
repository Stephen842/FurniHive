from django.contrib import admin
from tinymce.widgets import TinyMCE
from django.db import models
from django.db.models import Q
from .models import MyUsers, Category, Product

# Register your models here.

class UserAdmin(admin.ModelAdmin):
    # Specify the fields to be displayed in the list view
    list_display = ('id', 'name', 'is_active', 'is_staff')
    
    # Add filters in the right sidebar
    list_filter = ('is_active', 'is_staff')
    
    # Add a search bar at the top of the list view
    search_fields = ('name', 'email', 'username', 'phone')
    
    # Add fields to be displayed in the detail view
    fieldsets = (
        (None, {'fields': ('name', 'email', 'username', 'phone', 'country', 'is_active', 'is_staff')}),
        ('Permissions', {'fields': ('is_superuser',)}),
    )


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug for categories
    ordering = ('name',)  # Sort categories alphabetically


# Register Product Model in Admin Panel
class ProductsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'price', 'stock_availability', 'featured')
    search_fields = ('name', 'slug', 'category__name')
    list_filter = ('stock_availability', 'featured')
    ordering = ('name',)

    filter_horizontal = ('category',)

    prepopulated_fields = {'slug': ('name',)}  # Auto-generate slug in admin panel


    formfield_overrides = {
        models.TextField: {'widget': TinyMCE()},
    }

    def get_search_results(self, request, queryset, search_term):
        """Allow searching by product name and category name."""
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        queryset |= self.model.objects.filter(Q(category__name__icontains=search_term))

        return queryset, use_distinct
admin.site.register(MyUsers, UserAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductsAdmin)
