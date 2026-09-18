"""
URL configuration for the invoices module.
"""
from django.urls import path
from . import views
from . import views_zugferd

app_name = 'invoices'

urlpatterns = [
    # Invoices
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('<int:invoice_id>/edit/', views.invoice_update, name='invoice_update'),
    path('<int:invoice_id>/delete/', views.invoice_delete, name='invoice_delete'),
    path('<int:invoice_id>/post/', views.invoice_post, name='invoice_post'),
    path('<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    
    # Payments
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/create/<int:invoice_id>/', views.payment_create, name='payment_create_for_invoice'),
    path('payments/<int:payment_id>/delete/', views.payment_delete, name='payment_delete'),
    
    # Recurring Invoices
    path('recurring/', views.recurring_invoice_list, name='recurring_invoice_list'),
    path('recurring/create/', views.recurring_invoice_create, name='recurring_invoice_create'),
    path('recurring/<int:recurring_invoice_id>/', views.recurring_invoice_detail, name='recurring_invoice_detail'),
    
    # Templates
    path('templates/', views.invoice_template_list, name='invoice_template_list'),
    path('templates/create/', views.invoice_template_create, name='invoice_template_create'),
    
    # AJAX endpoints
    path('api/invoice/<int:invoice_id>/', views.get_invoice_data, name='get_invoice_data'),
    path('api/search/', views.invoice_search, name='invoice_search'),
    
    # ZUGFeRD endpoints
    path('zugferd/', views_zugferd.zugferd_dashboard, name='zugferd_dashboard'),
    path('zugferd/config/', views_zugferd.zugferd_config, name='zugferd_config'),
    path('zugferd/export/<int:invoice_id>/', views_zugferd.export_zugferd, name='export_zugferd'),
    path('zugferd/export/direct/<int:invoice_id>/', views_zugferd.export_zugferd_direct, name='export_zugferd_direct'),
    path('zugferd/import/', views_zugferd.import_zugferd, name='import_zugferd'),
    path('zugferd/send/email/<int:invoice_id>/', views_zugferd.send_zugferd_email, name='send_zugferd_email'),
    path('zugferd/invoices/', views_zugferd.zugferd_invoice_list, name='zugferd_invoice_list'),
    path('zugferd/invoices/<int:zugferd_id>/', views_zugferd.zugferd_invoice_detail, name='zugferd_invoice_detail'),
    path('zugferd/download/<int:zugferd_id>/', views_zugferd.download_zugferd_xml, name='download_zugferd_xml'),
    path('zugferd/hybrid/<int:invoice_id>/', views_zugferd.create_hybrid_pdf, name='create_hybrid_pdf'),
    path('zugferd/transmissions/', views_zugferd.transmission_list, name='transmission_list'),
    path('zugferd/transmissions/<int:transmission_id>/', views_zugferd.transmission_detail, name='transmission_detail'),
    path('zugferd/api/status/<int:invoice_id>/', views_zugferd.get_zugferd_status, name='get_zugferd_status'),
    path('zugferd/preview/<int:invoice_id>/', views_zugferd.preview_zugferd_xml, name='preview_zugferd_xml'),
]
