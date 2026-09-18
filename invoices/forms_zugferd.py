"""
Forms for ZUGFeRD electronic invoice functionality.
"""
from django import forms
from django.forms import ModelForm, Form
from .models_zugferd import ZugferdInvoice, ZugferdConfig, ZugferdProfile, ZugferdTransmission
from .models import Invoice


class ZugferdConfigForm(ModelForm):
    """Form for ZUGFeRD configuration."""
    
    class Meta:
        model = ZugferdConfig
        fields = [
            'company_name', 'company_address', 'company_city',
            'company_postal_code', 'company_country', 'vat_number',
            'tax_number', 'default_profile', 'email_from',
            'email_subject', 'email_body', 'peppol_id', 'peppol_enabled'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Firmenname'
            }),
            'company_address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Adresse'
            }),
            'company_city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Stadt'
            }),
            'company_postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Postleitzahl'
            }),
            'company_country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Land (z.B. DE)'
            }),
            'vat_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Umsatzsteuer-IdNr. (z.B. DE123456789)'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Steuernummer'
            }),
            'default_profile': forms.Select(attrs={
                'class': 'form-select'
            }),
            'email_from': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Absender E-Mail'
            }),
            'email_subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Betreff für Rechnungs-E-Mails'
            }),
            'email_body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'E-Mail-Text für Rechnungs-E-Mails'
            }),
            'peppol_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Peppol-ID'
            }),
            'peppol_enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'company_name': 'Firmenname',
            'company_address': 'Firmenadresse',
            'company_city': 'Stadt',
            'company_postal_code': 'Postleitzahl',
            'company_country': 'Land',
            'vat_number': 'Umsatzsteuer-IdNr.',
            'tax_number': 'Steuernummer',
            'default_profile': 'Standard ZUGFeRD-Profil',
            'email_from': 'Absender E-Mail',
            'email_subject': 'E-Mail-Betreff',
            'email_body': 'E-Mail-Text',
            'peppol_id': 'Peppol-ID',
            'peppol_enabled': 'Peppol aktiviert',
        }


class ZugferdExportForm(Form):
    """Form for exporting ZUGFeRD invoices."""
    
    profile = forms.ModelChoiceField(
        queryset=ZugferdProfile.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='ZUGFeRD-Profil'
    )
    
    invoice_type_code = forms.ChoiceField(
        choices=[
            ('380', 'Rechnung'),
            ('381', 'Gutschrift'),
        ],
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Rechnungstyp',
        initial='380'
    )


class ZugferdImportForm(Form):
    """Form for importing ZUGFeRD XML files."""
    
    xml_file = forms.FileField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xml,application/xml'
        }),
        label='ZUGFeRD XML-Datei'
    )
    
    profile = forms.ModelChoiceField(
        queryset=ZugferdProfile.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='ZUGFeRD-Profil (optional)'
    )


class ZugferdEmailForm(Form):
    """Form for sending ZUGFeRD invoices via email."""
    
    recipient_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Empfänger E-Mail-Adresse'
        }),
        label='Empfänger E-Mail'
    )
    
    subject = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Betreff'
        }),
        label='Betreff',
        initial='Rechnung {invoice_number}'
    )
    
    message = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Nachricht (optional)'
        }),
        label='Nachricht'
    )
    
    include_pdf = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='PDF beifügen',
        initial=True
    )


class ZugferdInvoiceSearchForm(Form):
    """Form for searching ZUGFeRD invoices."""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechnungsnummer oder Kunde'
        }),
        label='Suche'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Alle'),
            ('exported', 'Exportiert'),
            ('imported', 'Importiert'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status'
    )


class TransmissionSearchForm(Form):
    """Form for searching transmissions."""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechnungsnummer oder E-Mail'
        }),
        label='Suche'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Alle'),
            ('pending', 'Ausstehend'),
            ('sent', 'Gesendet'),
            ('delivered', 'Zugestellt'),
            ('failed', 'Fehlgeschlagen'),
            ('received', 'Empfangen'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Status'
    )
    
    method = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Alle'),
            ('email', 'E-Mail'),
            ('peppol', 'Peppol'),
            ('download', 'Download'),
            ('api', 'API'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Methode'
    )


class ZugferdProfileForm(ModelForm):
    """Form for creating/updating ZUGFeRD profiles."""
    
    class Meta:
        model = ZugferdProfile
        fields = ['name', 'code', 'description', 'min_version', 'max_version']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'min_version': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'max_version': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }
        labels = {
            'name': 'Name',
            'code': 'Code',
            'description': 'Beschreibung',
            'min_version': 'Minimale Version',
            'max_version': 'Maximale Version',
        }


class QuickZugferdExportForm(Form):
    """Quick form for exporting ZUGFeRD from invoice detail page."""
    
    profile = forms.ModelChoiceField(
        queryset=ZugferdProfile.objects.all(),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm'
        }),
        label='Profil'
    )
