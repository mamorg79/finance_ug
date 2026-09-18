"""
Views for the accounting module.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import uuid

from .models import (
    Account, AccountType, ChartOfAccounts, TaxRate, DocumentType,
    Transaction, TransactionLine, Journal, JournalEntry, Period,
    Reconciliation
)
from .forms import (
    TransactionForm, TransactionLineForm, AccountForm, 
    ReconciliationForm, PeriodForm
)
from contacts.models import Contact
from invoices.models import Invoice


@login_required
def dashboard(request):
    """Main accounting dashboard."""
    # Get current balances
    accounts = Account.objects.filter(is_active=True)
    
    # Calculate total assets and liabilities
    asset_accounts = accounts.filter(account_type__is_asset=True)
    liability_accounts = accounts.filter(account_type__is_liability=True)
    income_accounts = accounts.filter(account_type__is_income=True)
    expense_accounts = accounts.filter(account_type__is_expense=True)
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        created_by=request.user
    ).order_by('-date', '-document_number')[:10]
    
    # Get account balances
    account_balances = []
    for account in accounts[:10]:
        balance = account.get_balance()
        account_balances.append({
            'account': account,
            'balance': balance
        })
    
    # Calculate totals
    total_assets = sum(
        acc.get_balance() for acc in asset_accounts
    )
    total_liabilities = sum(
        acc.get_balance() for acc in liability_accounts
    )
    
    context = {
        'page_title': 'Buchhaltungs-Dashboard',
        'recent_transactions': recent_transactions,
        'account_balances': account_balances,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'total_equity': total_assets - total_liabilities,
        'asset_accounts': asset_accounts.count(),
        'liability_accounts': liability_accounts.count(),
        'income_accounts': income_accounts.count(),
        'expense_accounts': expense_accounts.count(),
    }
    
    return render(request, 'accounting/dashboard.html', context)


@login_required
def account_list(request):
    """List all accounts."""
    accounts = Account.objects.filter(is_active=True).order_by('account_number')
    
    # Filter by account type
    account_type = request.GET.get('type')
    if account_type:
        accounts = accounts.filter(account_type__code=account_type)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        accounts = accounts.filter(
            Q(account_number__icontains=search_query) | 
            Q(name__icontains=search_query)
        )
    
    paginator = Paginator(accounts, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Kontenliste',
        'accounts': page_obj,
        'account_types': AccountType.objects.all(),
        'selected_type': account_type,
        'search_query': search_query,
    }
    
    return render(request, 'accounting/account_list.html', context)


@login_required
def account_detail(request, account_id):
    """Show account details with transactions."""
    account = get_object_or_404(Account, pk=account_id)
    
    # Get transactions for this account
    transactions = TransactionLine.objects.filter(
        account=account
    ).select_related('transaction').order_by(
        '-transaction__date', '-transaction__document_number'
    )
    
    # Calculate balance
    balance = account.get_balance()
    
    # Get recent transactions
    recent_transactions = transactions[:20]
    
    context = {
        'page_title': f"Konto {account.account_number}",
        'account': account,
        'balance': balance,
        'transactions': recent_transactions,
    }
    
    return render(request, 'accounting/account_detail.html', context)


@login_required
def account_create(request):
    """Create a new account."""
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            account = form.save(commit=False)
            account.created_by = request.user
            account.save()
            messages.success(request, 'Konto erfolgreich erstellt!')
            return redirect('accounting:account_list')
    else:
        form = AccountForm()
    
    context = {
        'page_title': 'Neues Konto erstellen',
        'form': form,
    }
    
    return render(request, 'accounting/account_form.html', context)


@login_required
def account_update(request, account_id):
    """Update an existing account."""
    account = get_object_or_404(Account, pk=account_id)
    
    if request.method == 'POST':
        form = AccountForm(request.POST, instance=account)
        if form.is_valid():
            form.save()
            messages.success(request, 'Konto erfolgreich aktualisiert!')
            return redirect('accounting:account_detail', account_id=account.id)
    else:
        form = AccountForm(instance=account)
    
    context = {
        'page_title': f"Konto {account.account_number} bearbeiten",
        'form': form,
        'account': account,
    }
    
    return render(request, 'accounting/account_form.html', context)


@login_required
def transaction_list(request):
    """List all transactions."""
    transactions = Transaction.objects.filter(
        created_by=request.user
    ).order_by('-date', '-document_number')
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        transactions = transactions.filter(date__gte=date_from)
    if date_to:
        transactions = transactions.filter(date__lte=date_to)
    
    # Filter by document type
    doc_type = request.GET.get('doc_type')
    if doc_type:
        transactions = transactions.filter(document_type__code=doc_type)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        transactions = transactions.filter(
            Q(document_number__icontains=search_query) | 
            Q(description__icontains=search_query) | 
            Q(reference__icontains=search_query)
        )
    
    paginator = Paginator(transactions, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Buchungsliste',
        'transactions': page_obj,
        'document_types': DocumentType.objects.all(),
        'selected_doc_type': doc_type,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'accounting/transaction_list.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """Show transaction details."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    context = {
        'page_title': f"Buchung {transaction.document_number}",
        'transaction': transaction,
        'lines': transaction.lines.all().order_by('line_number'),
    }
    
    return render(request, 'accounting/transaction_detail.html', context)


