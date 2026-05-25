from django.contrib import admin
from .models import Transaction, Receipt


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('status', 'transaction_type', 'created_at')
    search_fields = ('user__username', 'reference_id', 'idempotency_key')
    readonly_fields = ('idempotency_key', 'created_at', 'completed_at')
    date_hierarchy = 'created_at'


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'transaction', 'generated_at')
    search_fields = ('receipt_number',)
    readonly_fields = ('generated_at',)
