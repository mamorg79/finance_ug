"""
URL configuration for the reports module.
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Standard reports
    path('balance-sheet/', views.balance_sheet, name='balance_sheet'),
    path('profit-loss/', views.profit_loss, name='profit_loss'),
    path('tax-report/', views.tax_report, name='tax_report'),
    path('account-statement/', views.account_statement, name='account_statement'),
    path('account-statement/<int:account_id>/', views.account_statement, name='account_statement_by_id'),
    path('general-ledger/', views.general_ledger_report, name='general_ledger'),
    path('trial-balance/', views.trial_balance_report, name='trial_balance'),
    path('aging-report/', views.aging_report, name='aging_report'),
    path('dashboard/', views.dashboard_report, name='dashboard_report'),
    
    # Report management
    path('templates/', views.report_template_list, name='report_template_list'),
    path('saved/', views.saved_report_list, name='saved_report_list'),
]
