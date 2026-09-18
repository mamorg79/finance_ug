"""
Invoice models for the accounting system.
Implements invoice creation, management, and integration with accounting.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.auth.models import User
from decimal import Decimal
import uuid

from accounting.models import Account, TaxRate, Transaction
from contacts.models import Contact


class InvoiceStatus(models.Model):
    """Status options for invoices."""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_final = models.BooleanField(default=False, help_text="Endgültiger Status")
    sort_order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Rechnungsstatus"
        verbose_name_plural = "Rechnungsstatus"
        ordering = ['sort_order']


class InvoiceType(models.Model):
    """Types of invoices."""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_credit_note = models.BooleanField(default=False, help_text="Gutschrift")
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Rechnungstyp"
        verbose_name_plural = "Rechnungstypen"


class PaymentTerm(models.Model):
    """Payment terms for invoices."""
    name = models.CharField(max_length=100, unique=True)
    days = models.PositiveIntegerField(default=14, help_text="Zahlungsziel in Tagen")
    description = models.TextField(blank=True)
    discount_days = models.PositiveIntegerField(
        default=0,
        help_text="Tage für Skonto",
        blank=True,
        null=True
    )
    discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Skonto in %",
        blank=True,
        null=True
    )
    
    def __str__(self):
        return f"{self.name} ({self.days} Tage)"
    
    class Meta:
        verbose_name = "Zahlungsbedingung"
        verbose_name_plural = "Zahlungsbedingungen"


class Invoice(models.Model):
    """Main invoice model."""
    invoice_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Rechnungsnummer"
    )
    invoice_type = models.ForeignKey(
        InvoiceType,
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="Rechnungstyp"
    )
    status = models.ForeignKey(
        InvoiceStatus,
        on_delete=models.PROTECT,
        related_name='invoices',
        default=1,
        help_text="Status"
    )
    
    # Customer/Supplier
    customer = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='invoices_as_customer',
        help_text="Kunde/Lieferant"
    )
    
    # Dates
    date = models.DateField(help_text="Rechnungsdatum")
    due_date = models.DateField(
        help_text="Fälligkeitsdatum",
        null=True,
        blank=True
    )
    payment_date = models.DateField(
        help_text="Zahlungsdatum",
        null=True,
        blank=True
    )
    
    # Financial data
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Nettobetrag"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Steuerbetrag"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Gesamtbetrag"
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Gezahlter Betrag"
    )
    
    # Payment terms
    payment_term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Zahlungsbedingung"
    )
    
    # Reference and notes
    reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Referenz (z.B. Bestellnummer)"
    )
    internal_notes = models.TextField(
        blank=True,
        help_text="Interne Notizen"
    )
    customer_notes = models.TextField(
        blank=True,
        help_text="Notizen für den Kunden"
    )
    
    # Accounting integration
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='invoices_as_revenue',
        help_text="Ertragskonto",
        null=True,
        blank=True
    )
    tax_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='invoices_as_tax',
        help_text="Steuerkonto",
        null=True,
        blank=True
    )
    receivable_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='invoices_as_receivable',
        help_text="Forderungskonto",
        null=True,
        blank=True
    )
    
    # Transaction reference
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice',
        help_text="Verknüpfte Buchung"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # File attachments
    pdf_file = models.FileField(
        upload_to='invoices/pdfs/',
        blank=True,
        null=True,
        help_text="PDF-Datei"
    )
    
    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"
    
    def get_status_display(self):
        return self.status.name
    
    def is_paid(self):
        return self.paid_amount >= self.total_amount
    
    def is_overdue(self):
        if self.due_date and not self.is_paid():
            from django.utils import timezone
            return self.due_date < timezone.now().date()
        return False
    
    def get_balance(self):
        """Get remaining balance to be paid."""
        return self.total_amount - self.paid_amount
    
    def calculate_totals(self):
        """Calculate invoice totals from lines."""
        from django.db.models import Sum
        
        lines = self.lines.all()
        self.subtotal = lines.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        self.tax_amount = lines.aggregate(
            total=Sum('tax_amount')
        )['total'] or Decimal('0.00')
        
        self.total_amount = self.subtotal + self.tax_amount
        self.save()
    
    def create_transaction(self):
        """Create accounting transaction for this invoice."""
        if self.transaction:
            return self.transaction
        
        # Create transaction
        transaction = Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            document_number=f"RE-{self.invoice_number}",
            date=self.date,
            posting_date=self.date,
            document_type_id=1,  # Should be linked to a document type
            description=f"Rechnung {self.invoice_number} - {self.customer.name}",
            reference=self.reference or self.invoice_number,
            created_by=self.created_by,
            is_posted=False
        )
        
        # Create transaction lines
        # Line 1: Receivable (debit)
        if self.receivable_account:
            TransactionLine.objects.create(
                transaction=transaction,
                account=self.receivable_account,
                side='debit',
                amount=self.total_amount,
                description=f"Forderung aus Rechnung {self.invoice_number}"
            )
        
        # Line 2: Revenue (credit)
        if self.revenue_account:
            TransactionLine.objects.create(
                transaction=transaction,
                account=self.revenue_account,
                side='credit',
                amount=self.subtotal,
                description=f"Ertrag aus Rechnung {self.invoice_number}"
            )
        
        # Line 3: Tax (credit)
        if self.tax_account:
            TransactionLine.objects.create(
                transaction=transaction,
                account=self.tax_account,
                side='credit',
                amount=self.tax_amount,
                description=f"Umsatzsteuer aus Rechnung {self.invoice_number}"
            )
        
        # Save transaction reference
        self.transaction = transaction
        self.save()
        
        return transaction
    
    class Meta:
        verbose_name = "Rechnung"
        verbose_name_plural = "Rechnungen"
        ordering = ['-date', '-invoice_number']


class InvoiceLine(models.Model):
    """Individual line item in an invoice."""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField(default=1)
    description = models.TextField(help_text="Beschreibung")
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.00,
        validators=[MinValueValidator(Decimal('0.0001'))],
        help_text="Menge"
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Einzelpreis"
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.PROTECT,
        related_name='invoice_lines',
        null=True,
        blank=True,
        help_text="Steuersatz"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Betrag (netto)"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Steuerbetrag"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_lines',
        help_text="Konto"
    )
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Kostenstelle"
    )
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - Zeile {self.line_number}"
    
    def calculate_amount(self):
        """Calculate line amount."""
        self.amount = self.quantity * self.unit_price
        
        if self.tax_rate:
            self.tax_amount = self.amount * (self.tax_rate.rate / Decimal('100'))
        else:
            self.tax_amount = Decimal('0.00')
        
        return self.amount
    
    def save(self, *args, **kwargs):
        """Override save to calculate amount."""
        if self.quantity and self.unit_price:
            self.amount = self.quantity * self.unit_price
        
        if self.tax_rate and self.amount:
            self.tax_amount = self.amount * (self.tax_rate.rate / Decimal('100'))
        
        super().save(*args, **kwargs)
        
        # Update invoice totals
        self.invoice.calculate_totals()
    
    class Meta:
        verbose_name = "Rechnungsposition"
        verbose_name_plural = "Rechnungspositionen"
        ordering = ['invoice', 'line_number']
        unique_together = ['invoice', 'line_number']


class Payment(models.Model):
    """Payment record for invoices."""
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Zahlungsbetrag"
    )
    payment_date = models.DateField(help_text="Zahlungsdatum")
    payment_method = models.CharField(
        max_length=50,
        choices=[
            ('bank_transfer', 'Überweisung'),
            ('cash', 'Barzahlung'),
            ('credit_card', 'Kreditkarte'),
            ('debit_card', 'EC-Karte'),
            ('paypal', 'PayPal'),
            ('other', 'Sonstiges'),
        ],
        help_text="Zahlungsart"
    )
    reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Referenz (z.B. Überweisungsvermerk)"
    )
    notes = models.TextField(blank=True, help_text="Notizen")
    
    # Accounting integration
    bank_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text="Bankkonto"
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment',
        help_text="Verknüpfte Buchung"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_payments'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Zahlung {self.payment_id} für Rechnung {self.invoice.invoice_number}"
    
    def create_transaction(self):
        """Create accounting transaction for this payment."""
        if self.transaction:
            return self.transaction
        
        # Create transaction
        transaction = Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            document_number=f"ZA-{self.invoice.invoice_number}-{self.payment_id}",
            date=self.payment_date,
            posting_date=self.payment_date,
            document_type_id=1,
            description=f"Zahlungseingang für Rechnung {self.invoice.invoice_number}",
            reference=self.reference or f"Zahlung {self.payment_id}",
            created_by=self.created_by,
            is_posted=False
        )
        
        # Create transaction lines
        # Line 1: Bank (debit)
        if self.bank_account:
            TransactionLine.objects.create(
                transaction=transaction,
                account=self.bank_account,
                side='debit',
                amount=self.amount,
                description=f"Zahlungseingang für Rechnung {self.invoice.invoice_number}"
            )
        
        # Line 2: Receivable (credit)
        if self.invoice.receivable_account:
            TransactionLine.objects.create(
                transaction=transaction,
                account=self.invoice.receivable_account,
                side='credit',
                amount=self.amount,
                description=f"Ausgleich Forderung Rechnung {self.invoice.invoice_number}"
            )
        
        # Save transaction reference
        self.transaction = transaction
        self.save()
        
        # Update invoice paid amount
        self.invoice.paid_amount += self.amount
        self.invoice.save()
        
        return transaction
    
    class Meta:
        verbose_name = "Zahlung"
        verbose_name_plural = "Zahlungen"
        ordering = ['-payment_date', '-created_at']


class RecurringInvoice(models.Model):
    """Template for recurring invoices."""
    template_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200, help_text="Name der Vorlage")
    customer = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='recurring_invoices',
        help_text="Kunde"
    )
    
    # Recurrence settings
    recurrence_type = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Täglich'),
            ('weekly', 'Wöchentlich'),
            ('monthly', 'Monatlich'),
            ('quarterly', 'Quartalsweise'),
            ('yearly', 'Jährlich'),
        ],
        default='monthly',
        help_text="Wiederholung"
    )
    recurrence_interval = models.PositiveIntegerField(
        default=1,
        help_text="Intervall (z.B. alle 2 Monate)"
    )
    start_date = models.DateField(help_text="Startdatum")
    end_date = models.DateField(
        help_text="Enddatum",
        null=True,
        blank=True
    )
    next_invoice_date = models.DateField(
        help_text="Nächstes Rechnungsdatum",
        null=True,
        blank=True
    )
    
    # Invoice template data
    invoice_type = models.ForeignKey(
        InvoiceType,
        on_delete=models.PROTECT,
        related_name='recurring_invoice_templates',
        help_text="Rechnungstyp"
    )
    payment_term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_invoice_templates',
        help_text="Zahlungsbedingung"
    )
    
    # Accounting accounts
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='recurring_invoice_templates_as_revenue',
        help_text="Ertragskonto",
        null=True,
        blank=True
    )
    tax_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='recurring_invoice_templates_as_tax',
        help_text="Steuerkonto",
        null=True,
        blank=True
    )
    receivable_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='recurring_invoice_templates_as_receivable',
        help_text="Forderungskonto",
        null=True,
        blank=True
    )
    
    # Status
    is_active = models.BooleanField(default=True, help_text="Aktiv")
    auto_send = models.BooleanField(
        default=False,
        help_text="Automatisch senden"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_recurring_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.customer.name}"
    
    class Meta:
        verbose_name = "Wiederkehrende Rechnung"
        verbose_name_plural = "Wiederkehrende Rechnungen"


class RecurringInvoiceLine(models.Model):
    """Line item template for recurring invoices."""
    template = models.ForeignKey(
        RecurringInvoice,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField(default=1)
    description = models.TextField(help_text="Beschreibung")
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=1.00,
        help_text="Menge"
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Einzelpreis"
    )
    tax_rate = models.ForeignKey(
        TaxRate,
        on_delete=models.PROTECT,
        related_name='recurring_invoice_lines',
        null=True,
        blank=True,
        help_text="Steuersatz"
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recurring_invoice_lines',
        help_text="Konto"
    )
    cost_center = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Kostenstelle"
    )
    
    def __str__(self):
        return f"{self.template.name} - Zeile {self.line_number}"
    
    class Meta:
        verbose_name = "Vorlage für Rechnungsposition"
        verbose_name_plural = "Vorlagen für Rechnungspositionen"
        ordering = ['template', 'line_number']


class InvoiceTemplate(models.Model):
    """Template for creating invoices."""
    template_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200, help_text="Name der Vorlage")
    description = models.TextField(blank=True, help_text="Beschreibung")
    
    # Default values
    invoice_type = models.ForeignKey(
        InvoiceType,
        on_delete=models.PROTECT,
        related_name='invoice_templates',
        null=True,
        blank=True,
        help_text="Standard-Rechnungstyp"
    )
    payment_term = models.ForeignKey(
        PaymentTerm,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_templates',
        help_text="Standard-Zahlungsbedingung"
    )
    revenue_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_templates_as_revenue',
        help_text="Standard-Ertragskonto"
    )
    tax_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_templates_as_tax',
        help_text="Standard-Steuerkonto"
    )
    receivable_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoice_templates_as_receivable',
        help_text="Standard-Forderungskonto"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoice_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Rechnungsvorlage"
        verbose_name_plural = "Rechnungsvorlagen"
