"""
Migration for creating ZUGFeRD models and initial data.
"""
from django.db import migrations, models
import uuid


def create_zugferd_profiles(apps, schema_editor):
    """Create default ZUGFeRD profiles."""
    ZugferdProfile = apps.get_model('invoices', 'ZugferdProfile')
    
    profiles = [
        {
            'name': 'Basic',
            'code': 'basic',
            'description': 'Minimales ZUGFeRD-Profil für einfache Rechnungen',
            'min_version': '2.0',
            'max_version': '2.0',
        },
        {
            'name': 'EN16931',
            'code': 'en16931',
            'description': 'EU-Standard für elektronische Rechnungen (EN 16931)',
            'min_version': '2.0',
            'max_version': '2.0',
        },
        {
            'name': 'Extended',
            'code': 'extended',
            'description': 'Erweitertes ZUGFeRD-Profil mit vollständigen Daten',
            'min_version': '2.0',
            'max_version': '2.0',
        },
    ]
    
    for profile_data in profiles:
        ZugferdProfile.objects.create(**profile_data)


def delete_zugferd_profiles(apps, schema_editor):
    """Delete ZUGFeRD profiles."""
    ZugferdProfile = apps.get_model('invoices', 'ZugferdProfile')
    ZugferdProfile.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('invoices', '0001_initial'),
    ]
    
    operations = [
        # Create ZugferdProfile model
        migrations.CreateModel(
            name='ZugferdProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Name')),
                ('code', models.CharField(max_length=20, unique=True, verbose_name='Code')),
                ('description', models.TextField(blank=True, verbose_name='Beschreibung')),
                ('min_version', models.CharField(default='2.0', max_length=20, verbose_name='Minimale Version')),
                ('max_version', models.CharField(default='2.0', max_length=20, verbose_name='Maximale Version')),
            ],
            options={
                'verbose_name': 'ZUGFeRD-Profil',
                'verbose_name_plural': 'ZUGFeRD-Profile',
            },
        ),
        
        # Create ZugferdInvoice model
        migrations.CreateModel(
            name='ZugferdInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zugferd_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='ZUGFeRD-ID')),
                ('invoice_type_code', models.CharField(default='380', help_text='Rechnungstyp Code (380 = Rechnung, 381 = Gutschrift)', max_length=10, verbose_name='Rechnungstyp Code')),
                ('is_exported', models.BooleanField(default=False, help_text='Als ZUGFeRD exportiert', verbose_name='Exportiert')),
                ('is_imported', models.BooleanField(default=False, help_text='Aus ZUGFeRD importiert', verbose_name='Importiert')),
                ('xml_file', models.FileField(blank=True, help_text='ZUGFeRD XML-Datei', null=True, upload_to='zugferd/xml/', verbose_name='XML-Datei')),
                ('pdf_file', models.FileField(blank=True, help_text='ZUGFeRD PDF-Datei (Hybrid)', null=True, upload_to='zugferd/pdfs/', verbose_name='PDF-Datei')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
                ('invoice', models.OneToOneField(on_delete=models.CASCADE, related_name='zugferd_invoice', to='invoices.Invoice', verbose_name='Rechnung')),
                ('profile', models.ForeignKey(on_delete=models.PROTECT, related_name='zugferd_invoices', to='invoices.ZugferdProfile', verbose_name='Profil')),
                ('created_by', models.ForeignKey(null=True, on_delete=models.SET_NULL, related_name='created_zugferd_invoices', to='auth.User', verbose_name='Erstellt von')),
            ],
            options={
                'verbose_name': 'ZUGFeRD-Rechnung',
                'verbose_name_plural': 'ZUGFeRD-Rechnungen',
            },
        ),
        
        # Create ZugferdConfig model
        migrations.CreateModel(
            name='ZugferdConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(help_text='Firmenname', max_length=200, verbose_name='Firmenname')),
                ('company_address', models.TextField(help_text='Firmenadresse', verbose_name='Firmenadresse')),
                ('company_city', models.CharField(help_text='Stadt', max_length=100, verbose_name='Stadt')),
                ('company_postal_code', models.CharField(help_text='Postleitzahl', max_length=20, verbose_name='Postleitzahl')),
                ('company_country', models.CharField(default='DE', help_text='Land', max_length=2, verbose_name='Land')),
                ('vat_number', models.CharField(help_text='Umsatzsteuer-IdNr.', max_length=50, verbose_name='USt-IdNr.')),
                ('tax_number', models.CharField(blank=True, help_text='Steuernummer', max_length=50, null=True, verbose_name='Steuernummer')),
                ('email_from', models.EmailField(help_text='Absender E-Mail', max_length=254, verbose_name='Absender E-Mail')),
                ('email_subject', models.CharField(default='Rechnung {invoice_number}', help_text='Betreff für Rechnungs-E-Mails', max_length=200, verbose_name='E-Mail-Betreff')),
                ('email_body', models.TextField(default='Anbei erhalten Sie die Rechnung {invoice_number} im ZUGFeRD-Format.', help_text='E-Mail-Text für Rechnungs-E-Mails', verbose_name='E-Mail-Text')),
                ('peppol_id', models.CharField(blank=True, help_text='Peppol-ID', max_length=100, null=True, verbose_name='Peppol-ID')),
                ('peppol_enabled', models.BooleanField(default=False, help_text='Peppol aktiviert', verbose_name='Peppol aktiviert')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
                ('created_by', models.ForeignKey(null=True, on_delete=models.SET_NULL, related_name='created_zugferd_configs', to='auth.User', verbose_name='Erstellt von')),
                ('default_profile', models.ForeignKey(null=True, on_delete=models.SET_NULL, related_name='default_config', to='invoices.ZugferdProfile', verbose_name='Standard-Profil')),
            ],
            options={
                'verbose_name': 'ZUGFeRD-Konfiguration',
                'verbose_name_plural': 'ZUGFeRD-Konfigurationen',
            },
        ),
        
        # Create ZugferdTransmission model
        migrations.CreateModel(
            name='ZugferdTransmission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transmission_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name='Übertragungs-ID')),
                ('method', models.CharField(choices=[('email', 'E-Mail'), ('peppol', 'Peppol'), ('download', 'Download'), ('api', 'API')], help_text='Übertragungsmethode', max_length=20, verbose_name='Methode')),
                ('recipient_email', models.EmailField(blank=True, help_text='Empfänger E-Mail', max_length=254, null=True, verbose_name='Empfänger E-Mail')),
                ('recipient_peppol_id', models.CharField(blank=True, help_text='Empfänger Peppol-ID', max_length=100, null=True, verbose_name='Empfänger Peppol-ID')),
                ('status', models.CharField(choices=[('pending', 'Ausstehend'), ('sent', 'Gesendet'), ('delivered', 'Zugestellt'), ('failed', 'Fehlgeschlagen'), ('received', 'Empfangen')], default='pending', help_text='Status', max_length=20, verbose_name='Status')),
                ('sent_at', models.DateTimeField(blank=True, help_text='Gesendet am', null=True, verbose_name='Gesendet am')),
                ('delivered_at', models.DateTimeField(blank=True, help_text='Zugestellt am', null=True, verbose_name='Zugestellt am')),
                ('response_status', models.CharField(blank=True, help_text='Antwort-Status', max_length=100, null=True, verbose_name='Antwort-Status')),
                ('response_message', models.TextField(blank=True, help_text='Antwort-Nachricht', verbose_name='Antwort-Nachricht')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Erstellt am')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Aktualisiert am')),
                ('created_by', models.ForeignKey(null=True, on_delete=models.SET_NULL, related_name='created_zugferd_transmissions', to='auth.User', verbose_name='Erstellt von')),
                ('zugferd_invoice', models.ForeignKey(on_delete=models.CASCADE, related_name='transmissions', to='invoices.ZugferdInvoice', verbose_name='ZUGFeRD-Rechnung')),
            ],
            options={
                'verbose_name': 'ZUGFeRD-Übertragung',
                'verbose_name_plural': 'ZUGFeRD-Übertragungen',
                'ordering': ['-created_at'],
            },
        ),
        
        # Add data migration for profiles
        migrations.RunPython(
            code=create_zugferd_profiles,
            reverse_code=delete_zugferd_profiles,
        ),
    ]
