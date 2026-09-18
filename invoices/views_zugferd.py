"""
Views for ZUGFeRD electronic invoice functionality.
Handles export, import, configuration, and transmission of ZUGFeRD invoices.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, FileResponse
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files import File
from django.utils import timezone
from django.db.models import Q
from django.conf import settings
import io
import os
import uuid

from .models import Invoice
from .models_zugferd import ZugferdInvoice, ZugferdConfig, ZugferdTransmission, ZugferdProfile
from accounting.models import Account
from contacts.models import Contact


@login_required
def zugferd_dashboard(request):
    """ZUGFeRD dashboard showing overview of ZUGFeRD invoices."""
    # Get ZUGFeRD invoices
    zugferd_invoices = ZugferdInvoice.objects.filter(
        invoice__created_by=request.user
    ).order_by('-created_at')
    
    # Get configuration
    config = ZugferdConfig.objects.filter(created_by=request.user).first()
    
    # Get statistics
    exported_count = zugferd_invoices.filter(is_exported=True).count()
    imported_count = zugferd_invoices.filter(is_imported=True).count()
    total_count = zugferd_invoices.count()
    
    # Get recent transmissions
    transmissions = ZugferdTransmission.objects.filter(
        zugferd_invoice__invoice__created_by=request.user
    ).order_by('-created_at')[:10]
    
    context = {
        'page_title': 'ZUGFeRD Dashboard',
        'zugferd_invoices': zugferd_invoices,
        'config': config,
        'exported_count': exported_count,
        'imported_count': imported_count,
        'total_count': total_count,
        'transmissions': transmissions,
    }
    
    return render(request, 'invoices/zugferd_dashboard.html', context)


@login_required
def zugferd_config(request):
    """Manage ZUGFeRD configuration."""
    config, created = ZugferdConfig.objects.get_or_create(
        created_by=request.user,
        defaults={
            'company_name': 'Finance UG',
            'company_address': 'Musterstraße 1',
            'company_city': 'Musterstadt',
            'company_postal_code': '12345',
            'company_country': 'DE',
            'vat_number': 'DE123456789',
            'email_from': 'buchhaltung@finance-ug.de',
        }
    )
    
    if request.method == 'POST':
        # Update configuration from form
        config.company_name = request.POST.get('company_name', config.company_name)
        config.company_address = request.POST.get('company_address', config.company_address)
        config.company_city = request.POST.get('company_city', config.company_city)
        config.company_postal_code = request.POST.get('company_postal_code', config.company_postal_code)
        config.company_country = request.POST.get('company_country', config.company_country)
        config.vat_number = request.POST.get('vat_number', config.vat_number)
        config.tax_number = request.POST.get('tax_number', config.tax_number)
        config.email_from = request.POST.get('email_from', config.email_from)
        config.email_subject = request.POST.get('email_subject', config.email_subject)
        config.email_body = request.POST.get('email_body', config.email_body)
        config.peppol_id = request.POST.get('peppol_id', config.peppol_id)
        config.peppol_enabled = request.POST.get('peppol_enabled', '').lower() == 'on'
        
        # Default profile
        profile_id = request.POST.get('default_profile')
        if profile_id:
            try:
                config.default_profile_id = profile_id
            except:
                pass
        
        config.save()
        messages.success(request, 'ZUGFeRD-Konfiguration erfolgreich gespeichert!')
        return redirect('invoices:zugferd_config')
    
    # Get available profiles
    profiles = ZugferdProfile.objects.all()
    
    context = {
        'page_title': 'ZUGFeRD-Konfiguration',
        'config': config,
        'profiles': profiles,
    }
    
    return render(request, 'invoices/zugferd_config.html', context)


@login_required
def export_zugferd(request, invoice_id):
    """Export an invoice as ZUGFeRD XML."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    # Get or create ZUGFeRD invoice
    zugferd_invoice, created = ZugferdInvoice.objects.get_or_create(
        invoice=invoice,
        defaults={
            'profile': ZugferdProfile.objects.filter(code='extended').first() or 
                      ZugferdProfile.objects.first(),
            'invoice_type_code': '380',
            'created_by': request.user,
        }
    )
    
    if request.method == 'POST':
        # Update profile if specified
        profile_id = request.POST.get('profile')
        if profile_id:
            try:
                zugferd_invoice.profile_id = profile_id
                zugferd_invoice.save()
            except:
                pass
        
        # Generate and download XML
        try:
            xml_content = zugferd_invoice.generate_xml()
            
            # Mark as exported
            zugferd_invoice.is_exported = True
            zugferd_invoice.save()
            
            # Return XML file
            response = HttpResponse(xml_content, content_type='application/xml')
            response['Content-Disposition'] = f'attachment; filename="ZUGFeRD_{invoice.invoice_number}.xml"'
            return response
            
        except Exception as e:
            messages.error(request, f'Fehler beim Generieren der ZUGFeRD-Datei: {str(e)}')
            return redirect('invoices:invoice_detail', invoice_id=invoice.id)
    
    # Get available profiles
    profiles = ZugferdProfile.objects.all()
    
    context = {
        'page_title': f"ZUGFeRD Export: {invoice.invoice_number}",
        'invoice': invoice,
        'zugferd_invoice': zugferd_invoice,
        'profiles': profiles,
    }
    
    return render(request, 'invoices/zugferd_export.html', context)


