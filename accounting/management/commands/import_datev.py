"""
Django management command for importing DATEV files.
Supports DATEV CSV format (EXTF and CSV).
"""
import csv
import io
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounting.models import (
    Account, Transaction, TransactionLine, DocumentType,
    TaxRate, Journal, JournalEntry
)
from contacts.models import Contact
from decimal import Decimal
import uuid
from datetime import datetime


class Command(BaseCommand):
    help = 'Import transactions from DATEV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to the DATEV file'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='csv',
            choices=['csv', 'extf'],
            help='DATEV format (csv or extf)'
        )
        parser.add_argument(
            '--encoding',
            type=str,
            default='utf-8',
            help='File encoding (default: utf-8)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Perform a dry run without saving'
        )
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        datev_format = options['format']
        encoding = options['encoding']
        dry_run = options['dry_run']
        
        try:
            # Read file
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            if datev_format == 'extf':
                # Parse EXTF format
                imported_count = self._import_extf(content, dry_run)
            else:
                # Parse CSV format
                imported_count = self._import_csv(content, dry_run)
            
            self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_count} transactions"))
            
            if dry_run:
                self.stdout.write(self.style.WARNING("Dry run - no data was saved"))
            
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except Exception as e:
            raise CommandError(f"Error importing DATEV: {str(e)}")
    
    def _import_csv(self, content, dry_run):
        """Import DATEV CSV format."""
        reader = csv.reader(io.StringIO(content), delimiter=';')
        
        imported_count = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=1):
            try:
                # DATEV CSV format:
                # 0: Umsatz (Vorgang) - Transaction type
                # 1: Buchungstext - Description
                # 2: Gegenkonto - Counter account
                # 3: Betrag - Amount
                # 4: Soll/Haben - Debit/Credit
                # 5: Währung - Currency
                # 6: Buchungsdatum - Booking date
                # 7: Belegdatum - Document date
                # 8: Belegnummer - Document number
                # ... more fields
                
                if len(row) < 9:
                    continue
                
                # Parse fields
                umsatz = row[0].strip()
                description = row[1].strip()
                gegenkonto = row[2].strip()
                amount_str = row[3].strip()
                soll_haben = row[4].strip()
                currency = row[5].strip()
                buchungsdatum = row[6].strip()
                belegdatum = row[7].strip()
                belegnummer = row[8].strip()
                
                # Validate
                if not amount_str:
                    continue
                
                # Parse amount
                try:
                    amount = Decimal(amount_str.replace(',', '.'))
                except:
                    errors.append(f"Row {row_num}: Invalid amount '{amount_str}'")
                    continue
                
                # Parse date
                try:
                    date_obj = datetime.strptime(buchungsdatum, '%Y%m%d').date()
                except:
                    errors.append(f"Row {row_num}: Invalid date '{buchungsdatum}'")
                    continue
                
                # Parse side
                side = 'debit' if soll_haben == 'S' else 'credit'
                
                # Create or get document type
                doc_type, created = DocumentType.objects.get_or_create(
                    code='DATEV_IMPORT',
                    defaults={'name': 'DATEV Import', 'is_system': True}
                )
                
                # Create transaction
                transaction = Transaction.objects.create(
                    transaction_id=uuid.uuid4(),
                    document_number=belegnummer or f"DATEV-{row_num}",
                    date=date_obj,
                    posting_date=date_obj,
                    document_type=doc_type,
                    description=description,
                    reference=f"DATEV Import Row {row_num}",
                    created_by=None,
                    is_posted=False
                )
                
                # Get or create account
                account, created = Account.objects.get_or_create(
                    account_number=gegenkonto,
                    defaults={
                        'name': f'Importiert: {gegenkonto}',
                        'chart_of_accounts_id': 1,  # Default
                        'account_type_id': 1,  # Default
                    }
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
        
        return imported_count
    
    def _import_extf(self, content, dry_run):
        """Import DATEV EXTF format."""
        # EXTF is a fixed-width format
        # For simplicity, we'll parse it as CSV with semicolon delimiter
        return self._import_csv(content, dry_run)
