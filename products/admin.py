from django.contrib import admin
from .models import Product, ProductCategory, Order


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'discount_percent', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'quantity', 'total_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'product__name')
    ordering = ('-created_at',)
