"""
Utility functions for importing data into the accounting system.
"""
import csv
import io
from decimal import Decimal
from datetime import datetime
import uuid

from accounting.models import (
    Account, Transaction, TransactionLine, DocumentType,
    TaxRate, Journal, JournalEntry
)
from invoices.models import Invoice, InvoiceLine, Payment
from contacts.models import Contact


class CSVImporter:
    """Base class for CSV import operations."""
    
    def __init__(self, delimiter=',', encoding='utf-8', skip_header=True):
        self.delimiter = delimiter
        self.encoding = encoding
        self.skip_header = skip_header
        self.errors = []
        self.imported_count = 0
    
    def import_file(self, file_path, dry_run=False):
        """Import data from CSV file."""
        try:
            with open(file_path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            return self.import_content(content, dry_run)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def import_content(self, content, dry_run=False):
        """Import data from CSV content string."""
        reader = csv.reader(io.StringIO(content), delimiter=self.delimiter)
        
        if self.skip_header:
            next(reader)  # Skip header
        
        self.errors = []
        self.imported_count = 0
        
        for row_num, row in enumerate(reader, start=2):
            try:
                if self.process_row(row, row_num):
                    self.imported_count += 1
            except Exception as e:
                self.errors.append(f"Row {row_num}: {str(e)}")
        
        return {
            'imported': self.imported_count,
            'errors': self.errors
        }
    
    def process_row(self, row, row_num):
        """Process a single row. Override in subclasses."""
        raise NotImplementedError("Subclasses must implement process_row")


class TransactionCSVImporter(CSVImporter):
    """Import transactions from CSV."""
    
    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
        self.current_transaction = None
        self.line_number = 0
    
    def process_row(self, row, row_num):
        """Process a transaction row."""
        # Expected format:
        # Date, Document Number, Description, Account Number, Side, Amount, Tax Rate, Reference
        
        if len(row) < 6:
            raise ValueError("Not enough columns")
        
        date_str = row[0].strip()
        document_number = row[1].strip()
        description = row[2].strip()
        account_number = row[3].strip()
        side = row[4].strip().lower()
        amount_str = row[5].strip()
        
        # Optional fields
        tax_rate_code = row[6].strip() if len(row) > 6 else None
        reference = row[7].strip() if len(row) > 7 else None
        
        # Validate side
        if side not in ['debit', 'credit', 'soll', 'haben']:
            raise ValueError(f"Invalid side '{side}'")
        
        # Normalize side
        side = 'debit' if side in ['debit', 'soll'] else 'credit'
        
        # Parse amount
        try:
            amount = Decimal(amount_str.replace(',', '.'))
        except:
            raise ValueError(f"Invalid amount '{amount_str}'")
        
        # Parse date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            try:
                date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
            except:
                raise ValueError(f"Invalid date '{date_str}'")
        
        # Get account
        try:
            account = Account.objects.get(account_number=account_number)
        except Account.DoesNotExist:
            raise ValueError(f"Account {account_number} not found")
        
        # Check if this is a new transaction
        if self.current_transaction is None or \
           self.current_transaction.document_number != document_number:
            # Create new transaction
            self._create_transaction(date_obj, document_number, description, reference)
            self.line_number = 0
        
        # Create transaction line
        self._create_line(account, side, amount, description, tax_rate_code)
        self.line_number += 1
        
        return True
    
    def _create_transaction(self, date_obj, document_number, description, reference):
        """Create a new transaction."""
        doc_type, created = DocumentType.objects.get_or_create(
            code='CSV_IMPORT',
            defaults={'name': 'CSV Import', 'is_system': True}
        )
        
        self.current_transaction = Transaction.objects.create(
            transaction_id=uuid.uuid4(),
            document_number=document_number or f"CSV-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            date=date_obj,
            posting_date=date_obj,
            document_type=doc_type,
            description=description,
            reference=reference or 'CSV Import',
            created_by=self.user,
            is_posted=False
        )
    
    def _create_line(self, account, side, amount, description, tax_rate_code):
        """Create a transaction line."""
        tax_rate = None
        if tax_rate_code:
            try:
                tax_rate = TaxRate.objects.get(code=tax_rate_code)
            except TaxRate.DoesNotExist:
                pass
        
        TransactionLine.objects.create(
            transaction=self.current_transaction,
            account=account,
            side=side,
            amount=amount,
            tax_rate=tax_rate,
            description=description,
            line_number=self.line_number + 1
        )


class InvoiceCSVImporter(CSVImporter):
    """Import invoices from CSV."""
    
    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
    
    def process_row(self, row, row_num):
        """Process an invoice row."""
        # Expected format:
        # Invoice Number, Date, Due Date, Customer Number, Description, Quantity, Unit Price, Tax Rate
        
        if len(row) < 7:
            raise ValueError("Not enough columns")
        
        invoice_number = row[0].strip()
        date_str = row[1].strip()
        due_date_str = row[2].strip()
        customer_number = row[3].strip()
        description = row[4].strip()
        quantity_str = row[5].strip()
        unit_price_str = row[6].strip()
        tax_rate_code = row[7].strip() if len(row) > 7 else None
        
        # Parse date
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        except:
            try:
                date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
            except:
                raise ValueError(f"Invalid date '{date_str}'")
        
        # Parse due date
        try:
            due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except:
            try:
                due_date_obj = datetime.strptime(due_date_str, '%d.%m.%Y').date()
            except:
                due_date_obj = date_obj  # Use invoice date as default
        
        # Get customer
        try:
            customer = Contact.objects.get(contact_number=customer_number)
        except Contact.DoesNotExist:
            raise ValueError(f"Customer {customer_number} not found")
        
        # Parse quantity and unit price
        try:
            quantity = Decimal(quantity_str.replace(',', '.'))
        except:
            raise ValueError(f"Invalid quantity '{quantity_str}'")
        
        try:
            unit_price = Decimal(unit_price_str.replace(',', '.'))
        except:
            raise ValueError(f"Invalid unit price '{unit_price_str}'")
        
        # Calculate amount
        amount = quantity * unit_price
        
        # Get tax rate
        tax_rate = None
        if tax_rate_code:
            try:
                tax_rate = TaxRate.objects.get(code=tax_rate_code)
            except TaxRate.DoesNotExist:
                pass
        
        # Create invoice
        invoice_type, created = InvoiceType.objects.get_or_create(
            code='STANDARD',
            defaults={'name': 'Standard Rechnung'}
        )
        
        status, created = InvoiceStatus.objects.get_or_create(
            code='DRAFT',
            defaults={'name': 'Entwurf', 'sort_order': 0}
        )
        
        invoice = Invoice.objects.create(
            invoice_id=uuid.uuid4(),
            invoice_number=invoice_number or f"IMP-{row_num}",
            invoice_type=invoice_type,
            status=status,
            customer=customer,
            date=date_obj,
            due_date=due_date_obj,
            description=description,
            created_by=self.user
        )
        
        # Create invoice line
        InvoiceLine.objects.create(
            invoice=invoice,
            line_number=1,
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            tax_rate=tax_rate,
            amount=amount
        )
        
        # Calculate totals
        invoice.calculate_totals()
        
        return True


class ContactCSVImporter(CSVImporter):
    """Import contacts from CSV."""
    
    def __init__(self, user=None, **kwargs):
        super().__init__(**kwargs)
        self.user = user
    
    def process_row(self, row, row_num):
        """Process a contact row."""
        # Expected format:
        # Contact Number, Name, First Name, Last Name, Email, Phone, Address, Postal Code, City
        
        if len(row) < 3:
            raise ValueError("Not enough columns")
        
        contact_number = row[0].strip()
        name = row[1].strip()
        first_name = row[2].strip() if len(row) > 2 else None
        last_name = row[3].strip() if len(row) > 3 else None
        email = row[4].strip() if len(row) > 4 else None
        phone = row[5].strip() if len(row) > 5 else None
        address = row[6].strip() if len(row) > 6 else None
        postal_code = row[7].strip() if len(row) > 7 else None
        city = row[8].strip() if len(row) > 8 else None
        
        # Get or create contact type
        contact_type, created = ContactType.objects.get_or_create(
            code='CUSTOMER',
            defaults={'name': 'Kunde', 'is_customer': True}
        )
        
        # Create contact
        Contact.objects.create(
            contact_id=uuid.uuid4(),
            contact_number=contact_number or f"K-{row_num}",
            contact_type=contact_type,
            name=name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address_line_1=address,
            postal_code=postal_code,
            city=city,
            created_by=self.user,
            is_active=True
        )
        
        return True


def import_csv_file(file_path, import_type='transactions', user=None, **kwargs):
    """
    Import data from CSV file.
    
    Args:
        file_path: Path to the CSV file
        import_type: Type of data to import ('transactions', 'invoices', 'contacts')
        user: User performing the import
        **kwargs: Additional arguments for the importer
    
    Returns:
        dict: Import results with 'imported' count and 'errors' list
    """
    importers = {
        'transactions': TransactionCSVImporter,
        'invoices': InvoiceCSVImporter,
        'contacts': ContactCSVImporter,
    }
    
    if import_type not in importers:
        raise ValueError(f"Unknown import type: {import_type}")
    
    importer = importers[import_type](user=user, **kwargs)
    return importer.import_file(file_path)


def import_datev_file(file_path, format_type='csv', user=None, **kwargs):
    """
    Import data from DATEV file.
    
    Args:
        file_path: Path to the DATEV file
        format_type: DATEV format ('csv' or 'extf')
        user: User performing the import
        **kwargs: Additional arguments
    
    Returns:
        dict: Import results with 'imported' count and 'errors' list
    """
    # For DATEV, we'll use a simplified approach
    # In a real implementation, we would parse the specific DATEV format
    
    if format_type == 'csv':
        # Use transaction importer for DATEV CSV
        importer = TransactionCSVImporter(user=user, delimiter=';', **kwargs)
    else:
        # For EXTF, we would need a specialized parser
        raise NotImplementedError("EXTF format not yet implemented")
    
    return importer.import_file(file_path)
