"""
Django management command for importing CSV files.
"""
import csv
import io
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounting.models import (
    Account, Transaction, TransactionLine, DocumentType,
    Journal, JournalEntry
)
from decimal import Decimal
import uuid
from datetime import datetime


class Command(BaseCommand):
    help = 'Import transactions from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the CSV file'
        )
        parser.add_argument(
            '--delimiter',
            type=str,
            default=',',
            help='CSV delimiter (default: comma)'
        )
        parser.add_argument(
            '--encoding',
            type=str,
            default='utf-8',
            help='File encoding (default: utf-8)'
        )
        parser.add_argument(
            '--skip-header',
            action='store_true',
            default=True,
            help='Skip header row'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Perform a dry run without saving'
        )
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        delimiter = options['delimiter']
        encoding = options['encoding']
        skip_header = options['skip_header']
        dry_run = options['dry_run']
        
        try:
            # Read CSV file
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            reader = csv.reader(io.StringIO(content), delimiter=delimiter)
            
            if skip_header:
                next(reader)  # Skip header
            
            # Expected CSV format:
            # Date, Document Number, Description, Account Number, Side (debit/credit), Amount, Tax Rate, Reference
            
            imported_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # Start from 2 because of header
                try:
                    if len(row) < 6:
                        errors.append(f"Row {row_num}: Not enough columns")
                        continue
                    
                    # Parse row
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
                        errors.append(f"Row {row_num}: Invalid side '{side}'")
                        continue
                    
                    # Normalize side
                    if side in ['soll']:
                        side = 'debit'
                    elif side in ['haben']:
                        side = 'credit'
                    
                    # Parse amount
                    try:
                        amount = Decimal(amount_str.replace(',', '.'))
                    except:
                        errors.append(f"Row {row_num}: Invalid amount '{amount_str}'")
                        continue
                    
                    # Parse date
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except:
                        try:
                            date_obj = datetime.strptime(date_str, '%d.%m.%Y').date()
                        except:
                            errors.append(f"Row {row_num}: Invalid date '{date_str}'")
                            continue
                    
                    # Get account
                    try:
                        account = Account.objects.get(account_number=account_number)
                    except Account.DoesNotExist:
                        errors.append(f"Row {row_num}: Account {account_number} not found")
                        continue
                    
                    # Create or get document type
                    doc_type, created = DocumentType.objects.get_or_create(
                        code='CSV_IMPORT',
                        defaults={'name': 'CSV Import', 'is_system': True}
                    )
                    
                    # Create transaction
                    transaction = Transaction.objects.create(
                        transaction_id=uuid.uuid4(),
                        document_number=f"CSV-{document_number}" if document_number else f"CSV-{row_num}",
                        date=date_obj,
                        posting_date=date_obj,
                        document_type=doc_type,
                        description=description,
                        reference=reference or f"CSV Import Row {row_num}",
                        created_by=None,  # Will be set if running as user
                        is_posted=False
                    )
                    
                    # Create transaction line
                    TransactionLine.objects.create(
                        transaction=transaction,
                        account=account,
                        side=side,
                        amount=amount,
                        description=description,
                        line_number=1
                    )
                    
                    imported_count += 1
                    
                    if not dry_run:
                        transaction.save()
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            # Output results
            self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} transactions"))
            
            if errors:
                self.stdout.write(self.style.WARNING(f"Encountered {len(errors)} errors:"))
                for error in errors[:10]:  # Show first 10 errors
                    self.stdout.write(self.style.WARNING(f"  - {error}"))
                if len(errors) > 10:
                    self.stdout.write(self.style.WARNING(f"  - ... and {len(errors) - 10} more errors"))
            
            if dry_run:
                self.stdout.write(self.style.WARNING("Dry run - no data was saved"))
            
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error importing CSV: {str(e)}")
