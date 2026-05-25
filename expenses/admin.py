from django.contrib import admin
from services.admin_base import AuditModelAdmin
from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(AuditModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)


@admin.register(Expense)
class ExpenseAdmin(AuditModelAdmin):
    list_display = ('title', 'raised_by', 'amount', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'description', 'raised_by__username')
    readonly_fields = ('raised_by', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
