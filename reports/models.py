"""
Report models for the accounting system.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class ReportTemplate(models.Model):
    """Template for custom reports."""
    template_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    report_type = models.CharField(
        max_length=20,
        choices=[
            ('balance_sheet', 'Bilanz'),
            ('profit_loss', 'GuV'),
            ('trial_balance', 'Summen- und Saldenliste'),
            ('account_statement', 'Kontoauszug'),
            ('tax_report', 'Steuerbericht'),
            ('custom', 'Benutzerdefiniert'),
        ]
    )
    sql_query = models.TextField(blank=True, help_text="SQL-Abfrage für benutzerdefinierte Berichte")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_report_templates'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()})"
    
    class Meta:
        verbose_name = "Berichtsvorlage"
        verbose_name_plural = "Berichtsvorlagen"


class SavedReport(models.Model):
    """Saved report instance."""
    report_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    template = models.ForeignKey(
        ReportTemplate,
        on_delete=models.SET_NULL,
        null=True,
        related_name='saved_reports'
    )
    name = models.CharField(max_length=200)
    report_data = models.JSONField(default=dict, help_text="Gespeicherte Berichts-Daten")
    parameters = models.JSONField(default=dict, help_text="Verwendete Parameter")
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_reports'
    )
    
    def __str__(self):
        return f"{self.name} ({self.generated_at.strftime('%d.%m.%Y %H:%M')})"
    
    class Meta:
        verbose_name = "Gespeicherter Bericht"
        verbose_name_plural = "Gespeicherte Berichte"
        ordering = ['-generated_at']