@login_required
def transaction_create(request):
    """Create a new transaction."""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        line_form = TransactionLineForm(request.POST, prefix='line')
        
        if form.is_valid() and line_form.is_valid():
            # Create transaction
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.transaction_id = uuid.uuid4()
            
            # Generate document number
            if not transaction.document_number:
                last_transaction = Transaction.objects.filter(
                    created_by=request.user
                ).order_by('-document_number').first()
                
                if last_transaction:
                    try:
                        last_num = int(last_transaction.document_number.split('-')[-1])
                        transaction.document_number = f"BKG-{last_num + 1:06d}"
                    except:
                        transaction.document_number = "BKG-000001"
                else:
                    transaction.document_number = "BKG-000001"
            
            transaction.save()
            
            # Create line
            line = line_form.save(commit=False)
            line.transaction = transaction
            line.line_number = 1
            line.save()
            
            messages.success(request, 'Buchung erfolgreich erstellt!')
            return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    else:
        form = TransactionForm(initial={
            'date': timezone.now().date(),
            'posting_date': timezone.now().date(),
        })
        line_form = TransactionLineForm(prefix='line')
    
    context = {
        'page_title': 'Neue Buchung erstellen',
        'form': form,
        'line_form': line_form,
    }
    
    return render(request, 'accounting/transaction_form.html', context)


@login_required
def transaction_update(request, transaction_id):
    """Update an existing transaction."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if transaction.is_posted:
        messages.error(request, 'Gebuchte Buchungen können nicht bearbeitet werden!')
        return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        
        if form.is_valid():
            transaction = form.save()
            messages.success(request, 'Buchung erfolgreich aktualisiert!')
            return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    else:
        form = TransactionForm(instance=transaction)
    
    context = {
        'page_title': f"Buchung {transaction.document_number} bearbeiten",
        'form': form,
        'transaction': transaction,
    }
    
    return render(request, 'accounting/transaction_form.html', context)


@login_required
def transaction_delete(request, transaction_id):
    """Delete a transaction."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if transaction.is_posted:
        messages.error(request, 'Gebuchte Buchungen können nicht gelöscht werden!')
        return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Buchung erfolgreich gelöscht!')
        return redirect('accounting:transaction_list')
    
    context = {
        'page_title': f"Buchung {transaction.document_number} löschen",
        'transaction': transaction,
    }
    
    return render(request, 'accounting/transaction_confirm_delete.html', context)


@login_required
def transaction_post(request, transaction_id):
    """Post a transaction (make it final)."""
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if transaction.is_posted:
        messages.warning(request, 'Diese Buchung ist bereits gebucht!')
        return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    
    if not transaction.is_balanced():
        messages.error(request, 'Buchung muss ausgeglichen sein (Soll = Haben)!')
        return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    
    if request.method == 'POST':
        transaction.is_posted = True
        transaction.save()
        
        # Update account balances
        for line in transaction.lines.all():
            line.account.update_current_balance()
        
        messages.success(request, 'Buchung erfolgreich gebucht!')
        return redirect('accounting:transaction_detail', transaction_id=transaction.id)
    
    context = {
        'page_title': f"Buchung {transaction.document_number} buchen",
        'transaction': transaction,
    }
    
    return render(request, 'accounting/transaction_confirm_post.html', context)


@login_required
def transaction_reverse(request, transaction_id):
    """Reverse a posted transaction."""
    original_transaction = get_object_or_404(Transaction, pk=transaction_id)
    
    if not original_transaction.is_posted:
        messages.error(request, 'Nur gebuchte Buchungen können storniert werden!')
        return redirect('accounting:transaction_detail', transaction_id=original_transaction.id)
    
    if original_transaction.is_reversed:
        messages.warning(request, 'Diese Buchung ist bereits storniert!')
        return redirect('accounting:transaction_detail', transaction_id=original_transaction.id)
    
    if request.method == 'POST':
        # Create reversal transaction
        reversal = Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            document_number=f"STORNO-{original_transaction.document_number}",
            date=timezone.now().date(),
            posting_date=timezone.now().date(),
            document_type=original_transaction.document_type,
            description=f"Stornierung: {original_transaction.description}",
            reference=f"Storniert Buchung {original_transaction.document_number}",
            created_by=request.user,
            is_posted=True,
            is_reversed=True,
            reversal_reference=original_transaction,
        )
        
        # Create reversed lines
        for line in original_transaction.lines.all():
            TransactionLine.objects.create(
                transaction=reversal,
                account=line.account,
                side='credit' if line.side == 'debit' else 'debit',
                amount=line.amount,
                tax_rate=line.tax_rate,
                tax_amount=line.tax_amount,
                description=f"Stornierung: {line.description}",
                cost_center=line.cost_center,
                line_number=line.line_number,
            )
        
        # Mark original as reversed
        original_transaction.is_reversed = True
        original_transaction.save()
        
        # Update account balances
        for line in reversal.lines.all():
            line.account.update_current_balance()
        
        messages.success(request, 'Buchung erfolgreich storniert!')
        return redirect('accounting:transaction_detail', transaction_id=reversal.id)
    
    context = {
        'page_title': f"Buchung {original_transaction.document_number} stornieren",
        'transaction': original_transaction,
    }
    
    return render(request, 'accounting/transaction_confirm_reverse.html', context)


