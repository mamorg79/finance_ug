"""
Forms for the accounting module.
"""
from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import (
    Account, AccountType, ChartOfAccounts, TaxRate, DocumentType,
    Transaction, TransactionLine, Journal, JournalEntry, Period,
    Reconciliation, ClosingEntry
)


class AccountForm(ModelForm):
    """Form for creating and updating accounts."""
    
    class Meta:
        model = Account
        fields = [
            'account_number', 'name', 'chart_of_accounts', 'account_type',
            'parent_account', 'is_active', 'tax_code', 'cost_center', 'notes'
        ]
        widgets = {
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kontonummer (z.B. 0600, 4000, 8000)'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kontobezeichnung'
            }),
            'chart_of_accounts': forms.Select(attrs={
                'class': 'form-select'
            }),
            'account_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'parent_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Steuerschlüssel'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kostenstelle'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notizen'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'account_number': 'Kontonummer',
            'name': 'Bezeichnung',
            'chart_of_accounts': 'Kontenrahmen',
            'account_type': 'Kontenart',
            'parent_account': 'Übergeordnetes Konto',
            'is_active': 'Aktiv',
            'tax_code': 'Steuerschlüssel',
            'cost_center': 'Kostenstelle',
            'notes': 'Notizen',
        }


class TransactionForm(ModelForm):
    """Form for creating and updating transactions."""
    
    class Meta:
        model = Transaction
        fields = [
            'document_number', 'date', 'posting_date', 'document_type',
            'description', 'reference'
        ]
        widgets = {
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Belegnummer'
            }),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'posting_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'document_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Buchungstext'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Referenz (z.B. Rechnungsnummer)'
            }),
        }
        labels = {
            'document_number': 'Belegnummer',
            'date': 'Buchungsdatum',
            'posting_date': 'Wertstellungsdatum',
            'document_type': 'Belegart',
            'description': 'Beschreibung',
            'reference': 'Referenz',
        }


class TransactionLineForm(ModelForm):
    """Form for transaction lines."""
    
    class Meta:
        model = TransactionLine
        fields = [
            'account', 'side', 'amount', 'tax_rate', 'tax_amount',
            'description', 'cost_center'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-select account-select'
            }),
            'side': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control amount-input',
                'step': '0.01',
                'min': '0.01'
            }),
            'tax_rate': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tax_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Beschreibung'
            }),
            'cost_center': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kostenstelle'
            }),
        }
        labels = {
            'account': 'Konto',
            'side': 'Seite',
            'amount': 'Betrag',
            'tax_rate': 'Steuersatz',
            'tax_amount': 'Steuerbetrag',
            'description': 'Beschreibung',
            'cost_center': 'Kostenstelle',
        }


class PeriodForm(ModelForm):
    """Form for accounting periods."""
    
    class Meta:
        model = Period
        fields = [
            'name', 'start_date', 'end_date', 'period_type', 'fiscal_year', 'is_closed'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Periodenname'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'period_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'fiscal_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2000,
                'max': 2100
            }),
            'is_closed': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'name': 'Name',
            'start_date': 'Startdatum',
            'end_date': 'Enddatum',
            'period_type': 'Periodentyp',
            'fiscal_year': 'Geschäftsjahr',
            'is_closed': 'Abgeschlossen',
        }


class ReconciliationForm(ModelForm):
    """Form for bank/account reconciliations."""
    
    class Meta:
        model = Reconciliation
        fields = [
            'account', 'statement_date', 'statement_balance',
            'reconciled_balance', 'difference', 'is_reconciled', 'notes'
        ]
        widgets = {
            'account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'statement_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'statement_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'reconciled_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'difference': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'readonly': 'readonly'
            }),
            'is_reconciled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notizen'
            }),
        }
        labels = {
            'account': 'Konto',
            'statement_date': 'Aussagedatum',
            'statement_balance': 'Aussagesaldo',
            'reconciled_balance': 'Abgestimmter Saldo',
            'difference': 'Differenz',
            'is_reconciled': 'Abgestimmt',
            'notes': 'Notizen',
        }


class ClosingEntryForm(ModelForm):
    """Form for closing entries."""
    
    class Meta:
        model = ClosingEntry
        fields = [
            'period', 'from_account', 'to_account', 'amount', 'description'
        ]
        widgets = {
            'period': forms.Select(attrs={
                'class': 'form-select'
            }),
            'from_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'to_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Beschreibung'
            }),
        }
        labels = {
            'period': 'Periode',
            'from_account': 'Von Konto',
            'to_account': 'Nach Konto',
            'amount': 'Betrag',
            'description': 'Beschreibung',
        }


# Formsets
TransactionLineFormSet = inlineformset_factory(
    Transaction,
    TransactionLine,
    form=TransactionLineForm,
    extra=2,
    min_num=2,
    can_delete=True,
    can_order=True
)


class SearchForm(forms.Form):
    """Generic search form."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Suche...'
        })
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


class ImportCSVForm(forms.Form):
    """Form for CSV import."""
    csv_file = forms.FileField(
        label='CSV-Datei',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    delimiter = forms.ChoiceField(
        label='Trennzeichen',
        choices=[
            (',', 'Komma'),
            (';', 'Semikolon'),
            ('\t', 'Tabulator'),
        ],
        initial=',',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    encoding = forms.ChoiceField(
        label='Zeichencodierung',
        choices=[
            ('utf-8', 'UTF-8'),
            ('latin-1', 'Latin-1'),
            ('cp1252', 'Windows-1252'),
        ],
        initial='utf-8',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    skip_header = forms.BooleanField(
        label='Erste Zeile überspringen',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )


class ImportDATEVForm(forms.Form):
    """Form for DATEV import."""
    datev_file = forms.FileField(
        label='DATEV-Datei',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.txt'
        })
    )
    format_type = forms.ChoiceField(
        label='DATEV-Format',
        choices=[
            ('extf', 'Extended Format (EXTF)'),
            ('csv', 'CSV Format'),
        ],
        initial='csv',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
