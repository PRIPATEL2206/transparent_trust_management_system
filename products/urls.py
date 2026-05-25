from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list_view, name='products_list'),
    path('<int:product_id>/', views.product_detail_view, name='products_detail'),
    path('<int:product_id>/order/', views.place_order_view, name='products_order'),
    path('orders/', views.order_list_view, name='products_orders'),
    path('orders/<int:order_id>/cancel/', views.cancel_order_view, name='products_cancel'),
    path('admin/products/', views.product_admin_list_view, name='products_admin_list'),
    path('admin/products/create/', views.product_create_view, name='products_create'),
    path('admin/products/<int:product_id>/edit/', views.product_edit_view, name='products_edit'),
    path('admin/orders/', views.order_admin_view, name='products_admin_orders'),
    path('admin/orders/<int:order_id>/action/', views.order_action_view, name='products_order_action'),
]
