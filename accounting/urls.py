"""
URL configuration for the accounting module.
"""
from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Accounts
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('accounts/<int:account_id>/', views.account_detail, name='account_detail'),
    path('accounts/<int:account_id>/edit/', views.account_update, name='account_update'),
    path('accounts/<int:account_id>/balance/', views.get_account_balance, name='get_account_balance'),
    
    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),
    path('transactions/<int:transaction_id>/edit/', views.transaction_update, name='transaction_update'),
    path('transactions/<int:transaction_id>/delete/', views.transaction_delete, name='transaction_delete'),
    path('transactions/<int:transaction_id>/post/', views.transaction_post, name='transaction_post'),
    path('transactions/<int:transaction_id>/reverse/', views.transaction_reverse, name='transaction_reverse'),
    
    # Journals
    path('journals/', views.journal_list, name='journal_list'),
    path('journals/<int:journal_id>/', views.journal_detail, name='journal_detail'),
    
    # Periods
    path('periods/', views.period_list, name='period_list'),
    path('periods/create/', views.period_create, name='period_create'),
    
    # Reconciliations
    path('reconciliations/', views.reconciliation_list, name='reconciliation_list'),
    path('reconciliations/create/', views.reconciliation_create, name='reconciliation_create'),
    path('reconciliations/<int:reconciliation_id>/', views.reconciliation_detail, name='reconciliation_detail'),
    
    # Reports
    path('trial-balance/', views.trial_balance, name='trial_balance'),
    path('general-ledger/', views.general_ledger, name='general_ledger'),
]
