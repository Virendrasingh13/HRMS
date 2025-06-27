from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views


urlpatterns = [
    path('dashboard/', views.superadminHome, name='superadmin_home'),
    path('companies/', views.superadminCompanies, name='superadmin_companies'),
    path('countries/', views.superadminCountries, name='superadmin_countries'),


    #Active to Deactive Country
    path('countries/active/<int:country_id>/', views.superadminActiveCountry, name='superadmin_active_country'),
    path('countries/deactive/<int:country_id>/', views.superadminDeactiveCountry, name='superadmin_deactive_country'),
    path('countries/edit/<int:country_id>/', views.superadminEditCountry, name='superadmin_edit_country'),

    # Edit Company
    path('companies/edit/<int:company_id>/', views.superadminEditCompany, name='superadmin_edit_company'),
    path('companies/view/<int:company_id>/', views.superadminEditView, name='superadmin_edit_view'),

    # Edit Document
    path('companies/view/<int:company_id>/documents/edit/<int:document_id>/', views.superadminEditDocument, name='superadmin_edit_document'),
    path('documents/upload/<int:company_id>/', views.superadminUploadDocument, name='superadmin_upload_document'),

    # Delete Company
    path('companies/delete/<int:company_id>/', views.superadminDeleteCompany, name='superadmin_delete_company'),
    path('documents/delete/<int:document_id>/', views.superadminDeleteDocument, name='superadmin_delete_document'),

    path('companies/view/<int:company_id>/employee/<int:employee_id>/', views.paymentDetailsData, name='payment_details_data'),
    path('companies/view/<int:company_id>/employee/no/<int:employee_id>/', views.submitButtonPaymentDetails, name='submit_button_payment_details'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)