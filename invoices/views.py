"""
Views for the invoices module.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import uuid
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from .models import (
    Invoice, InvoiceLine, InvoiceStatus, InvoiceType, PaymentTerm,
    Payment, RecurringInvoice, RecurringInvoiceLine, InvoiceTemplate
)
from .forms import (
    InvoiceForm, InvoiceLineForm, InvoiceSearchForm, PaymentForm,
    RecurringInvoiceForm, InvoiceTemplateForm
)
from accounting.models import Account, TaxRate, Transaction
from contacts.models import Contact


@login_required
def invoice_list(request):
    """List all invoices."""
    invoices = Invoice.objects.filter(created_by=request.user).order_by('-date', '-invoice_number')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        invoices = invoices.filter(status__code=status_filter)
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        invoices = invoices.filter(invoice_type__code=type_filter)
    
    # Filter by customer
    customer_filter = request.GET.get('customer')
    if customer_filter:
        invoices = invoices.filter(customer__id=customer_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        invoices = invoices.filter(date__gte=date_from)
    if date_to:
        invoices = invoices.filter(date__lte=date_to)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(reference__icontains=search_query)
        )
    
    # Get statistics
    total_amount = invoices.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    paid_amount = invoices.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
    open_amount = total_amount - paid_amount
    
    paginator = Paginator(invoices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Rechnungsliste',
        'invoices': page_obj,
        'statuses': InvoiceStatus.objects.all(),
        'types': InvoiceType.objects.all(),
        'customers': Contact.objects.filter(created_by=request.user, contact_type__is_customer=True),
        'selected_status': status_filter,
        'selected_type': type_filter,
        'selected_customer': customer_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'total_amount': total_amount,
        'paid_amount': paid_amount,
        'open_amount': open_amount,
    }
    
    return render(request, 'invoices/invoice_list.html', context)


@login_required
def invoice_detail(request, invoice_id):
    """Show invoice details."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    # Get payments
    payments = Payment.objects.filter(invoice=invoice).order_by('-payment_date')
    
    # Get remaining balance
    remaining_balance = invoice.get_balance()
    
    context = {
        'page_title': f"Rechnung {invoice.invoice_number}",
        'invoice': invoice,
        'lines': invoice.lines.all().order_by('line_number'),
        'payments': payments,
        'remaining_balance': remaining_balance,
        'is_overdue': invoice.is_overdue(),
    }
    
    return render(request, 'invoices/invoice_detail.html', context)


@login_required
def invoice_create(request):
    """Create a new invoice."""
    if request.method == 'POST':
        form = InvoiceForm(request.POST, user=request.user)
        line_form = InvoiceLineForm(request.POST, prefix='line')
        
        if form.is_valid():
            # Create invoice
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.invoice_id = uuid.uuid4()
            
            # Generate invoice number
            if not invoice.invoice_number:
                last_invoice = Invoice.objects.filter(created_by=request.user).order_by('-invoice_number').first()
                if last_invoice:
                    try:
                        last_num = int(last_invoice.invoice_number.split('-')[-1])
                        invoice.invoice_number = f"RG-{last_num + 1:06d}"
                    except:
                        invoice.invoice_number = "RG-000001"
                else:
                    invoice.invoice_number = "RG-000001"
            
            invoice.save()
            
            # Create line
            if line_form.is_valid():
                line = line_form.save(commit=False)
                line.invoice = invoice
                line.line_number = 1
                line.save()
                invoice.calculate_totals()
            
            messages.success(request, 'Rechnung erfolgreich erstellt!')
            return redirect('invoices:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm(user=request.user, initial={
            'date': timezone.now().date(),
            'due_date': timezone.now().date() + timezone.timedelta(days=14),
        })
        line_form = InvoiceLineForm(prefix='line')
    
    context = {
        'page_title': 'Neue Rechnung erstellen',
        'form': form,
        'line_form': line_form,
    }
    
    return render(request, 'invoices/invoice_form.html', context)


