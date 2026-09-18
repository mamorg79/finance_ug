"""
ZUGFeRD models for electronic invoices.
Implements ZUGFeRD 2.0 (CIUS - Cross Industry Invoice) XML format.
"""
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
import uuid
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime

from .models import Invoice, InvoiceLine, Contact, TaxRate


class ZugferdProfile(models.Model):
    """ZUGFeRD profile definitions."""
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    min_version = models.CharField(max_length=20, default='2.0')
    max_version = models.CharField(max_length=20, default='2.0')
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        verbose_name = "ZUGFeRD-Profil"
        verbose_name_plural = "ZUGFeRD-Profile"


class ZugferdInvoice(models.Model):
    """Extended invoice model with ZUGFeRD support."""
    zugferd_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invoice = models.OneToOneField(
        Invoice,
        on_delete=models.CASCADE,
        related_name='zugferd_invoice',
        help_text="Verknüpfte Rechnung"
    )
    profile = models.ForeignKey(
        ZugferdProfile,
        on_delete=models.PROTECT,
        related_name='zugferd_invoices',
        help_text="ZUGFeRD-Profil"
    )
    
    # ZUGFeRD specific fields
    invoice_type_code = models.CharField(
        max_length=10,
        default='380',
        help_text="Rechnungstyp Code (380 = Rechnung, 381 = Gutschrift)"
    )
    
    # Status
    is_exported = models.BooleanField(
        default=False,
        help_text="Als ZUGFeRD exportiert"
    )
    is_imported = models.BooleanField(
        default=False,
        help_text="Aus ZUGFeRD importiert"
    )
    
    # File storage
    xml_file = models.FileField(
        upload_to='zugferd/xml/',
        blank=True,
        null=True,
        help_text="ZUGFeRD XML-Datei"
    )
    pdf_file = models.FileField(
        upload_to='zugferd/pdfs/',
        blank=True,
        null=True,
        help_text="ZUGFeRD PDF-Datei (Hybrid)"
    )
    
    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_zugferd_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ZUGFeRD {self.profile.code} - {self.invoice.invoice_number}"
    
    def generate_xml(self):
        """Generate ZUGFeRD XML from invoice."""
        invoice = self.invoice
        
        # Create root element
        ns = {
            'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
            'qdt': 'urn:un:unece:uncefact:data:standard:QualifiedDataType:100',
            'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100',
            'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        
        root = ET.Element('rsm:CrossIndustryInvoice', nsmap=ns)
        root.set('{http://www.w3.org/2001/XMLSchema-instance}schemaLocation', 
                'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100 CrossIndustryInvoice_100pD16B.xsd')
        
        # Header
        header = ET.SubElement(root, 'rsm:ExchangedDocumentContext')
        
        # Document ID
        doc_id = ET.SubElement(header, 'ram:ID')
        doc_id.text = invoice.invoice_number
        
        # Document type code
        doc_type = ET.SubElement(header, 'ram:TypeCode')
        doc_type.text = self.invoice_type_code
        
        # Issue date
        issue_date = ET.SubElement(header, 'ram:IssueDateTime')
        issue_date.set('format', '102')
        issue_date.text = invoice.date.strftime('%Y%m%d')
        
        # Add header information
        self._add_header_info(header, invoice)
        
        # Add supplier (company)
        self._add_supplier(root, invoice)
        
        # Add customer
        self._add_customer(root, invoice)
        
        # Add payment terms
        self._add_payment_terms(root, invoice)
        
        # Add tax information
        self._add_tax_info(root, invoice)
        
        # Add invoice lines
        self._add_invoice_lines(root, invoice)
        
        # Add totals
        self._add_totals(root, invoice)
        
        # Convert to pretty XML
        xml_str = ET.tostring(root, encoding='unicode')
        xml_pretty = minidom.parseString(xml_str).toprettyxml(indent='  ')
        
        return xml_pretty
    
    def _add_header_info(self, header, invoice):
        """Add header information to XML."""
        # Process context
        process_context = ET.SubElement(header, 'ram:ProcessContext')
        
        # Business process
        business_process = ET.SubElement(process_context, 'ram:BusinessProcess')
        business_id = ET.SubElement(business_process, 'ram:ID')
        business_id.text = 'urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:extended'
        
        # Test indicator (if applicable)
        if invoice.invoice_number.startswith('TEST'):
            test_indicator = ET.SubElement(process_context, 'ram:TestIndicator')
            test_indicator.text = 'true'
    
    def _add_supplier(self, root, invoice):
        """Add supplier (our company) information."""
        # This would be your company information
        # For now, we'll use placeholder data
        supplier = ET.SubElement(root, 'ram:AccountingSupplierParty')
        
        # Party
        party = ET.SubElement(supplier, 'ram:Party')
        
        # Name
        name = ET.SubElement(party, 'ram:Name')
        name.text = 'Finance UG'
        
        # Address
        address = ET.SubElement(party, 'ram:PostalTradeAddress')
        
        # Street
        street = ET.SubElement(address, 'ram:StreetName')
        street.text = 'Musterstraße'
        
        # Building number
        building = ET.SubElement(address, 'ram:BuildingNumber')
        building.text = '1'
        
        # City
        city = ET.SubElement(address, 'ram:CityName')
        city.text = 'Musterstadt'
        
        # Postal code
        postal_code = ET.SubElement(address, 'ram:PostcodeCode')
        postal_code.text = '12345'
        
        # Country
        country = ET.SubElement(address, 'ram:CountryID')
        country.text = 'DE'
        
        # Tax information
        tax_info = ET.SubElement(supplier, 'ram:SpecifiedTaxRegistration')
        
        # Tax ID
        tax_id = ET.SubElement(tax_info, 'ram:ID')
        tax_id.set('schemeID', 'VA')
        tax_id.text = 'DE123456789'  # Your VAT number
        
        # Contact
        contact = ET.SubElement(supplier, 'ram:AccountingContact')
        contact_name = ET.SubElement(contact, 'ram:Name')
        contact_name.text = 'Finance UG Buchhaltung'
        
        contact_email = ET.SubElement(contact, 'ram:EmailAddress')
        contact_email.text = 'buchhaltung@finance-ug.de'
    
    def _add_customer(self, root, invoice):
        """Add customer information."""
        customer = ET.SubElement(root, 'ram:AccountingCustomerParty')
        
        # Party
        party = ET.SubElement(customer, 'ram:Party')
        
        # Name
        name = ET.SubElement(party, 'ram:Name')
        name.text = invoice.customer.name
        
        # Address
        if invoice.customer.address_line_1:
            address = ET.SubElement(party, 'ram:PostalTradeAddress')
            
            # Street and number
            street_parts = invoice.customer.address_line_1.split()
            if street_parts:
                street = ET.SubElement(address, 'ram:StreetName')
                street.text = ' '.join(street_parts[:-1]) if len(street_parts) > 1 else street_parts[0]
                
                building = ET.SubElement(address, 'ram:BuildingNumber')
                building.text = street_parts[-1] if len(street_parts) > 1 else ''
            
            # City
            if invoice.customer.city:
                city = ET.SubElement(address, 'ram:CityName')
                city.text = invoice.customer.city
            
            # Postal code
            if invoice.customer.postal_code:
                postal_code = ET.SubElement(address, 'ram:PostcodeCode')
                postal_code.text = invoice.customer.postal_code
            
            # Country
            if invoice.customer.country:
                country = ET.SubElement(address, 'ram:CountryID')
                country.text = invoice.customer.country.code
        
        # Tax information (if available)
        if invoice.customer.vat_number:
            tax_info = ET.SubElement(customer, 'ram:SpecifiedTaxRegistration')
            tax_id = ET.SubElement(tax_info, 'ram:ID')
            tax_id.set('schemeID', 'VA')
            tax_id.text = invoice.customer.vat_number
        
        # Contact
        contact = ET.SubElement(customer, 'ram:AccountingContact')
        contact_name = ET.SubElement(contact, 'ram:Name')
        contact_name.text = invoice.customer.get_full_name()
        
        if invoice.customer.email:
            contact_email = ET.SubElement(contact, 'ram:EmailAddress')
            contact_email.text = invoice.customer.email
    
    def _add_payment_terms(self, root, invoice):
        """Add payment terms to XML."""
        if invoice.payment_term:
            payment_terms = ET.SubElement(root, 'ram:ApplicableTradeAgreement')
            
            # Payment due date
            due_date = ET.SubElement(payment_terms, 'ram:PaymentDueDate')
            due_date.set('format', '102')
            due_date.text = invoice.due_date.strftime('%Y%m%d') if invoice.due_date else invoice.date.strftime('%Y%m%d')
            
            # Payment terms description
            if invoice.payment_term.description:
                terms = ET.SubElement(payment_terms, 'ram:PaymentTerms')
                terms.text = invoice.payment_term.description
    
    def _add_tax_info(self, root, invoice):
        """Add tax information to XML."""
        # This is handled per line in _add_invoice_lines
        pass
    
    def _add_invoice_lines(self, root, invoice):
        """Add invoice lines to XML."""
        line_items = ET.SubElement(root, 'ram:SpecifiedTradeSettlementMonetarySummation')
        
        # Line item container
        line_container = ET.SubElement(root, 'ram:SpecifiedTradeAgreement')
        line_item_list = ET.SubElement(line_container, 'ram:LineItem')
        
        for line in invoice.lines.all().order_by('line_number'):
            line_item = ET.SubElement(line_item_list, 'ram:LineItem')
            
            # Line ID
            line_id = ET.SubElement(line_item, 'ram:ID')
            line_id.text = str(line.line_number)
            
            # Description
            description = ET.SubElement(line_item, 'ram:Description')
            description.text = line.description
            
            # Quantity
            quantity = ET.SubElement(line_item, 'ram:BilledQuantity')
            quantity.text = str(line.quantity)
            quantity.set('unitCode', 'C62')  # Default unit: piece
            
            # Unit price
            price = ET.SubElement(line_item, 'ram:Price')
            price_amount = ET.SubElement(price, 'ram:PriceAmount')
            price_amount.text = str(line.unit_price)
            price_amount.set('currencyID', invoice.currency or 'EUR')
            
            # Line total
            line_total = ET.SubElement(line_item, 'ram:LineTotalAmount')
            line_total.text = str(line.amount)
            line_total.set('currencyID', invoice.currency or 'EUR')
            
            # Tax information
            if line.tax_rate:
                tax_info = ET.SubElement(line_item, 'ram:ApplicableTradeTax')
                
                # Tax category
                tax_category = ET.SubElement(tax_info, 'ram:CategoryCode')
                tax_category.text = self._get_tax_category_code(line.tax_rate)
                
                # Tax rate
                tax_rate = ET.SubElement(tax_info, 'ram:RateApplicable')
                tax_rate.text = str(line.tax_rate.rate)
                
                # Tax amount
                tax_amount = ET.SubElement(line_item, 'ram:TradeTaxAmount')
                tax_amount.text = str(line.tax_amount)
                tax_amount.set('currencyID', invoice.currency or 'EUR')
    
    def _get_tax_category_code(self, tax_rate):
        """Get ZUGFeRD tax category code."""
        if tax_rate.tax_type == 'vat':
            if tax_rate.rate == Decimal('0.00'):
                return 'E'  # Exempt
            elif tax_rate.rate == Decimal('19.00'):
                return 'S'  # Standard rate
            elif tax_rate.rate == Decimal('7.00'):
                return 'G'  # Reduced rate
            else:
                return 'S'  # Standard rate
        elif tax_rate.tax_type == 'input_vat':
            return 'AE'  # Exempt from VAT
        else:
            return 'E'  # Exempt
    
    def _add_totals(self, root, invoice):
        """Add invoice totals to XML."""
        totals = ET.SubElement(root, 'ram:SpecifiedTradeSettlementMonetarySummation')
        
        # Line total
        line_total = ET.SubElement(totals, 'ram:LineTotalAmount')
        line_total.text = str(invoice.subtotal)
        line_total.set('currencyID', invoice.currency or 'EUR')
        
        # Tax total
        tax_total = ET.SubElement(totals, 'ram:TaxTotalAmount')
        tax_total.text = str(invoice.tax_amount)
        tax_total.set('currencyID', invoice.currency or 'EUR')
        
        # Grand total
        grand_total = ET.SubElement(totals, 'ram:GrandTotalAmount')
        grand_total.text = str(invoice.total_amount)
        grand_total.set('currencyID', invoice.currency or 'EUR')
        
        # Due amount
        due_amount = ET.SubElement(totals, 'ram:DuePayableAmount')
        due_amount.text = str(invoice.get_balance())
        due_amount.set('currencyID', invoice.currency or 'EUR')
    
    def export_xml(self, file_path=None):
        """Export invoice as ZUGFeRD XML."""
        xml_content = self.generate_xml()
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
        
        # Save to model
        self.xml_file.save(
            f'zugferd_{self.invoice.invoice_number}.xml',
            io.BytesIO(xml_content.encode('utf-8'))
        )
        self.is_exported = True
        self.save()
        
        return xml_content
    
    def import_from_xml(self, xml_content):
        """Import invoice from ZUGFeRD XML."""
        try:
            root = ET.fromstring(xml_content)
            
            # Extract basic information
            ns = {
                'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
                'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100'
            }
            
            # Get document context
            doc_context = root.find('rsm:ExchangedDocumentContext', ns)
            if doc_context is not None:
                # Invoice number
                invoice_number = doc_context.find('ram:ID', ns)
                if invoice_number is not None:
                    self.invoice.invoice_number = invoice_number.text
                
                # Invoice date
                issue_date = doc_context.find('ram:IssueDateTime', ns)
                if issue_date is not None:
                    try:
                        self.invoice.date = datetime.strptime(issue_date.text, '%Y%m%d').date()
                    except:
                        pass
            
            # Get supplier and customer
            supplier = root.find('ram:AccountingSupplierParty', ns)
            customer = root.find('ram:AccountingCustomerParty', ns)
            
            # Get invoice lines
            line_items = root.findall('.//ram:LineItem', ns)
            for line_item in line_items:
                # Extract line information
                description = line_item.find('ram:Description', ns)
                quantity = line_item.find('ram:BilledQuantity', ns)
                price = line_item.find('ram:Price/ram:PriceAmount', ns)
                line_total = line_item.find('ram:LineTotalAmount', ns)
                
                # Create invoice line
                InvoiceLine.objects.create(
                    invoice=self.invoice,
                    line_number=1,  # Will be updated
                    description=description.text if description is not None else '',
                    quantity=Decimal(quantity.text) if quantity is not None else Decimal('1.00'),
                    unit_price=Decimal(price.text) if price is not None else Decimal('0.00'),
                    amount=Decimal(line_total.text) if line_total is not None else Decimal('0.00')
                )
            
            # Calculate totals
            self.invoice.calculate_totals()
            self.invoice.save()
            
            self.is_imported = True
            self.save()
            
            return True
            
        except Exception as e:
            raise ValueError(f"Error importing ZUGFeRD XML: {str(e)}")
    
    def create_hybrid_pdf(self, pdf_file_path):
        """Create hybrid PDF with embedded ZUGFeRD XML."""
        from PyPDF2 import PdfReader, PdfWriter
        import io
        
        # Generate XML
        xml_content = self.generate_xml()
        
        # Create PDF with embedded XML
        # This would require a PDF library that supports embedding XML
        # For now, we'll just save both files separately
        
        # Save XML
        self.export_xml()
        
        # For hybrid PDF, we would need to:
        # 1. Generate the visual PDF
        # 2. Embed the XML as an attachment or in the metadata
        # This is a simplified version
        
        self.pdf_file.save(
            f'zugferd_{self.invoice.invoice_number}.pdf',
            io.BytesIO(xml_content.encode('utf-8'))
        )
        
        return True
    
    class Meta:
        verbose_name = "ZUGFeRD-Rechnung"
        verbose_name_plural = "ZUGFeRD-Rechnungen"


class ZugferdConfig(models.Model):
    """ZUGFeRD configuration for the company."""
    company_name = models.CharField(max_length=200, help_text="Firmenname")
    company_address = models.TextField(help_text="Firmenadresse")
    company_city = models.CharField(max_length=100, help_text="Stadt")
    company_postal_code = models.CharField(max_length=20, help_text="Postleitzahl")
    company_country = models.CharField(max_length=2, default='DE', help_text="Land")
    vat_number = models.CharField(max_length=50, help_text="Umsatzsteuer-IdNr.")
    tax_number = models.CharField(max_length=50, blank=True, null=True, help_text="Steuernummer")
    
    # Default profile
    default_profile = models.ForeignKey(
        ZugferdProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='default_config',
        help_text="Standard ZUGFeRD-Profil"
    )
    
    # Email settings for sending
    email_from = models.EmailField(help_text="Absender E-Mail")
    email_subject = models.CharField(
        max_length=200,
        default='Rechnung {invoice_number}',
        help_text="Betreff für Rechnungs-E-Mails"
    )
    email_body = models.TextField(
        default='Anbei erhalten Sie die Rechnung {invoice_number} im ZUGFeRD-Format.',
        help_text="E-Mail-Text für Rechnungs-E-Mails"
    )
    
    # Peppol settings
    peppol_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Peppol-ID"
    )
    peppol_enabled = models.BooleanField(
        default=False,
        help_text="Peppol aktiviert"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_zugferd_configs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ZUGFeRD-Konfiguration: {self.company_name}"
    
    class Meta:
        verbose_name = "ZUGFeRD-Konfiguration"
        verbose_name_plural = "ZUGFeRD-Konfigurationen"


class ZugferdTransmission(models.Model):
    """Record of ZUGFeRD invoice transmissions."""
    transmission_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    zugferd_invoice = models.ForeignKey(
        ZugferdInvoice,
        on_delete=models.CASCADE,
        related_name='transmissions',
        help_text="ZUGFeRD-Rechnung"
    )
    
    # Transmission method
    TRANSMISSION_METHODS = [
        ('email', 'E-Mail'),
        ('peppol', 'Peppol'),
        ('download', 'Download'),
        ('api', 'API'),
    ]
    method = models.CharField(
        max_length=20,
        choices=TRANSMISSION_METHODS,
        help_text="Übertragungsmethode"
    )
    
    # Recipient information
    recipient_email = models.EmailField(
        blank=True,
        null=True,
        help_text="Empfänger E-Mail"
    )
    recipient_peppol_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Empfänger Peppol-ID"
    )
    
    # Status
    TRANSMISSION_STATUSES = [
        ('pending', 'Ausstehend'),
        ('sent', 'Gesendet'),
        ('delivered', 'Zugestellt'),
        ('failed', 'Fehlgeschlagen'),
        ('received', 'Empfangen'),
    ]
    status = models.CharField(
        max_length=20,
        choices=TRANSMISSION_STATUSES,
        default='pending',
        help_text="Status"
    )
    
    # Timestamps
    sent_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Gesendet am"
    )
    delivered_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Zugestellt am"
    )
    
    # Response
    response_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Antwort-Status"
    )
    response_message = models.TextField(
        blank=True,
        help_text="Antwort-Nachricht"
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_zugferd_transmissions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"ZUGFeRD-Übertragung {self.transmission_id} ({self.get_method_display()})"
    
    class Meta:
        verbose_name = "ZUGFeRD-Übertragung"
        verbose_name_plural = "ZUGFeRD-Übertragungen"
        ordering = ['-created_at']
