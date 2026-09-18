"""
Views for the reports module.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q, F
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from accounting.models import (
    Account, AccountType, Transaction, TransactionLine, 
    TaxRate, Journal, JournalEntry, Period
)
from invoices.models import Invoice, Payment, InvoiceType
from contacts.models import Contact
from .models import ReportTemplate, SavedReport


@login_required
def balance_sheet(request):
    """Generate balance sheet (Bilanz)."""
    # Get current date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        # Default to current fiscal year
        today = date.today()
        date_from = date(today.year, 1, 1)
        date_to = date(today.year, 12, 31)
    else:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    
    # Get all accounts
    asset_accounts = Account.objects.filter(
        account_type__is_asset=True,
        is_active=True
    ).order_by('account_number')
    
    liability_accounts = Account.objects.filter(
        Q(account_type__is_liability=True) | Q(account_type__is_income=True),
        is_active=True
    ).order_by('account_number')
    
    # Calculate balances
    assets = []
    total_assets = Decimal('0.00')
    
    for account in asset_accounts:
        balance = account.get_balance(date_from, date_to)
        assets.append({
            'account': account,
            'balance': balance
        })
        total_assets += balance
    
    liabilities = []
    total_liabilities = Decimal('0.00')
    
    for account in liability_accounts:
        balance = account.get_balance(date_from, date_to)
        liabilities.append({
            'account': account,
            'balance': balance
        })
        total_liabilities += balance
    
    # Calculate equity
    total_equity = total_assets - total_liabilities
    
    context = {
        'page_title': 'Bilanz',
        'date_from': date_from,
        'date_to': date_to,
        'assets': assets,
        'liabilities': liabilities,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_equity,
        'is_balanced': total_assets == total_liabilities + total_equity,
    }
    
    return render(request, 'reports/balance_sheet.html', context)


@login_required
def profit_loss(request):
    """Generate profit and loss statement (GuV)."""
    # Get current date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        # Default to current year
        today = date.today()
        date_from = date(today.year, 1, 1)
        date_to = date(today.year, 12, 31)
    else:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    
    # Get income and expense accounts
    income_accounts = Account.objects.filter(
        account_type__is_income=True,
        is_active=True
    ).order_by('account_number')
    
    expense_accounts = Account.objects.filter(
        account_type__is_expense=True,
        is_active=True
    ).order_by('account_number')
    
    # Calculate income totals
    income_items = []
    total_income = Decimal('0.00')
    
    for account in income_accounts:
        balance = account.get_balance(date_from, date_to)
        # For income accounts, credit balance is positive
        credit_total = account.transaction_lines.filter(
            transaction__date__gte=date_from,
            transaction__date__lte=date_to,
            side='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        debit_total = account.transaction_lines.filter(
            transaction__date__gte=date_from,
            transaction__date__lte=date_to,
            side='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_income = credit_total - debit_total
        
        income_items.append({
            'account': account,
            'amount': net_income
        })
        total_income += net_income
    
    # Calculate expense totals
    expense_items = []
    total_expenses = Decimal('0.00')
    
    for account in expense_accounts:
        debit_total = account.transaction_lines.filter(
            transaction__date__gte=date_from,
            transaction__date__lte=date_to,
            side='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        credit_total = account.transaction_lines.filter(
            transaction__date__gte=date_from,
            transaction__date__lte=date_to,
            side='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        net_expense = debit_total - credit_total
        
        expense_items.append({
            'account': account,
            'amount': net_expense
        })
        total_expenses += net_expense
    
    # Calculate net profit/loss
    net_profit = total_income - total_expenses
    
    context = {
        'page_title': 'Gewinn- und Verlustrechnung (GuV)',
        'date_from': date_from,
        'date_to': date_to,
        'income_items': income_items,
        'expense_items': expense_items,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'is_profitable': net_profit >= 0,
    }
    
    return render(request, 'reports/profit_loss.html', context)


@login_required
def tax_report(request):
    """Generate tax report."""
    # Get current date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        # Default to current year
        today = date.today()
        date_from = date(today.year, 1, 1)
        date_to = date(today.year, 12, 31)
    else:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    
    # Get tax rates
    tax_rates = TaxRate.objects.filter(is_active=True)
    
    # Calculate tax by rate
    tax_by_rate = []
    total_tax = Decimal('0.00')
    
    for tax_rate in tax_rates:
        # Get all transaction lines with this tax rate
        lines = TransactionLine.objects.filter(
            tax_rate=tax_rate,
            transaction__date__gte=date_from,
            transaction__date__lte=date_to
        )
        
        tax_amount = lines.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
        base_amount = lines.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        tax_by_rate.append({
            'tax_rate': tax_rate,
            'base_amount': base_amount,
            'tax_amount': tax_amount
        })
        total_tax += tax_amount
    
    # Get input and output tax separately
    input_vat = TaxRate.objects.filter(tax_type='input_vat', is_active=True).first()
    output_vat = TaxRate.objects.filter(tax_type='vat', is_active=True).first()
    
    input_vat_amount = Decimal('0.00')
    output_vat_amount = Decimal('0.00')
    
    if input_vat:
        input_vat_amount = TransactionLine.objects.filter(
            tax_rate=input_vat,
            transaction__date__gte=date_from,
            transaction__date__lte=date_to
        ).aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
    
    if output_vat:
        output_vat_amount = TransactionLine.objects.filter(
            tax_rate=output_vat,
            transaction__date__gte=date_from,
            transaction__date__lte=date_to
        ).aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')
    
    # Net tax (to pay or to receive)
    net_tax = output_vat_amount - input_vat_amount
    
    context = {
        'page_title': 'Steuerbericht',
        'date_from': date_from,
        'date_to': date_to,
        'tax_by_rate': tax_by_rate,
        'total_tax': total_tax,
        'input_vat_amount': input_vat_amount,
        'output_vat_amount': output_vat_amount,
        'net_tax': net_tax,
        'tax_to_pay': net_tax > 0,
    }
    
    return render(request, 'reports/tax_report.html', context)


@login_required
def account_statement(request, account_id=None):
    """Generate account statement."""
    # Get account
    if account_id:
        account = get_object_or_404(Account, pk=account_id)
    else:
        # Get first active account
        account = Account.objects.filter(is_active=True).first()
        if not account:
            return render(request, 'reports/account_statement.html', {
                'page_title': 'Kontoauszug',
                'error': 'Keine Konten gefunden'
            })
    
    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        # Default to current year
        today = date.today()
        date_from = date(today.year, 1, 1)
        date_to = date(today.year, 12, 31)
    else:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    
    # Get transactions for this account
    transactions = TransactionLine.objects.filter(
        account=account,
        transaction__date__gte=date_from,
        transaction__date__lte=date_to
    ).select_related('transaction').order_by('transaction__date', 'transaction__document_number')
    
    # Calculate running balance
    running_balance = Decimal('0.00')
    transactions_with_balance = []
    
    for line in transactions:
        if line.side == 'debit':
            running_balance += line.amount
        else:
            running_balance -= line.amount
        
        transactions_with_balance.append({
            'line': line,
            'running_balance': running_balance
        })
    
    # Get opening and closing balance
    opening_balance = account.get_balance(date_from - timedelta(days=1))
    closing_balance = account.get_balance(date_to)
    
    context = {
        'page_title': f"Kontoauszug - {account.account_number}",
        'account': account,
        'date_from': date_from,
        'date_to': date_to,
        'transactions': transactions_with_balance,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'all_accounts': Account.objects.filter(is_active=True).order_by('account_number'),
    }
    
    return render(request, 'reports/account_statement.html', context)


@login_required
def general_ledger_report(request):
    """Generate general ledger report."""
    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        # Default to current year
        today = date.today()
        date_from = date(today.year, 1, 1)
        date_to = date(today.year, 12, 31)
    else:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    
    # Get all transactions in date range
    transactions = Transaction.objects.filter(
        date__gte=date_from,
        date__lte=date_to
    ).select_related('document_type', 'created_by').prefetch_related(
        'lines__account', 'lines__tax_rate'
    ).order_by('date', 'document_number')
    
    context = {
        'page_title': 'Hauptbuch',
        'date_from': date_from,
        'date_to': date_to,
        'transactions': transactions,
    }
    
    return render(request, 'reports/general_ledger.html', context)


@login_required
def trial_balance_report(request):
    """Generate trial balance report."""
    # Get date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if not date_from or not date_to:
        # Default to current year
        today = date.today()
        date_from = date(today.year, 1, 1)
        date_to = date(today.year, 12, 31)
    else:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    
    # Get all accounts
    accounts = Account.objects.filter(is_active=True).order_by('account_number')
    
    # Calculate balances
    account_data = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    
    for account in accounts:
        debit_total = account.transaction_lines.filter(
            transaction__date__gte=date_from,
            transaction__date__lte=date_to,
            side='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        credit_total = account.transaction_lines.filter(
            transaction__date__gte=date_from,
            transaction__date__lte=date_to,
            side='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        balance = debit_total - credit_total
        
        account_data.append({
            'account': account,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'balance': balance
        })
        
        total_debit += debit_total
        total_credit += credit_total
    
    context = {
        'page_title': 'Summen- und Saldenliste',
        'date_from': date_from,
        'date_to': date_to,
        'account_data': account_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
    }
    
    return render(request, 'reports/trial_balance.html', context)


@login_required
def aging_report(request):
    """Generate accounts receivable aging report."""
    # Get date for aging calculation
    report_date = request.GET.get('report_date')
    if not report_date:
        report_date = date.today()
    else:
        report_date = date.fromisoformat(report_date)
    
    # Get open invoices
    open_invoices = Invoice.objects.filter(
        created_by=request.user,
        status__is_final=False,
        paid_amount__lt=F('total_amount')
    ).select_related('customer').order_by('due_date')
    
    # Aging buckets (0-30, 31-60, 61-90, 90+ days)
    aging_buckets = [
        {'name': '0-30 Tage', 'days': 30, 'invoices': [], 'total': Decimal('0.00')},
        {'name': '31-60 Tage', 'days': 60, 'invoices': [], 'total': Decimal('0.00')},
        {'name': '61-90 Tage', 'days': 90, 'invoices': [], 'total': Decimal('0.00')},
        {'name': '90+ Tage', 'days': 9999, 'invoices': [], 'total': Decimal('0.00')},
    ]
    
    for invoice in open_invoices:
        if not invoice.due_date:
            continue
        
        days_overdue = (report_date - invoice.due_date).days
        
        for bucket in aging_buckets:
            if days_overdue <= bucket['days']:
                balance = invoice.get_balance()
                bucket['invoices'].append({
                    'invoice': invoice,
                    'days_overdue': days_overdue,
                    'balance': balance
                })
                bucket['total'] += balance
                break
    
    # Calculate totals
    total_open = sum(bucket['total'] for bucket in aging_buckets)
    
    context = {
        'page_title': 'Altersstruktur der Forderungen',
        'report_date': report_date,
        'aging_buckets': aging_buckets,
        'total_open': total_open,
    }
    
    return render(request, 'reports/aging_report.html', context)


@login_required
def dashboard_report(request):
    """Generate dashboard with key metrics."""
    # Get current year
    current_year = date.today().year
    
    # Get financial data
    total_invoices = Invoice.objects.filter(
        created_by=request.user,
        date__year=current_year
    ).count()
    
    total_invoice_amount = Invoice.objects.filter(
        created_by=request.user,
        date__year=current_year
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_paid = Invoice.objects.filter(
        created_by=request.user,
        date__year=current_year
    ).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
    
    total_transactions = Transaction.objects.filter(
        created_by=request.user,
        date__year=current_year
    ).count()
    
    # Get monthly data
    monthly_data = []
    for month in range(1, 13):
        month_start = date(current_year, month, 1)
        if month == 12:
            month_end = date(current_year, 12, 31)
        else:
            month_end = date(current_year, month + 1, 1) - timedelta(days=1)
        
        invoices = Invoice.objects.filter(
            created_by=request.user,
            date__gte=month_start,
            date__lte=month_end
        ).aggregate(
            count=Sum('id'),
            total=Sum('total_amount')
        )
        
        payments = Payment.objects.filter(
            invoice__created_by=request.user,
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))
        
        monthly_data.append({
            'month': month,
            'invoice_count': invoices['count'] or 0,
            'invoice_total': invoices['total'] or Decimal('0.00'),
            'payment_total': payments['total'] or Decimal('0.00')
        })
    
    context = {
        'page_title': 'Finanz-Dashboard',
        'current_year': current_year,
        'total_invoices': total_invoices,
        'total_invoice_amount': total_invoice_amount,
        'total_paid': total_paid,
        'total_transactions': total_transactions,
        'monthly_data': monthly_data,
    }
    
    return render(request, 'reports/dashboard_report.html', context)


@login_required
def report_template_list(request):
    """List all report templates."""
    templates = ReportTemplate.objects.filter(
        Q(created_by=request.user) | Q(created_by__isnull=True)
    )
    
    context = {
        'page_title': 'Berichtsvorlagen',
        'templates': templates,
    }
    
    return render(request, 'reports/report_template_list.html', context)


@login_required
def saved_report_list(request):
    """List all saved reports."""
    reports = SavedReport.objects.filter(generated_by=request.user).order_by('-generated_at')
    
    context = {
        'page_title': 'Gespeicherte Berichte',
        'reports': reports,
    }
    
    return render(request, 'reports/saved_report_list.html', context)