@login_required
def export_zugferd_direct(request, invoice_id):
    """Direct export of ZUGFeRD XML without intermediate page."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    # Get or create ZUGFeRD invoice
    zugferd_invoice, created = ZugferdInvoice.objects.get_or_create(
        invoice=invoice,
        defaults={
            'profile': ZugferdProfile.objects.filter(code='extended').first() or 
                      ZugferdProfile.objects.first(),
            'invoice_type_code': '380',
            'created_by': request.user,
        }
    )
    
    try:
        xml_content = zugferd_invoice.generate_xml()
        
        # Mark as exported
        zugferd_invoice.is_exported = True
        zugferd_invoice.save()
        
        # Return XML file
        response = HttpResponse(xml_content, content_type='application/xml')
        response['Content-Disposition'] = f'attachment; filename="ZUGFeRD_{invoice.invoice_number}.xml"'
        return response
        
    except Exception as e:
        messages.error(request, f'Fehler beim Generieren der ZUGFeRD-Datei: {str(e)}')
        return redirect('invoices:invoice_detail', invoice_id=invoice.id)


@login_required
def import_zugferd(request):
    """Import a ZUGFeRD XML file."""
    if request.method == 'POST':
        xml_file = request.FILES.get('xml_file')
        
        if not xml_file:
            messages.error(request, 'Bitte wählen Sie eine XML-Datei aus!')
            return redirect('invoices:import_zugferd')
        
        try:
            # Read XML content
            xml_content = xml_file.read().decode('utf-8')
            
            # Create a temporary invoice
            temp_invoice = Invoice.objects.create(
                invoice_id=uuid.uuid4(),
                invoice_number=f"IMP-{uuid.uuid4().hex[:8].upper()}",
                invoice_type_id=1,  # Default invoice type
                status_id=1,  # Draft status
                date=timezone.now().date(),
                created_by=request.user,
            )
            
            # Create ZUGFeRD invoice
            zugferd_invoice = ZugferdInvoice.objects.create(
                invoice=temp_invoice,
                profile=ZugferdProfile.objects.filter(code='extended').first() or 
                        ZugferdProfile.objects.first(),
                invoice_type_code='380',
                created_by=request.user,
            )
            
            # Import from XML
            success = zugferd_invoice.import_from_xml(xml_content)
            
            if success:
                # Save XML file
                xml_filename = f'zugferd_import_{temp_invoice.invoice_number}.xml'
                zugferd_invoice.xml_file.save(
                    xml_filename,
                    ContentFile(xml_content.encode('utf-8'))
                )
                zugferd_invoice.is_imported = True
                zugferd_invoice.save()
                
                messages.success(request, f'ZUGFeRD-Rechnung erfolgreich importiert: {temp_invoice.invoice_number}')
                return redirect('invoices:invoice_detail', invoice_id=temp_invoice.id)
            else:
                # Clean up if import failed
                temp_invoice.delete()
                messages.error(request, 'Fehler beim Importieren der ZUGFeRD-Datei!')
                
        except Exception as e:
            messages.error(request, f'Fehler beim Importieren: {str(e)}')
    
    context = {
        'page_title': 'ZUGFeRD importieren',
    }
    
    return render(request, 'invoices/zugferd_import.html', context)


@login_required
def send_zugferd_email(request, invoice_id):
    """Send ZUGFeRD invoice via email."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    zugferd_invoice = get_object_or_404(ZugferdInvoice, invoice=invoice)
    config = ZugferdConfig.objects.filter(created_by=request.user).first()
    
    if not config:
        messages.error(request, 'Bitte konfigurieren Sie zuerst ZUGFeRD in den Einstellungen!')
        return redirect('invoices:zugferd_config')
    
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email', '')
        
        if not recipient_email:
            messages.error(request, 'Bitte geben Sie eine Empfänger-E-Mail-Adresse ein!')
            return redirect('invoices:send_zugferd_email', invoice_id=invoice.id)
        
        try:
            # Generate XML
            xml_content = zugferd_invoice.generate_xml()
            
            # Save XML file
            xml_filename = f'zugferd_{invoice.invoice_number}.xml'
            zugferd_invoice.xml_file.save(
                xml_filename,
                ContentFile(xml_content.encode('utf-8'))
            )
            zugferd_invoice.is_exported = True
            zugferd_invoice.save()
            
            # Create transmission record
            transmission = ZugferdTransmission.objects.create(
                zugferd_invoice=zugferd_invoice,
                method='email',
                recipient_email=recipient_email,
                status='sent',
                sent_at=timezone.now(),
                created_by=request.user,
            )
            
            # TODO: Actually send email with attachment
            # For now, we'll just record the transmission
            # In a real implementation, you would use Django's send_mail
            # with the XML as an attachment
            
            messages.success(request, f'ZUGFeRD-Rechnung {invoice.invoice_number} wurde zum Versand vorbereitet!')
            return redirect('invoices:invoice_detail', invoice_id=invoice.id)
            
        except Exception as e:
            messages.error(request, f'Fehler beim Senden: {str(e)}')
    
    context = {
        'page_title': f"ZUGFeRD per E-Mail senden: {invoice.invoice_number}",
        'invoice': invoice,
        'zugferd_invoice': zugferd_invoice,
        'config': config,
    }
    
    return render(request, 'invoices/zugferd_send_email.html', context)


