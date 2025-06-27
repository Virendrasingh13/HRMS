from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views
from employee import views as employee_views

urlpatterns = [
    path('', views.register, name='register'),
    path('business_detail/', views.businessDetail, name='business_detail'),
    path('personal_detail/', views.personalDetail, name='personal_detail'),
    path('application_received/', views.applicationReceived, name='application_received'),

    path('dashboard/', views.companyDashboard, name='company_dashboard'),
    path('employee/', views.companyEmployee, name='company_employee'),
    path('document/', views.companyDocument , name='company_document'),
    
    path('email_verify/', views.emailVerify, name='email_verify'),
    path('verify/<uidb64>/<token>/', views.verifyEmail, name='verify_email'),
    # HIRE PERSON METHOD
    path('hire_person/', views.hirePerson, name='hire_person'),
    path('hire_person/employee/', views.hirePersonEmployee, name='hire_person_employee'),
    # HIRE PERSON CONTRACTOR METHOD
    path('hire_person/contractor/', views.hirePersonContractor, name='hire_person_contractor'),
    path('hire_person/contractor/pay_as_go', views.hirePersonContractorPayAsGo, name='hire_person_contractor_pay_as_go'),
    path('hire_person/contractor/fixed_rate/', views.hirePersonContractorFixedRate, name='hire_person_contractor_fixed_rate'),
    path('hire_person/contractor/milestone/', views.hirePersonContractorMilestone, name='hire_person_contractor_milestone'),
    path('hire_person/personal_profile/', views.hirePersonPersonalProfile, name='hire_person_personal_profile'),   
    
    path('employee/personal_profile/<int:id>/', views.personalProfile, name='personal_profile'),
    

    #company document
    path('documents/upload/', views.companyUploadDocument, name='company_upload_document'),
    path('documents/edit/<int:document_id>/', views.companyEditDocument, name='company_edit_document'),
    path('documents/delete/<int:document_id>/', views.companyDeleteDocument, name='company_delete_document'),

    #payment details
    path('employee/personal_profile/no/<int:id>/', views.submitPaymentDetails, name='submit_payment_details'),
    #employee document
    path('employee/personal_profile/doument/edit/<int:document_id>/<int:employee_id>/' , views.employeeEditDocument, name='company_employee_edit_document'),
    path('company_employee_delete_document/<int:document_id>//<int:employee_id>/', views.employeeDeleteDocument, name= 'company_employee_delete_document'),
    
    #edit employee
    path('employee/edit/<int:id>/', views.companyEditEmployee, name= 'company_edit_employee'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)