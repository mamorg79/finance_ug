"""
Forms for the invoices module.
"""
from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Invoice, InvoiceLine, InvoiceStatus, InvoiceType, PaymentTerm,
    Payment, RecurringInvoice, RecurringInvoiceLine, InvoiceTemplate
)
from accounting.models import Account, TaxRate
from contacts.models import Contact


class InvoiceForm(ModelForm):
    """Form for creating and updating invoices."""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['customer'].queryset = Contact.objects.filter(
                created_by=self.user,
                contact_type__is_customer=True
            )
            self.fields['revenue_account'].queryset = Account.objects.filter(
                account_type__is_income=True
            )
            self.fields['tax_account'].queryset = Account.objects.filter(
                account_type__code__in=['TAX', 'VAT']
            )
            self.fields['receivable_account'].queryset = Account.objects.filter(
                account_type__is_asset=True
            )
    
    class Meta:
        model = Invoice
        fields = [
            'invoice_number', 'invoice_type', 'status', 'customer',
            'date', 'due_date', 'payment_term',
            'reference', 'internal_notes', 'customer_notes',
            'revenue_account', 'tax_account', 'receivable_account'
        ]
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Rechnungsnummer'
            }),
            'invoice_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_term': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referenz (z.B. Bestellnummer)'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Interne Notizen'
            }),
            'customer_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notizen für den Kunden'
            }),
            'revenue_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'receivable_account': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'invoice_number': 'Rechnungsnummer',
            'invoice_type': 'Rechnungstyp',
            'status': 'Status',
            'customer': 'Kunde',
            'date': 'Rechnungsdatum',
            'due_date': 'Fälligkeitsdatum',
            'payment_term': 'Zahlungsbedingung',
            'reference': 'Referenz',
            'internal_notes': 'Interne Notizen',
            'customer_notes': 'Notizen für den Kunden',
            'revenue_account': 'Ertragskonto',
            'tax_account': 'Steuerkonto',
            'receivable_account': 'Forderungskonto',
        }


class InvoiceLineForm(ModelForm):
    """Form for invoice lines."""
    
    class Meta:
        model = InvoiceLine
        fields = [
            'description', 'quantity', 'unit_price', 'tax_rate',
            'account', 'cost_center'
        ]
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Beschreibung'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0.0001'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'tax_rate': forms.Select(attrs={
                'class': 'form-select'
            }),
            'account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kostenstelle'
            }),
        }
        labels = {
            'description': 'Beschreibung',
            'quantity': 'Menge',
            'unit_price': 'Einzelpreis',
            'tax_rate': 'Steuersatz',
            'account': 'Konto',
            'cost_center': 'Kostenstelle',
        }


class PaymentForm(ModelForm):
    """Form for creating payments."""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.invoice = kwargs.pop('invoice', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['invoice'].queryset = Invoice.objects.filter(created_by=self.user)
            self.fields['bank_account'].queryset = Account.objects.filter(
                account_type__is_asset=True
            )
        
        if self.invoice:
            self.fields['invoice'].initial = self.invoice
            self.fields['invoice'].disabled = True
    
    class Meta:
        model = Payment
        fields = [
            'invoice', 'amount', 'payment_date', 'payment_method',
            'reference', 'notes', 'bank_account'
        ]
        widgets = {
            'invoice': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referenz (z.B. Überweisungsvermerk)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notizen'
            }),
            'bank_account': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'invoice': 'Rechnung',
            'amount': 'Zahlungsbetrag',
            'payment_date': 'Zahlungsdatum',
            'payment_method': 'Zahlungsart',
            'reference': 'Referenz',
            'notes': 'Notizen',
            'bank_account': 'Bankkonto',
        }


class RecurringInvoiceForm(ModelForm):
    """Form for creating recurring invoices."""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['customer'].queryset = Contact.objects.filter(
                created_by=self.user,
                contact_type__is_customer=True
            )
            self.fields['revenue_account'].queryset = Account.objects.filter(
                account_type__is_income=True
            )
            self.fields['tax_account'].queryset = Account.objects.filter(
                account_type__code__in=['TAX', 'VAT']
            )
            self.fields['receivable_account'].queryset = Account.objects.filter(
                account_type__is_asset=True
            )
    
    class Meta:
        model = RecurringInvoice
        fields = [
            'name', 'customer', 'invoice_type', 'payment_term',
            'recurrence_type', 'recurrence_interval', 'start_date', 'end_date',
            'revenue_account', 'tax_account', 'receivable_account',
            'is_active', 'auto_send'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name der wiederkehrenden Rechnung'
            }),
            'customer': forms.Select(attrs={
                'class': 'form-select'
            }),
            'invoice_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_term': forms.Select(attrs={
                'class': 'form-select'
            }),
            'recurrence_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'recurrence_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'revenue_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'receivable_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'auto_send': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Name',
            'customer': 'Kunde',
            'invoice_type': 'Rechnungstyp',
            'payment_term': 'Zahlungsbedingung',
            'recurrence_type': 'Wiederholung',
            'recurrence_interval': 'Intervall',
            'start_date': 'Startdatum',
            'end_date': 'Enddatum',
            'revenue_account': 'Ertragskonto',
            'tax_account': 'Steuerkonto',
            'receivable_account': 'Forderungskonto',
            'is_active': 'Aktiv',
            'auto_send': 'Automatisch senden',
        }


class InvoiceTemplateForm(ModelForm):
    """Form for creating invoice templates."""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['revenue_account'].queryset = Account.objects.filter(
                account_type__is_income=True
            )
            self.fields['tax_account'].queryset = Account.objects.filter(
                account_type__code__in=['TAX', 'VAT']
            )
            self.fields['receivable_account'].queryset = Account.objects.filter(
                account_type__is_asset=True
            )
    
    class Meta:
        model = InvoiceTemplate
        fields = [
            'name', 'description', 'invoice_type', 'payment_term',
            'revenue_account', 'tax_account', 'receivable_account'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Name der Vorlage'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Beschreibung'
            }),
            'invoice_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_term': forms.Select(attrs={
                'class': 'form-select'
            }),
            'revenue_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'receivable_account': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        labels = {
            'name': 'Name',
            'description': 'Beschreibung',
            'invoice_type': 'Rechnungstyp',
            'payment_term': 'Zahlungsbedingung',
            'revenue_account': 'Ertragskonto',
            'tax_account': 'Steuerkonto',
            'receivable_account': 'Forderungskonto',
        }


class InvoiceSearchForm(forms.Form):
    """Form for searching invoices."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechnungsnummer, Kunde, Beschreibung...'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'Alle Status')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    invoice_type = forms.ChoiceField(
        required=False,
        choices=[('', 'Alle Typen')],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    customer = forms.ModelChoiceField(
        required=False,
        queryset=Contact.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dynamically populate choices to avoid circular imports
        self.fields['status'].choices = [('', 'Alle Status')] + [
            (s.code, s.name) for s in InvoiceStatus.objects.all()
        ]
        self.fields['invoice_type'].choices = [('', 'Alle Typen')] + [
            (t.code, t.name) for t in InvoiceType.objects.all()
        ]


# Formsets
InvoiceLineFormSet = inlineformset_factory(
    Invoice,
    InvoiceLine,
    form=InvoiceLineForm,
    extra=3,
    min_num=1,
    can_delete=True,
    can_order=True
)


class DateRangeForm(forms.Form):
    """Form for date range filtering."""
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
