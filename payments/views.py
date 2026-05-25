import uuid
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from roles.decorators import admin_required
from services.rate_limit import rate_limit
from services.csv_utils import make_csv_response, make_file_response
from .models import Transaction, Receipt
from .forms import PaymentForm
from .services import PaymentService, ReceiptService


@login_required
@rate_limit(max_attempts=10, window=300, key_prefix='payment_create')
def payment_create_view(request: HttpRequest):
    form = PaymentForm()
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            transaction = PaymentService.initiate_payment(
                user=request.user,
                amount=form.cleaned_data['amount'],
                transaction_type=form.cleaned_data['transaction_type'],
                idempotency_key=str(uuid.uuid4()),
                metadata={'notes': form.cleaned_data.get('notes', '')}
            )
            PaymentService.complete_payment(transaction.id)
            messages.success(request, "Payment completed successfully.")
            return redirect('payments_history')
    return render(request, 'payments/payment_form.html', {'form': form})


@login_required
def payment_history_view(request: HttpRequest):
    transactions = PaymentService.get_user_transactions(request.user)
    paginator = Paginator(transactions, 15)
    page = paginator.get_page(request.GET.get('page', 1))
    context = {'page': page}
    return render(request, 'payments/payment_history.html', context)


@login_required
def receipt_download_view(request: HttpRequest, transaction_id: int):
    transaction = get_object_or_404(Transaction, id=transaction_id, user=request.user)

    if not hasattr(transaction, 'receipt') or not transaction.receipt:
        receipt = ReceiptService.generate_receipt(transaction)
    else:
        receipt = transaction.receipt

    if receipt.pdf_file:
        with receipt.pdf_file.open('rb') as f:
            content = f.read()
        return make_file_response(content, f'{receipt.receipt_number}.pdf', 'application/pdf')

    messages.error(request, "Receipt not available.")
    return redirect('payments_history')


@admin_required
def payment_admin_view(request: HttpRequest):
    transactions = Transaction.objects.select_related('user').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        transactions = transactions.filter(status=status)
    paginator = Paginator(transactions, 20)
    page = paginator.get_page(request.GET.get('page', 1))
    context = {'page': page, 'status': status}
    return render(request, 'payments/payment_admin.html', context)


@admin_required
def payment_export_view(request: HttpRequest):
    transactions = Transaction.objects.select_related('user').order_by('-created_at')
    status = request.GET.get('status', '')
    if status:
        transactions = transactions.filter(status=status)

    rows = [
        [
            t.created_at.strftime('%Y-%m-%d %H:%M'),
            t.user.username,
            t.get_transaction_type_display(),
            t.amount,
            t.get_status_display(),
            t.reference_id or '-',
        ]
        for t in transactions
    ]
    return make_csv_response(
        f'transactions_{status or "all"}.csv',
        ['Date', 'User', 'Type', 'Amount', 'Status', 'Reference'],
        rows
    )
