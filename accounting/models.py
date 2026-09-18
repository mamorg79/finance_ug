"""
Accounting models for double-entry bookkeeping system.
Implements SKR03/SKR04 chart of accounts and proper accounting rules.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
import uuid


class AccountType(models.Model):
    """Account type classification according to German accounting standards."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_asset = models.BooleanField(default=False, help_text="Aktivkonto")
    is_liability = models.BooleanField(default=False, help_text="Passivkonto")
    is_income = models.BooleanField(default=False, help_text="Ertragskonto")
    is_expense = models.BooleanField(default=False, help_text="Aufwandskonto")
    balance_side = models.CharField(
        max_length=10,
        choices=[
            ('debit', 'Soll'),
            ('credit', 'Haben'),
        ],
        help_text="Normal balance side for this account type"
    )
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "Kontenart"
        verbose_name_plural = "Kontenarten"


class ChartOfAccounts(models.Model):
    """Chart of accounts (SKR03, SKR04, custom)."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "Kontenrahmen"
        verbose_name_plural = "Kontenrahmen"


class Account(models.Model):
    """Individual account in the chart of accounts."""
    account_number = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(9999999999),
        ],
        help_text="Kontonummer (z.B. 0600, 4000, 8000)"
    )
    name = models.CharField(max_length=200)
    chart_of_accounts = models.ForeignKey(
        ChartOfAccounts,
        on_delete=models.PROTECT,
        related_name='accounts'
    )
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name='accounts'
    )
    parent_account = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_accounts',
        help_text="Übergeordnetes Konto für Hierarchie"
    )
    is_active = models.BooleanField(default=True)
    tax_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Steuerschlüssel"
    )
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Kostenstelle"
    )
    notes = models.TextField(blank=True)
    
    # Calculated fields (denormalized for performance)
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Aktueller Saldo"
    )
    
    def __str__(self):
        return f"{self.account_number} - {self.name}"
    
    def get_balance(self, date_from=None, date_to=None):
        """Calculate balance for a specific period."""
        from django.db.models import Sum
        from .models import TransactionLine
        
        queryset = self.transaction_lines.all()
        
        if date_from:
            queryset = queryset.filter(transaction__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(transaction__date__lte=date_to)
        
        # For asset/expense accounts: debit - credit
        # For liability/income accounts: credit - debit
        if self.account_type.balance_side == 'debit':
            balance = (queryset.aggregate(
                total=Sum('amount', filter=models.Q(side='debit'))
            )['total'] or Decimal('0.00')) - (queryset.aggregate(
                total=Sum('amount', filter=models.Q(side='credit'))
            )['total'] or Decimal('0.00'))
        else:
            balance = (queryset.aggregate(
                total=Sum('amount', filter=models.Q(side='credit'))
            )['total'] or Decimal('0.00')) - (queryset.aggregate(
                total=Sum('amount', filter=models.Q(side='debit'))
            )['total'] or Decimal('0.00'))
        
        return balance
    
    def update_current_balance(self):
        """Update the denormalized current_balance field."""
        self.current_balance = self.get_balance()
        self.save(update_fields=['current_balance'])
    
    class Meta:
        verbose_name = "Konto"
        verbose_name_plural = "Konten"
        ordering = ['account_number']


class TaxRate(models.Model):
    """Tax rates for different tax types."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_active = models.BooleanField(default=True)
    tax_type = models.CharField(
        max_length=20,
        choices=[
            ('vat', 'Umsatzsteuer'),
            ('input_vat', 'Vorsteuer'),
            ('other', 'Sonstige'),
        ]
    )
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.rate}%)"
    
    class Meta:
        verbose_name = "Steuersatz"
        verbose_name_plural = "Steuersätze"


