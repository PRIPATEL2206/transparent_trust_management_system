from django.contrib.auth.models import User
from django.db import transaction

from services.base import BaseService, service_error_handler
from services.exceptions import ValidationError
from .models import Product, Order


class ProductService(BaseService):

    @staticmethod
    @service_error_handler
    def get_active_products():
        return Product.objects.filter(is_active=True).select_related('category').order_by('-created_at')

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def place_order(user: User, product: Product, quantity: int = 1) -> Order:
        product = Product.objects.select_for_update().get(pk=product.pk)
        if not product.is_active:
            raise ValidationError("This product is not available")
        if product.stock < quantity:
            raise ValidationError(f"Only {product.stock} items available")
        if quantity <= 0:
            raise ValidationError("Quantity must be positive")

        unit_price = product.discounted_price
        total_amount = unit_price * quantity

        order = Order.objects.create(
            user=user,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            status='pending'
        )

        product.stock -= quantity
        product.save()

        ProductService.log_action('order_placed', user=user, order_id=order.id)
        return order

    @staticmethod
    @service_error_handler
    def confirm_order(order: Order, admin_user: User) -> Order:
        if order.status != 'pending':
            raise ValidationError("Only pending orders can be confirmed")
        order.status = 'confirmed'
        order.save()
        ProductService.log_action('order_confirmed', user=admin_user, order_id=order.id)
        return order

    @staticmethod
    @service_error_handler
    @transaction.atomic
    def cancel_order(order: Order, user: User) -> Order:
        if order.status not in ('pending', 'confirmed'):
            raise ValidationError("This order cannot be cancelled")
        order.status = 'cancelled'
        order.save()
        order.product.stock += order.quantity
        order.product.save()
        ProductService.log_action('order_cancelled', user=user, order_id=order.id)
        return order

    @staticmethod
    def get_user_orders(user: User):
        return Order.objects.filter(user=user).select_related('product').order_by('-created_at')
