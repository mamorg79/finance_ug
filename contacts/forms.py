"""
Forms for the contacts module.
"""
from django import forms
from django.forms import ModelForm, inlineformset_factory
from .models import Contact, ContactType, Industry, Country, ContactPerson, BankAccount


class ContactForm(ModelForm):
    """Form for creating and updating contacts."""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit choices based on user if provided
        if self.user:
            pass  # In a real implementation, you might limit some fields
    
    class Meta:
        model = Contact
        fields = [
            'contact_number', 'contact_type', 'name', 'first_name', 'last_name',
            'industry', 'email', 'phone', 'mobile', 'fax', 'website',
            'tax_number', 'vat_number',
            'address_line_1', 'address_line_2', 'postal_code', 'city', 'country',
            'default_account', 'payment_term', 'currency',
            'is_active', 'notes', 'internal_notes'
        ]
        widgets = {
            'contact_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kundennummer'
            }),
            'contact_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Firmenname'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vorname'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nachname'
            }),
            'industry': forms.Select(attrs={
                'class': 'form-select'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-Mail-Adresse'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefonnummer'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mobiltelefon'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Fax'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Webseite'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Steuernummer'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Umsatzsteuer-IdNr.'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Straße und Hausnummer'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresszusatz'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postleitzahl'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stadt'
            }),
            'country': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_account': forms.Select(attrs={
                'class': 'form-select'
            }),
            'payment_term': forms.Select(attrs={
                'class': 'form-select'
            }),
            'currency': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Währung (z.B. EUR)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notizen'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Interne Notizen'
            }),
        }
        labels = {
            'contact_number': 'Kundennummer',
            'contact_type': 'Kontaktart',
            'name': 'Firmenname',
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'industry': 'Branche',
            'email': 'E-Mail-Adresse',
            'phone': 'Telefonnummer',
            'mobile': 'Mobiltelefon',
            'fax': 'Fax',
            'website': 'Webseite',
            'tax_number': 'Steuernummer',
            'vat_number': 'Umsatzsteuer-IdNr.',
            'address_line_1': 'Straße und Hausnummer',
            'address_line_2': 'Adresszusatz',
            'postal_code': 'Postleitzahl',
            'city': 'Stadt',
            'country': 'Land',
            'default_account': 'Standardkonto',
            'payment_term': 'Standard-Zahlungsbedingung',
            'currency': 'Währung',
            'is_active': 'Aktiv',
            'notes': 'Notizen',
            'internal_notes': 'Interne Notizen',
        }


class ContactPersonForm(ModelForm):
    """Form for contact persons."""
    
    class Meta:
        model = ContactPerson
        fields = [
            'first_name', 'last_name', 'position', 'email',
            'phone', 'mobile', 'is_primary', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Vorname'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nachname'
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Position'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'E-Mail-Adresse'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Telefonnummer'
            }),
            'mobile': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mobiltelefon'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notizen'
            }),
        }
        labels = {
            'first_name': 'Vorname',
            'last_name': 'Nachname',
            'position': 'Position',
            'email': 'E-Mail-Adresse',
            'phone': 'Telefonnummer',
            'mobile': 'Mobiltelefon',
            'is_primary': 'Hauptansprechpartner',
            'notes': 'Notizen',
        }


class BankAccountForm(ModelForm):
    """Form for bank accounts."""
    
    class Meta:
        model = BankAccount
        fields = [
            'bank_name', 'account_number', 'iban', 'bic',
            'is_default', 'account_holder', 'notes'
        ]
        widgets = {
            'bank_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bankname'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kontonummer'
            }),
            'iban': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'IBAN'
            }),
            'bic': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BIC/SWIFT-Code'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'account_holder': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kontoinhaber'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Notizen'
            }),
        }
        labels = {
            'bank_name': 'Bankname',
            'account_number': 'Kontonummer',
            'iban': 'IBAN',
            'bic': 'BIC/SWIFT-Code',
            'is_default': 'Standard-Bankverbindung',
            'account_holder': 'Kontoinhaber',
            'notes': 'Notizen',
        }


class ContactSearchForm(forms.Form):
    """Form for searching contacts."""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name, Kundennummer, E-Mail...'
        })
    )
    
    contact_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Alle Typen'),
            ('customer', 'Kunden'),
            ('supplier', 'Lieferanten'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


# Formsets
ContactPersonFormSet = inlineformset_factory(
    Contact,
    ContactPerson,
    form=ContactPersonForm,
    extra=1,
    can_delete=True
)


BankAccountFormSet = inlineformset_factory(
    Contact,
    BankAccount,
    form=BankAccountForm,
    extra=1,
    can_delete=True
)
