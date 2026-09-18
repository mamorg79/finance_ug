from django.contrib import admin
from .models_zugferd import ZugferdProfile, ZugferdInvoice, ZugferdConfig, ZugferdTransmission


@admin.register(ZugferdProfile)
class ZugferdProfileAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'min_version', 'max_version')
    list_filter = ('min_version', 'max_version')
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(ZugferdInvoice)
class ZugferdInvoiceAdmin(admin.ModelAdmin):
    list_display = ('zugferd_id', 'invoice', 'profile', 'invoice_type_code', 'is_exported', 'is_imported', 'created_at')
    list_filter = ('is_exported', 'is_imported', 'profile', 'invoice_type_code')
    search_fields = ('zugferd_id', 'invoice__invoice_number', 'invoice__customer__name')
    raw_id_fields = ('invoice', 'profile')
    date_hierarchy = 'created_at'
    readonly_fields = ('zugferd_id', 'created_at', 'updated_at')


@admin.register(ZugferdConfig)
class ZugferdConfigAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'vat_number', 'peppol_enabled', 'created_by', 'created_at')
    list_filter = ('peppol_enabled', 'company_country')
    search_fields = ('company_name', 'vat_number', 'peppol_id')
    raw_id_fields = ('created_by', 'default_profile')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ZugferdTransmission)
class ZugferdTransmissionAdmin(admin.ModelAdmin):
    list_display = ('transmission_id', 'zugferd_invoice', 'method', 'status', 'recipient_email', 'sent_at', 'created_at')
    list_filter = ('method', 'status', 'sent_at', 'created_at')
    search_fields = ('transmission_id', 'zugferd_invoice__zugferd_id', 'recipient_email', 'recipient_peppol_id')
    raw_id_fields = ('zugferd_invoice', 'created_by')
    date_hierarchy = 'created_at'
    readonly_fields = ('transmission_id', 'created_at', 'updated_at')