@login_required
def journal_list(request):
    """List all journals."""
    journals = Journal.objects.filter(is_active=True)
    
    context = {
        'page_title': 'Journale',
        'journals': journals,
    }
    
    return render(request, 'accounting/journal_list.html', context)


@login_required
def journal_detail(request, journal_id):
    """Show journal details with entries."""
    journal = get_object_or_404(Journal, pk=journal_id)
    entries = JournalEntry.objects.filter(journal=journal).order_by('-date', '-entry_number')
    
    context = {
        'page_title': f"Journal {journal.code}",
        'journal': journal,
        'entries': entries,
    }
    
    return render(request, 'accounting/journal_detail.html', context)


@login_required
def period_list(request):
    """List all accounting periods."""
    periods = Period.objects.all().order_by('-start_date')
    
    context = {
        'page_title': 'Buchungsperioden',
        'periods': periods,
    }
    
    return render(request, 'accounting/period_list.html', context)


@login_required
def period_create(request):
    """Create a new accounting period."""
    if request.method == 'POST':
        form = PeriodForm(request.POST)
        if form.is_valid():
            period = form.save()
            messages.success(request, 'Periode erfolgreich erstellt!')
            return redirect('accounting:period_list')
    else:
        form = PeriodForm()
    
    context = {
        'page_title': 'Neue Periode erstellen',
        'form': form,
    }
    
    return render(request, 'accounting/period_form.html', context)


@login_required
def reconciliation_list(request):
    """List all reconciliations."""
    reconciliations = Reconciliation.objects.filter(
        account__is_active=True
    ).order_by('-statement_date')
    
    context = {
        'page_title': 'Abstimmungen',
        'reconciliations': reconciliations,
    }
    
    return render(request, 'accounting/reconciliation_list.html', context)


@login_required
def reconciliation_create(request):
    """Create a new reconciliation."""
    if request.method == 'POST':
        form = ReconciliationForm(request.POST)
        if form.is_valid():
            reconciliation = form.save(commit=False)
            reconciliation.created_by = request.user
            reconciliation.save()
            messages.success(request, 'Abstimmung erfolgreich erstellt!')
            return redirect('accounting:reconciliation_list')
    else:
        form = ReconciliationForm()
    
    context = {
        'page_title': 'Neue Abstimmung erstellen',
        'form': form,
    }
    
    return render(request, 'accounting/reconciliation_form.html', context)


@login_required
def reconciliation_detail(request, reconciliation_id):
    """Show reconciliation details."""
    reconciliation = get_object_or_404(Reconciliation, pk=reconciliation_id)
    
    context = {
        'page_title': f"Abstimmung {reconciliation.account.account_number}",
        'reconciliation': reconciliation,
        'items': reconciliation.items.all(),
    }
    
    return render(request, 'accounting/reconciliation_detail.html', context)


@login_required
def get_account_balance(request, account_id):
    """AJAX endpoint to get account balance."""
    account = get_object_or_404(Account, pk=account_id)
    balance = account.get_balance()
    
    return JsonResponse({
        'balance': str(balance),
        'account_number': account.account_number,
        'account_name': account.name,
    })


@login_required
def trial_balance(request):
    """Show trial balance (Summen- und Saldenliste)."""
    accounts = Account.objects.filter(is_active=True).order_by('account_number')
    
    # Calculate balances for all accounts
    account_data = []
    total_debit = Decimal('0.00')
    total_credit = Decimal('0.00')
    
    for account in accounts:
        balance = account.get_balance()
        
        # Get debit and credit totals separately
        from django.db.models import Sum
        debit_total = account.transaction_lines.filter(
            side='debit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        credit_total = account.transaction_lines.filter(
            side='credit'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        account_data.append({
            'account': account,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'balance': balance,
        })
        
        total_debit += debit_total
        total_credit += credit_total
    
    context = {
        'page_title': 'Summen- und Saldenliste',
        'account_data': account_data,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': total_debit == total_credit,
    }
    
    return render(request, 'accounting/trial_balance.html', context)


@login_required
def general_ledger(request):
    """Show general ledger."""
    transactions = Transaction.objects.filter(
        created_by=request.user
    ).order_by('date', 'document_number').select_related(
        'document_type', 'created_by'
    ).prefetch_related('lines__account')
    
    context = {
        'page_title': 'Hauptbuch',
        'transactions': transactions,
    }
    
    return render(request, 'accounting/general_ledger.html', context)