@login_required
def zugferd_invoice_list(request):
    """List all ZUGFeRD invoices."""
    zugferd_invoices = ZugferdInvoice.objects.filter(
        invoice__created_by=request.user
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter == 'exported':
        zugferd_invoices = zugferd_invoices.filter(is_exported=True)
    elif status_filter == 'imported':
        zugferd_invoices = zugferd_invoices.filter(is_imported=True)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        zugferd_invoices = zugferd_invoices.filter(
            Q(invoice__invoice_number__icontains=search_query) |
            Q(invoice__customer__name__icontains=search_query)
        )
    
    paginator = Paginator(zugferd_invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'ZUGFeRD-Rechnungen',
        'zugferd_invoices': page_obj,
        'selected_status': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'invoices/zugferd_invoice_list.html', context)


@login_required
def zugferd_invoice_detail(request, zugferd_id):
    """Show ZUGFeRD invoice details."""
    zugferd_invoice = get_object_or_404(ZugferdInvoice, pk=zugferd_id, invoice__created_by=request.user)
    
    # Get transmissions
    transmissions = ZugferdTransmission.objects.filter(
        zugferd_invoice=zugferd_invoice
    ).order_by('-created_at')
    
    context = {
        'page_title': f"ZUGFeRD: {zugferd_invoice.invoice.invoice_number}",
        'zugferd_invoice': zugferd_invoice,
        'transmissions': transmissions,
    }
    
    return render(request, 'invoices/zugferd_invoice_detail.html', context)


@login_required
def download_zugferd_xml(request, zugferd_id):
    """Download ZUGFeRD XML file."""
    zugferd_invoice = get_object_or_404(ZugferdInvoice, pk=zugferd_id, invoice__created_by=request.user)
    
    if not zugferd_invoice.xml_file:
        # Generate XML if not exists
        xml_content = zugferd_invoice.generate_xml()
        xml_filename = f'zugferd_{zugferd_invoice.invoice.invoice_number}.xml'
        zugferd_invoice.xml_file.save(
            xml_filename,
            ContentFile(xml_content.encode('utf-8'))
        )
    
    # Return file
    try:
        file_path = zugferd_invoice.xml_file.path
        if default_storage.exists(file_path):
            with default_storage.open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/xml')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
    except:
        pass
    
    # Fallback: generate and return XML
    xml_content = zugferd_invoice.generate_xml()
    response = HttpResponse(xml_content, content_type='application/xml')
    response['Content-Disposition'] = f'attachment; filename="ZUGFeRD_{zugferd_invoice.invoice.invoice_number}.xml"'
    return response


@login_required
def create_hybrid_pdf(request, invoice_id):
    """Create hybrid PDF with embedded ZUGFeRD XML."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    zugferd_invoice = get_object_or_404(ZugferdInvoice, invoice=invoice)
    
    try:
        # Generate XML
        xml_content = zugferd_invoice.generate_xml()
        
        # Create hybrid PDF
        # Note: This is a simplified implementation
        # A full implementation would require embedding XML in PDF metadata
        # or as an attachment using a library like PyPDF2 or pdfrw
        
        success = zugferd_invoice.create_hybrid_pdf(None)
        
        if success:
            zugferd_invoice.save()
            messages.success(request, 'Hybrid-PDF erfolgreich erstellt!')
        else:
            messages.error(request, 'Fehler beim Erstellen der Hybrid-PDF!')
            
    except Exception as e:
        messages.error(request, f'Fehler: {str(e)}')
    
    return redirect('invoices:invoice_detail', invoice_id=invoice.id)


@login_required
def transmission_list(request):
    """List all ZUGFeRD transmissions."""
    transmissions = ZugferdTransmission.objects.filter(
        zugferd_invoice__invoice__created_by=request.user
    ).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        transmissions = transmissions.filter(status=status_filter)
    
    # Filter by method
    method_filter = request.GET.get('method')
    if method_filter:
        transmissions = transmissions.filter(method=method_filter)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        transmissions = transmissions.filter(
            Q(zugferd_invoice__invoice__invoice_number__icontains=search_query) |
            Q(recipient_email__icontains=search_query)
        )
    
    paginator = Paginator(transmissions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'ZUGFeRD-Übertragungen',
        'transmissions': page_obj,
        'selected_status': status_filter,
        'selected_method': method_filter,
        'search_query': search_query,
    }
    
    return render(request, 'invoices/transmission_list.html', context)


@login_required
def transmission_detail(request, transmission_id):
    """Show transmission details."""
    transmission = get_object_or_404(
        ZugferdTransmission,
        pk=transmission_id,
        zugferd_invoice__invoice__created_by=request.user
    )
    
    context = {
        'page_title': f"Übertragung {transmission.transmission_id}",
        'transmission': transmission,
    }
    
    return render(request, 'invoices/transmission_detail.html', context)


@login_required
def get_zugferd_status(request, invoice_id):
    """AJAX endpoint to get ZUGFeRD status for an invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    zugferd_invoice = ZugferdInvoice.objects.filter(invoice=invoice).first()
    
    if zugferd_invoice:
        data = {
            'has_zugferd': True,
            'is_exported': zugferd_invoice.is_exported,
            'is_imported': zugferd_invoice.is_imported,
            'profile': zugferd_invoice.profile.code if zugferd_invoice.profile else None,
            'transmissions': ZugferdTransmission.objects.filter(
                zugferd_invoice=zugferd_invoice
            ).count(),
        }
    else:
        data = {
            'has_zugferd': False,
            'is_exported': False,
            'is_imported': False,
            'profile': None,
            'transmissions': 0,
        }
    
    return JsonResponse(data)


@login_required
def preview_zugferd_xml(request, invoice_id):
    """Preview ZUGFeRD XML in browser."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    zugferd_invoice, created = ZugferdInvoice.objects.get_or_create(
        invoice=invoice,
        defaults={
            'profile': ZugferdProfile.objects.filter(code='extended').first() or 
                      ZugferdProfile.objects.first(),
            'invoice_type_code': '380',
            'created_by': request.user,
        }
    )
    
    try:
        xml_content = zugferd_invoice.generate_xml()
        
        return HttpResponse(xml_content, content_type='application/xml')
        
    except Exception as e:
        messages.error(request, f'Fehler beim Generieren der Vorschau: {str(e)}')
        return redirect('invoices:invoice_detail', invoice_id=invoice.id)
