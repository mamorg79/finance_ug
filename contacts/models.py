"""
Contact models for the accounting system.
Manages customers, suppliers, and other contacts.
"""
from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.contrib.auth.models import User
import uuid


class ContactType(models.Model):
    """Types of contacts (customer, supplier, etc.)."""
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=10, unique=True)
    is_customer = models.BooleanField(default=False, help_text="Kunde")
    is_supplier = models.BooleanField(default=False, help_text="Lieferant")
    is_both = models.BooleanField(default=False, help_text="Kunde und Lieferant")
    
    def __str__(self):
        return f"{self.name}"
    
    class Meta:
        verbose_name = "Kontaktart"
        verbose_name_plural = "Kontaktarten"


class Industry(models.Model):
    """Industry classifications for contacts."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Branche"
        verbose_name_plural = "Branchen"


class Country(models.Model):
    """Country model for address information."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=2, unique=True)
    eu_member = models.BooleanField(default=False, help_text="EU-Mitglied")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Land"
        verbose_name_plural = "Länder"


class Contact(models.Model):
    """Main contact model for customers and suppliers."""
    contact_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    contact_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Kundennummer/Lieferantennummer"
    )
    
    # Contact type
    contact_type = models.ForeignKey(
        ContactType,
        on_delete=models.PROTECT,
        related_name='contacts',
        help_text="Kontaktart"
    )
    
    # Basic information
    name = models.CharField(max_length=200, help_text="Firmenname")
    first_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Vorname (Ansprechpartner)"
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Nachname (Ansprechpartner)"
    )
    
    # Industry
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        help_text="Branche"
    )
    
    # Contact information
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="E-Mail-Adresse",
        validators=[EmailValidator()]
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Telefonnummer"
    )
    mobile = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Mobiltelefon"
    )
    fax = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Fax"
    )
    website = models.URLField(
        blank=True,
        null=True,
        help_text="Webseite"
    )
    
    # Tax information
    tax_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Steuernummer"
    )
    vat_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Umsatzsteuer-Identifikationsnummer",
        validators=[
            RegexValidator(
                regex='^[A-Za-z]{2}[A-Za-z0-9]{8,12}$',
                message='USt-IdNr. muss dem EU-Format entsprechen (z.B. DE123456789)',
                code='invalid_vat_number'
            )
        ]
    )
    
    # Address information
    address_line_1 = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Straße und Hausnummer"
    )
    address_line_2 = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Adresszusatz"
    )
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Postleitzahl"
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Stadt"
    )
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        help_text="Land"
    )
    
    # Accounting information
    default_account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_as_default',
        help_text="Standardkonto"
    )
    payment_term = models.ForeignKey(
        'invoices.PaymentTerm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        help_text="Standard-Zahlungsbedingung"
    )
    currency = models.CharField(
        max_length=3,
        default='EUR',
        help_text="Währung"
    )
    
    # Status and notes
    is_active = models.BooleanField(default=True, help_text="Aktiv")
    notes = models.TextField(blank=True, help_text="Notizen")
    internal_notes = models.TextField(blank=True, help_text="Interne Notizen")
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_contacts'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.contact_number} - {self.name}"
    
    def get_full_name(self):
        """Get full name including contact person."""
        if self.first_name and self.last_name:
            return f"{self.name} - {self.first_name} {self.last_name}"
        return self.name
    
    def get_full_address(self):
        """Get formatted full address."""
        parts = []
        if self.name:
            parts.append(self.name)
        if self.first_name and self.last_name:
            parts.append(f"z.Hd. {self.first_name} {self.last_name}")
        if self.address_line_1:
            parts.append(self.address_line_1)
        if self.address_line_2:
            parts.append(self.address_line_2)
        if self.postal_code and self.city:
            parts.append(f"{self.postal_code} {self.city}")
        if self.country:
            parts.append(self.country.name)
        return "\n".join(parts)
    
    def is_customer(self):
        return self.contact_type.is_customer or self.contact_type.is_both
    
    def is_supplier(self):
        return self.contact_type.is_supplier or self.contact_type.is_both
    
    class Meta:
        verbose_name = "Kontakt"
        verbose_name_plural = "Kontakte"
        ordering = ['name']


class ContactPerson(models.Model):
    """Additional contact persons for a contact."""
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='contact_persons'
    )
    first_name = models.CharField(max_length=100, help_text="Vorname")
    last_name = models.CharField(max_length=100, help_text="Nachname")
    position = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Position"
    )
    email = models.EmailField(
        blank=True,
        null=True,
        help_text="E-Mail-Adresse"
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Telefonnummer"
    )
    mobile = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Mobiltelefon"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Hauptansprechpartner"
    )
    notes = models.TextField(blank=True, help_text="Notizen")
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.contact.name})"
    
    class Meta:
        verbose_name = "Ansprechpartner"
        verbose_name_plural = "Ansprechpartner"
        ordering = ['last_name', 'first_name']


class BankAccount(models.Model):
    """Bank account information for contacts."""
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    bank_name = models.CharField(max_length=200, help_text="Bankname")
    account_number = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Kontonummer"
    )
    iban = models.CharField(
        max_length=34,
        blank=True,
        null=True,
        help_text="IBAN"
    )
    bic = models.CharField(
        max_length=11,
        blank=True,
        null=True,
        help_text="BIC/SWIFT-Code"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Standard-Bankverbindung"
    )
    account_holder = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Kontoinhaber (falls abweichend)"
    )
    notes = models.TextField(blank=True, help_text="Notizen")
    
    def __str__(self):
        return f"{self.bank_name} - {self.iban}"
    
    class Meta:
        verbose_name = "Bankverbindung"
        verbose_name_plural = "Bankverbindungen"
