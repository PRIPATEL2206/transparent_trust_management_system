from django.http import HttpRequest
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, login_not_required
from django.views.decorators.http import require_POST
from django.views.decorators.cache import cache_page

from roles.decorators import admin_required
from services.rate_limit import rate_limit
from services.pagination import safe_paginate
from dashboard.services import ActivityLogService
from notices.services import NotificationService
from .models import Product, Order
from .forms import OrderForm, ProductForm
from .services import ProductService


@login_not_required
@cache_page(60 * 2)
def product_list_view(request: HttpRequest):
    products = ProductService.get_active_products()
    search = request.GET.get('q', '')[:100]
    if search:
        products = products.filter(name__icontains=search)
    page, _ = safe_paginate(products, request, default_per_page=12)
    context = {'page': page, 'search': search}
    return render(request, 'products/product_list.html', context)


@login_not_required
def product_detail_view(request: HttpRequest, product_id: int):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    form = OrderForm()
    context = {'product': product, 'form': form}
    return render(request, 'products/product_detail.html', context)


@login_required
@rate_limit(max_attempts=10, window=300, key_prefix='place_order')
def place_order_view(request: HttpRequest, product_id: int):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            ProductService.place_order(
                user=request.user,
                product=product,
                quantity=form.cleaned_data['quantity']
            )
            ActivityLogService.log(
                request.user, f"Placed order for '{product.name}' (qty: {form.cleaned_data['quantity']})",
                category='order', request=request
            )
            messages.success(request, "Order placed successfully.")
            return redirect('products_orders')
    return redirect('products_detail', product_id=product_id)


@login_required
def order_list_view(request: HttpRequest):
    orders = ProductService.get_user_orders(request.user)
    page, _ = safe_paginate(orders, request)
    context = {'page': page}
    return render(request, 'products/order_list.html', context)


@login_required
@require_POST
def cancel_order_view(request: HttpRequest, order_id: int):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    ProductService.cancel_order(order, request.user)
    ActivityLogService.log(
        request.user, f"Cancelled order #{order.id} for '{order.product.name}'",
        category='order', request=request
    )
    messages.success(request, "Order cancelled.")
    return redirect('products_orders')


@admin_required
def order_admin_view(request: HttpRequest):
    orders = Order.objects.select_related('user', 'product').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    page, _ = safe_paginate(orders, request, default_per_page=20)
    context = {'page': page, 'status': status}
    return render(request, 'products/order_admin.html', context)


@admin_required
@require_POST
def order_action_view(request: HttpRequest, order_id: int):
    order = get_object_or_404(Order, id=order_id)
    action = request.POST.get('action')
    if action == 'confirm':
        ProductService.confirm_order(order, request.user)
        ActivityLogService.log(
            request.user, f"Confirmed order #{order.id} for {order.user.username}",
            category='order', target_user=order.user, request=request
        )
        NotificationService.send(
            order.user, "Order Confirmed",
            f"Your order for '{order.product.name}' has been confirmed.",
            notification_type='success', link='/products/orders/'
        )
        messages.success(request, "Order confirmed.")
    elif action == 'deliver':
        order.status = 'delivered'
        order.save()
        ActivityLogService.log(
            request.user, f"Delivered order #{order.id} for {order.user.username}",
            category='order', target_user=order.user, request=request
        )
        NotificationService.send(
            order.user, "Order Delivered",
            f"Your order for '{order.product.name}' has been delivered.",
            notification_type='success', link='/products/orders/'
        )
        messages.success(request, "Order marked as delivered.")
    return redirect('products_admin_orders')


@admin_required
def product_admin_list_view(request: HttpRequest):
    products = Product.objects.select_related('category').order_by('-created_at')
    search = request.GET.get('q', '')[:100]
    if search:
        products = products.filter(name__icontains=search)
    page, _ = safe_paginate(products, request, default_per_page=15)
    context = {'page': page, 'search': search}
    return render(request, 'products/product_admin_list.html', context)


@admin_required
def product_create_view(request: HttpRequest):
    form = ProductForm()
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            ActivityLogService.log(
                request.user, f"Created product '{product.name}'",
                category='order', request=request
            )
            messages.success(request, "Product created successfully.")
            return redirect('products_admin_list')
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Add Product'})


@admin_required
def product_edit_view(request: HttpRequest, product_id: int):
    product = get_object_or_404(Product, id=product_id)
    form = ProductForm(instance=product)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            ActivityLogService.log(
                request.user, f"Updated product '{product.name}'",
                category='order', request=request
            )
            messages.success(request, "Product updated successfully.")
            return redirect('products_admin_list')
    return render(request, 'products/product_form.html', {'form': form, 'title': 'Edit Product', 'product': product})
