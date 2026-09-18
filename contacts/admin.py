"""
Django admin configuration for contacts models.
"""
from django.contrib import admin
from .models import ContactType, Industry, Country, Contact, ContactPerson, BankAccount


@admin.register(ContactType)
class ContactTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_customer', 'is_supplier', 'is_both')
    list_filter = ('is_customer', 'is_supplier', 'is_both')
    search_fields = ('code', 'name')


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'eu_member')
    list_filter = ('eu_member',)
    search_fields = ('code', 'name')


class ContactPersonInline(admin.TabularInline):
    model = ContactPerson
    extra = 1


class BankAccountInline(admin.TabularInline):
    model = BankAccount
    extra = 1


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('contact_number', 'name', 'contact_type', 'email', 'phone', 'is_active')
    list_filter = ('contact_type', 'is_active', 'country')
    search_fields = ('contact_number', 'name', 'first_name', 'last_name', 'email', 'phone')
    inlines = [ContactPersonInline, BankAccountInline]
    raw_id_fields = ('default_account', 'payment_term')


@admin.register(ContactPerson)
class ContactPersonAdmin(admin.ModelAdmin):
    list_display = ('contact', 'first_name', 'last_name', 'position', 'email', 'phone', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('first_name', 'last_name', 'position', 'email', 'contact__name')
    raw_id_fields = ('contact',)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('contact', 'bank_name', 'iban', 'account_holder', 'is_default')
    list_filter = ('is_default',)
    search_fields = ('bank_name', 'iban', 'bic', 'account_holder', 'contact__name')
    raw_id_fields = ('contact',)
