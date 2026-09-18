"""
Views for the contacts module.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Contact, ContactType, Industry, Country, ContactPerson, BankAccount
from .forms import ContactForm, ContactPersonForm, BankAccountForm, ContactSearchForm
from invoices.models import Invoice


@login_required
def contact_list(request):
    """List all contacts."""
    contacts = Contact.objects.filter(created_by=request.user).order_by('name')
    
    # Filter by type
    contact_type = request.GET.get('type')
    if contact_type:
        if contact_type == 'customer':
            contacts = contacts.filter(contact_type__is_customer=True)
        elif contact_type == 'supplier':
            contacts = contacts.filter(contact_type__is_supplier=True)
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        contacts = contacts.filter(
            Q(name__icontains=search_query) |
            Q(contact_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Get statistics
    total_customers = contacts.filter(contact_type__is_customer=True).count()
    total_suppliers = contacts.filter(contact_type__is_supplier=True).count()
    
    paginator = Paginator(contacts, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Kontaktliste',
        'contacts': page_obj,
        'contact_types': ContactType.objects.all(),
        'selected_type': contact_type,
        'search_query': search_query,
        'total_customers': total_customers,
        'total_suppliers': total_suppliers,
    }
    
    return render(request, 'contacts/contact_list.html', context)


@login_required
def contact_detail(request, contact_id):
    """Show contact details."""
    contact = get_object_or_404(Contact, pk=contact_id, created_by=request.user)
    
    # Get related data
    invoices = Invoice.objects.filter(customer=contact).order_by('-date')[:10]
    contact_persons = ContactPerson.objects.filter(contact=contact).order_by('-is_primary', 'last_name')
    bank_accounts = BankAccount.objects.filter(contact=contact).order_by('-is_default')
    
    context = {
        'page_title': f"Kontakt: {contact.name}",
        'contact': contact,
        'invoices': invoices,
        'contact_persons': contact_persons,
        'bank_accounts': bank_accounts,
    }
    
    return render(request, 'contacts/contact_detail.html', context)


@login_required
def contact_create(request):
    """Create a new contact."""
    if request.method == 'POST':
        form = ContactForm(request.POST, user=request.user)
        
        if form.is_valid():
            contact = form.save(commit=False)
            contact.created_by = request.user
            
            # Generate contact number
            if not contact.contact_number:
                last_contact = Contact.objects.filter(created_by=request.user).order_by('-contact_number').first()
                if last_contact:
                    try:
                        last_num = int(last_contact.contact_number.split('-')[-1])
                        contact.contact_number = f"K-{last_num + 1:06d}"
                    except:
                        contact.contact_number = "K-000001"
                else:
                    contact.contact_number = "K-000001"
            
            contact.save()
            messages.success(request, 'Kontakt erfolgreich erstellt!')
            return redirect('contacts:contact_detail', contact_id=contact.id)
    else:
        form = ContactForm(user=request.user)
    
    context = {
        'page_title': 'Neuen Kontakt erstellen',
        'form': form,
    }
    
    return render(request, 'contacts/contact_form.html', context)


@login_required
def contact_update(request, contact_id):
    """Update an existing contact."""
    contact = get_object_or_404(Contact, pk=contact_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ContactForm(request.POST, instance=contact, user=request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Kontakt erfolgreich aktualisiert!')
            return redirect('contacts:contact_detail', contact_id=contact.id)
    else:
        form = ContactForm(instance=contact, user=request.user)
    
    context = {
        'page_title': f"Kontakt {contact.name} bearbeiten",
        'form': form,
        'contact': contact,
    }
    
    return render(request, 'contacts/contact_form.html', context)


@login_required
def contact_delete(request, contact_id):
    """Delete a contact."""
    contact = get_object_or_404(Contact, pk=contact_id, created_by=request.user)
    
    if request.method == 'POST':
        contact.delete()
        messages.success(request, 'Kontakt erfolgreich gelöscht!')
        return redirect('contacts:contact_list')
    
    context = {
        'page_title': f"Kontakt {contact.name} löschen",
        'contact': contact,
    }
    
    return render(request, 'contacts/contact_confirm_delete.html', context)


@login_required
def get_contact_data(request, contact_id):
    """AJAX endpoint to get contact data."""
    contact = get_object_or_404(Contact, pk=contact_id, created_by=request.user)
    
    data = {
        'name': contact.name,
        'contact_number': contact.contact_number,
        'email': contact.email,
        'phone': contact.phone,
        'address': contact.get_full_address(),
    }
    
    return JsonResponse(data)


@login_required
def contact_search(request):
    """Search contacts."""
    form = ContactSearchForm(request.GET or None)
    
    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        contacts = Contact.objects.filter(created_by=request.user)
        
        if query:
            contacts = contacts.filter(
                Q(name__icontains=query) |
                Q(contact_number__icontains=query) |
                Q(email__icontains=query)
            )
        
        results = [{
            'id': contact.id,
            'name': contact.name,
            'contact_number': contact.contact_number,
            'email': contact.email,
        } for contact in contacts[:10]]
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})