@login_required
def invoice_update(request, invoice_id):
    """Update an existing invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice, user=request.user)
        
        if form.is_valid():
            invoice = form.save()
            invoice.calculate_totals()
            messages.success(request, 'Rechnung erfolgreich aktualisiert!')
            return redirect('invoices:invoice_detail', invoice_id=invoice.id)
    else:
        form = InvoiceForm(instance=invoice, user=request.user)
    
    context = {
        'page_title': f"Rechnung {invoice.invoice_number} bearbeiten",
        'form': form,
        'invoice': invoice,
    }
    
    return render(request, 'invoices/invoice_form.html', context)


@login_required
def invoice_delete(request, invoice_id):
    """Delete an invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    if request.method == 'POST':
        # Delete related transaction if exists
        if invoice.transaction:
            invoice.transaction.delete()
        
        invoice.delete()
        messages.success(request, 'Rechnung erfolgreich gelöscht!')
        return redirect('invoices:invoice_list')
    
    context = {
        'page_title': f"Rechnung {invoice.invoice_number} löschen",
        'invoice': invoice,
    }
    
    return render(request, 'invoices/invoice_confirm_delete.html', context)


@login_required
def invoice_post(request, invoice_id):
    """Post an invoice (create accounting transaction)."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    if invoice.transaction:
        messages.warning(request, 'Diese Rechnung hat bereits eine Buchung!')
        return redirect('invoices:invoice_detail', invoice_id=invoice.id)
    
    if request.method == 'POST':
        # Create transaction
        transaction = invoice.create_transaction()
        
        # Post transaction
        transaction.is_posted = True
        transaction.save()
        
        # Update account balances
        for line in transaction.lines.all():
            line.account.update_current_balance()
        
        messages.success(request, 'Rechnung erfolgreich gebucht!')
        return redirect('invoices:invoice_detail', invoice_id=invoice.id)
    
    context = {
        'page_title': f"Rechnung {invoice.invoice_number} buchen",
        'invoice': invoice,
    }
    
    return render(request, 'invoices/invoice_confirm_post.html', context)


@login_required
def invoice_pdf(request, invoice_id):
    """Generate PDF for an invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    # Create PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Rechnung_{invoice.invoice_number}.pdf"'
    
    # Create PDF document
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Add header
    story.append(Spacer(1, 20))
    story.append(Paragraph("RECHNUNG", title_style))
    story.append(Spacer(1, 10))
    
    # Company info (placeholder)
    company_info = f"Finance UG<br/>Musterstraße 1<br/>12345 Musterstadt<br/>Deutschland"
    story.append(Paragraph(company_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Invoice info table
    invoice_data = [
        ['Rechnungsnummer:', invoice.invoice_number],
        ['Datum:', invoice.date.strftime('%d.%m.%Y')],
        ['Fälligkeitsdatum:', invoice.due_date.strftime('%d.%m.%Y') if invoice.due_date else ''],
        ['Kundennummer:', invoice.customer.contact_number],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[120, 200])
    invoice_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(invoice_table)
    story.append(Spacer(1, 20))
    
    # Customer info
    story.append(Paragraph("Rechnungsempfänger:", styles['Heading2']))
    customer_info = f"{invoice.customer.name}<br/>"
    if invoice.customer.first_name and invoice.customer.last_name:
        customer_info += f"{invoice.customer.first_name} {invoice.customer.last_name}<br/>"
    if invoice.customer.address_line_1:
        customer_info += f"{invoice.customer.address_line_1}<br/>"
    if invoice.customer.address_line_2:
        customer_info += f"{invoice.customer.address_line_2}<br/>"
    if invoice.customer.postal_code and invoice.customer.city:
        customer_info += f"{invoice.customer.postal_code} {invoice.customer.city}<br/>"
    if invoice.customer.country:
        customer_info += invoice.customer.country.name
    
    story.append(Paragraph(customer_info, styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Invoice lines table
    line_data = [['Pos.', 'Beschreibung', 'Menge', 'Einzelpreis', 'Betrag']]
    for line in invoice.lines.all().order_by('line_number'):
        line_data.append([
            str(line.line_number),
            line.description,
            str(line.quantity),
            f"{line.unit_price|floatformat:2} €",
            f"{line.amount|floatformat:2} €"
        ])
    
    # Add empty rows if needed
    while len(line_data) < 15:
        line_data.append(['', '', '', '', ''])
    
    # Add totals
    line_data.append(['', '', '', 'Nettobetrag:', f"{invoice.subtotal|floatformat:2} €"])
    line_data.append(['', '', '', 'zzgl. MwSt.:', f"{invoice.tax_amount|floatformat:2} €"])
    line_data.append(['', '', '', 'Gesamtbetrag:', f"{invoice.total_amount|floatformat:2} €"])
    
    line_table = Table(line_data, colWidths=[30, 250, 60, 80, 80])
    line_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -3), 1, colors.lightgrey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('FONTWEIGHT', (0, 0), (-1, 0), 'BOLD'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),
        ('FONTWEIGHT', (-2, -3), (-1, -1), 'BOLD'),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 10))
    
    # Payment info
    payment_info = f"Zahlungsbedingung: {invoice.payment_term.name if invoice.payment_term else '14 Tage'}<br/>"
    payment_info += f"Zahlbar bis: {invoice.due_date.strftime('%d.%m.%Y') if invoice.due_date else ''}"
    story.append(Paragraph(payment_info, styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    response.write(buffer.getvalue())
    buffer.close()
    
    return response


@login_required
def payment_list(request):
    """List all payments."""
    payments = Payment.objects.filter(invoice__created_by=request.user).order_by('-payment_date')
    
    # Filter by invoice
    invoice_filter = request.GET.get('invoice')
    if invoice_filter:
        payments = payments.filter(invoice__id=invoice_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        payments = payments.filter(payment_date__gte=date_from)
    if date_to:
        payments = payments.filter(payment_date__lte=date_to)
    
    # Get statistics
    total_paid = payments.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Zahlungsliste',
        'payments': page_obj,
        'invoices': Invoice.objects.filter(created_by=request.user),
        'selected_invoice': invoice_filter,
        'date_from': date_from,
        'date_to': date_to,
        'total_paid': total_paid,
    }
    
    return render(request, 'invoices/payment_list.html', context)


@login_required
def payment_create(request, invoice_id=None):
    """Create a new payment."""
    invoice = None
    if invoice_id:
        invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    if request.method == 'POST':
        form = PaymentForm(request.POST, user=request.user, invoice=invoice)
        
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.payment_id = uuid.uuid4()
            
            if not payment.payment_date:
                payment.payment_date = timezone.now().date()
            
            payment.save()
            
            # Update invoice paid amount
            payment.invoice.paid_amount += payment.amount
            payment.invoice.save()
            
            # Create transaction if requested
            if request.POST.get('create_transaction'):
                payment.create_transaction()
            
            messages.success(request, 'Zahlung erfolgreich erfasst!')
            return redirect('invoices:invoice_detail', invoice_id=payment.invoice.id)
    else:
        form = PaymentForm(user=request.user, invoice=invoice, initial={
            'payment_date': timezone.now().date(),
            'amount': invoice.get_balance() if invoice else None,
        })
    
    context = {
        'page_title': 'Neue Zahlung erfassen',
        'form': form,
        'invoice': invoice,
    }
    
    return render(request, 'invoices/payment_form.html', context)


@login_required
def payment_delete(request, payment_id):
    """Delete a payment."""
    payment = get_object_or_404(Payment, pk=payment_id, invoice__created_by=request.user)
    
    if request.method == 'POST':
        # Delete related transaction if exists
        if payment.transaction:
            payment.transaction.delete()
        
        # Update invoice paid amount
        payment.invoice.paid_amount -= payment.amount
        payment.invoice.save()
        
        payment.delete()
        messages.success(request, 'Zahlung erfolgreich gelöscht!')
        return redirect('invoices:invoice_detail', invoice_id=payment.invoice.id)
    
    context = {
        'page_title': f"Zahlung löschen",
        'payment': payment,
    }
    
    return render(request, 'invoices/payment_confirm_delete.html', context)


@login_required
def recurring_invoice_list(request):
    """List all recurring invoices."""
    recurring_invoices = RecurringInvoice.objects.filter(created_by=request.user).order_by('-start_date')
    
    context = {
        'page_title': 'Wiederkehrende Rechnungen',
        'recurring_invoices': recurring_invoices,
    }
    
    return render(request, 'invoices/recurring_invoice_list.html', context)


@login_required
def recurring_invoice_detail(request, recurring_invoice_id):
    """Show recurring invoice details."""
    recurring_invoice = get_object_or_404(RecurringInvoice, pk=recurring_invoice_id, created_by=request.user)
    
    # Get generated invoices
    generated_invoices = Invoice.objects.filter(
        reference=f"Recurring: {recurring_invoice.template_id}"
    ).order_by('-date')
    
    context = {
        'page_title': f"Wiederkehrende Rechnung: {recurring_invoice.name}",
        'recurring_invoice': recurring_invoice,
        'lines': recurring_invoice.lines.all().order_by('line_number'),
        'generated_invoices': generated_invoices,
    }
    
    return render(request, 'invoices/recurring_invoice_detail.html', context)


@login_required
def recurring_invoice_create(request):
    """Create a new recurring invoice."""
    if request.method == 'POST':
        form = RecurringInvoiceForm(request.POST, user=request.user)
        
        if form.is_valid():
            recurring_invoice = form.save(commit=False)
            recurring_invoice.created_by = request.user
            recurring_invoice.template_id = uuid.uuid4()
            recurring_invoice.save()
            
            messages.success(request, 'Wiederkehrende Rechnung erfolgreich erstellt!')
            return redirect('invoices:recurring_invoice_list')
    else:
        form = RecurringInvoiceForm(user=request.user)
    
    context = {
        'page_title': 'Neue wiederkehrende Rechnung erstellen',
        'form': form,
    }
    
    return render(request, 'invoices/recurring_invoice_form.html', context)


@login_required
def invoice_template_list(request):
    """List all invoice templates."""
    templates = InvoiceTemplate.objects.filter(created_by=request.user)
    
    context = {
        'page_title': 'Rechnungsvorlagen',
        'templates': templates,
    }
    
    return render(request, 'invoices/invoice_template_list.html', context)


@login_required
def invoice_template_create(request):
    """Create a new invoice template."""
    if request.method == 'POST':
        form = InvoiceTemplateForm(request.POST, user=request.user)
        
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.template_id = uuid.uuid4()
            template.save()
            
            messages.success(request, 'Rechnungsvorlage erfolgreich erstellt!')
            return redirect('invoices:invoice_template_list')
    else:
        form = InvoiceTemplateForm(user=request.user)
    
    context = {
        'page_title': 'Neue Rechnungsvorlage erstellen',
        'form': form,
    }
    
    return render(request, 'invoices/invoice_template_form.html', context)


@login_required
def get_invoice_data(request, invoice_id):
    """AJAX endpoint to get invoice data."""
    invoice = get_object_or_404(Invoice, pk=invoice_id, created_by=request.user)
    
    data = {
        'invoice_number': invoice.invoice_number,
        'date': invoice.date.strftime('%d.%m.%Y'),
        'due_date': invoice.due_date.strftime('%d.%m.%Y') if invoice.due_date else None,
        'customer': {
            'name': invoice.customer.name,
            'contact_number': invoice.customer.contact_number,
        },
        'total_amount': str(invoice.total_amount),
        'paid_amount': str(invoice.paid_amount),
        'balance': str(invoice.get_balance()),
        'is_paid': invoice.is_paid(),
        'is_overdue': invoice.is_overdue(),
    }
    
    return JsonResponse(data)


@login_required
def invoice_search(request):
    """Search invoices."""
    form = InvoiceSearchForm(request.GET or None)
    
    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        invoices = Invoice.objects.filter(created_by=request.user)
        
        if query:
            invoices = invoices.filter(
                Q(invoice_number__icontains=query) |
                Q(customer__name__icontains=query) |
                Q(description__icontains=query)
            )
        
        results = [{
            'id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'customer': invoice.customer.name,
            'date': invoice.date.strftime('%d.%m.%Y'),
            'total_amount': str(invoice.total_amount),
            'status': invoice.status.name,
        } for invoice in invoices[:10]]
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})