class DocumentType(models.Model):
    """Types of accounting documents."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_system = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "Belegart"
        verbose_name_plural = "Belegarten"


class Transaction(models.Model):
    """Accounting transaction (Buchungssatz)."""
    transaction_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    document_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Belegnummer"
    )
    date = models.DateField(help_text="Buchungsdatum")
    posting_date = models.DateField(
        help_text="Wertstellungsdatum",
        null=True,
        blank=True
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name='transactions'
    )
    description = models.TextField(help_text="Buchungstext")
    reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Referenz (z.B. Rechnungsnummer)"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_posted = models.BooleanField(
        default=False,
        help_text="Gebucht (nicht mehr änderbar)"
    )
    is_reversed = models.BooleanField(
        default=False,
        help_text="Storniert"
    )
    reversal_reference = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reversed_by',
        help_text="Referenz zur Stornobuchung"
    )
    
    def __str__(self):
        return f"{self.document_number} - {self.date.strftime('%d.%m.%Y')}"
    
    def get_total_amount(self):
        """Get total amount of the transaction (sum of all lines)."""
        from django.db.models import Sum
        total = self.lines.aggregate(
            total_debit=Sum('amount', filter=models.Q(side='debit')),
            total_credit=Sum('amount', filter=models.Q(side='credit'))
        )
        debit = total['total_debit'] or Decimal('0.00')
        credit = total['total_credit'] or Decimal('0.00')
        return debit, credit
    
    def is_balanced(self):
        """Check if transaction is balanced (debit = credit)."""
        debit, credit = self.get_total_amount()
        return debit == credit
    
    def save(self, *args, **kwargs):
        """Override save to ensure transaction is balanced."""
        if self.pk and self.is_posted:
            # Prevent changes to posted transactions
            raise ValueError("Posted transactions cannot be modified")
        
        if not self.is_balanced():
            raise ValueError("Transaction must be balanced (Soll = Haben)")
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Buchung"
        verbose_name_plural = "Buchungen"
        ordering = ['-date', '-document_number']


class TransactionLine(models.Model):
    """Individual line in a transaction."""
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='transaction_lines'
    )
    side = models.CharField(
        max_length=10,
        choices=[
            ('debit', 'Soll'),
            ('credit', 'Haben'),
        ],
        help_text="Buchungsseite"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Betrag"
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transaction_lines',
        help_text="Steuersatz"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Steuerbetrag"
    )
    description = models.TextField(
        blank=True,
        help_text="Buchungstext für diese Position"
    )
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Kostenstelle"
    )
    line_number = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.transaction.document_number} - {self.account.account_number} ({self.side}) {self.amount}€"
    
    def clean(self):
        """Validate the line before saving."""
        # Check if account type matches side
        if self.account.account_type.balance_side == 'debit':
            # Asset/Expense accounts: debit increases, credit decreases
            if self.side == 'credit' and self.amount > self.account.current_balance:
                raise ValidationError(
                    f"Credit amount cannot exceed current balance for account {self.account.account_number}"
                )
        else:
            # Liability/Income accounts: credit increases, debit decreases
            if self.side == 'debit' and self.amount > self.account.current_balance:
                raise ValidationError(
                    f"Debit amount cannot exceed current balance for account {self.account.account_number}"
                )
    
    class Meta:
        verbose_name = "Buchungsposition"
        verbose_name_plural = "Buchungspositionen"
        ordering = ['transaction', 'line_number']
        unique_together = ['transaction', 'line_number']


class Journal(models.Model):
    """Accounting journal for organizing transactions."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    journal_type = models.CharField(
        max_length=20,
        choices=[
            ('general', 'Hauptbuch'),
            ('sales', 'Verkaufsjournal'),
            ('purchase', 'Einkaufsjournal'),
            ('bank', 'Bankjournal'),
            ('cash', 'Kassajournal'),
        ]
    )
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journale"


class JournalEntry(models.Model):
    """Entry in a specific journal."""
    journal = models.ForeignKey(
        Journal,
        on_delete=models.PROTECT,
        related_name='entries'
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='journal_entry'
    )
    entry_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    
    def __str__(self):
        return f"{self.journal.code} - {self.entry_number}"
    
    class Meta:
        verbose_name = "Journaleintrag"
        verbose_name_plural = "Journaleinträge"
        ordering = ['journal', '-date', '-entry_number']


class Period(models.Model):
    """Accounting period (monthly, quarterly, yearly)."""
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    period_type = models.CharField(
        max_length=20,
        choices=[
            ('month', 'Monat'),
            ('quarter', 'Quartal'),
            ('year', 'Jahr'),
        ]
    )
    fiscal_year = models.PositiveIntegerField()
    
    def __str__(self):
        return f"{self.name} ({self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')})"
    
    class Meta:
        verbose_name = "Periode"
        verbose_name_plural = "Perioden"
        ordering = ['start_date']


class ClosingEntry(models.Model):
    """Closing entries for period end."""
    period = models.ForeignKey(
        Period,
        on_delete=models.PROTECT,
        related_name='closing_entries'
    )
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='closing_entries_from'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='closing_entries_to'
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.TextField()
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closing_entry'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_closing_entries'
    )
    
    def __str__(self):
        return f"Abschluss {self.period.name}: {self.from_account.account_number} -> {self.to_account.account_number}"
    
    class Meta:
        verbose_name = "Abschlussbuchung"
        verbose_name_plural = "Abschlussbuchungen"


class Reconciliation(models.Model):
    """Bank/Account reconciliation."""
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='reconciliations'
    )
    statement_date = models.DateField()
    statement_balance = models.DecimalField(max_digits=15, decimal_places=2)
    reconciled_balance = models.DecimalField(max_digits=15, decimal_places=2)
    difference = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    is_reconciled = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_reconciliations'
    )
    
    def __str__(self):
        return f"Abstimmung {self.account.account_number} - {self.statement_date.strftime('%d.%m.%Y')}"
    
    class Meta:
        verbose_name = "Abstimmung"
        verbose_name_plural = "Abstimmungen"


class ReconciliationItem(models.Model):
    """Individual item in a reconciliation."""
    reconciliation = models.ForeignKey(
        Reconciliation,
        on_delete=models.CASCADE,
        related_name='items'
    )
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name='reconciliation_items'
    )
    statement_line = models.CharField(max_length=200, blank=True)
    is_reconciled = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    def __str__(self):
        return f"{self.reconciliation.account.account_number} - {self.transaction.document_number}"
    
    class Meta:
        verbose_name = "Abstimmungsposition"
        verbose_name_plural = "Abstimmungsposten"
