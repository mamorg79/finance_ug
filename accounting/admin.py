"""
Django admin configuration for accounting models.
"""
from django.contrib import admin
from .models import (
    AccountType, ChartOfAccounts, Account, TaxRate, DocumentType,
    Transaction, TransactionLine, Journal, JournalEntry, Period,
    ClosingEntry, Reconciliation, ReconciliationItem
)


@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'balance_side')
    list_filter = ('is_asset', 'is_liability', 'is_income', 'is_expense')
    search_fields = ('code', 'name')


@admin.register(ChartOfAccounts)
class ChartOfAccountsAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_number', 'name', 'chart_of_accounts', 'account_type', 'current_balance', 'is_active')
    list_filter = ('chart_of_accounts', 'account_type', 'is_active')
    search_fields = ('account_number', 'name', 'chart_of_accounts__name')
    raw_id_fields = ('parent_account',)
    readonly_fields = ('current_balance',)


@admin.register(TaxRate)
class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'rate', 'tax_type', 'is_active')
    list_filter = ('tax_type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_system')
    list_filter = ('is_system',)
    search_fields = ('code', 'name')


class TransactionLineInline(admin.TabularInline):
    model = TransactionLine
    extra = 1
    min_num = 2
    readonly_fields = ('amount',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('document_number', 'date', 'document_type', 'description', 'is_posted', 'is_reversed')
    list_filter = ('document_type', 'date', 'is_posted', 'is_reversed')
    search_fields = ('document_number', 'description', 'reference')
    inlines = [TransactionLineInline]
    readonly_fields = ('transaction_id', 'created_at', 'updated_at', 'is_balanced')
    fieldsets = (
        (None, {
            'fields': ('transaction_id', 'document_number', 'date', 'posting_date', 'document_type', 'is_posted', 'is_reversed')
        }),
        ('Description', {
            'fields': ('description', 'reference')
        }),
        ('Status', {
            'fields': ('created_by', 'created_at', 'updated_at', 'reversal_reference')
        }),
    )
    
    def is_balanced(self, obj):
        return obj.is_balanced()
    is_balanced.boolean = True


@admin.register(TransactionLine)
class TransactionLineAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'account', 'side', 'amount', 'tax_rate', 'tax_amount')
    list_filter = ('side', 'tax_rate', 'account__account_type')
    search_fields = ('transaction__document_number', 'account__account_number', 'description')
    raw_id_fields = ('transaction', 'account')


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'journal_type', 'is_active')
    list_filter = ('journal_type', 'is_active')
    search_fields = ('code', 'name')


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('journal', 'entry_number', 'transaction', 'date')
    list_filter = ('journal', 'date')
    search_fields = ('entry_number', 'transaction__document_number')
    raw_id_fields = ('transaction',)


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'period_type', 'fiscal_year', 'is_closed')
    list_filter = ('period_type', 'fiscal_year', 'is_closed')
    search_fields = ('name',)


@admin.register(ClosingEntry)
class ClosingEntryAdmin(admin.ModelAdmin):
    list_display = ('period', 'from_account', 'to_account', 'amount', 'created_at')
    list_filter = ('period', 'created_at')
    search_fields = ('period__name', 'from_account__account_number', 'to_account__account_number')
    raw_id_fields = ('transaction',)


@admin.register(Reconciliation)
class ReconciliationAdmin(admin.ModelAdmin):
    list_display = ('account', 'statement_date', 'statement_balance', 'reconciled_balance', 'difference', 'is_reconciled')
    list_filter = ('account', 'statement_date', 'is_reconciled')
    search_fields = ('account__account_number', 'notes')


@admin.register(ReconciliationItem)
class ReconciliationItemAdmin(admin.ModelAdmin):
    list_display = ('reconciliation', 'transaction', 'statement_line', 'amount', 'is_reconciled')
    list_filter = ('is_reconciled',)
    search_fields = ('reconciliation__account__account_number', 'transaction__document_number')
    raw_id_fields = ('reconciliation', 'transaction')
