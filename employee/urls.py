from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views
from core import views as core_views
from employee import views as employee_views


urlpatterns = [
    path('', views.employee_dashboard, name='employee_dashboard'),
    path('documents/', views.employee_documents, name='employee_documents'),
    path('profile/', employee_views.employee_profile, name='employee_profile'),

    # Employee Documents Upload
    path('documents/upload/<int:employee_id>/<str:source>/', views.employeeUploadDocuments, name='employee_upload_document_with_source'),
    path('documents/upload/<int:employee_id>/', views.employeeUploadDocuments , name='employee_upload_document'),

    # Employee Documents Edit
    path('documents/edit/<int:document_id>/<str:source>/', views.employeeEditDocument, name='employee_edit_document_with_source'),
    path('documents/edit/<int:document_id>/', views.employeeEditDocument, name='employee_edit_document'),

    # Employee Documents Delete
    path('documents/delete/<int:document_id>/<str:source>/', views.employeeDeleteDocument, name='employee_delete_document_with_source'),
    path('documents/delete/<int:document_id>/', views.employeeDeleteDocument, name='employee_delete_document'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)