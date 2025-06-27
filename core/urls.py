from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from . import views
from core import views as core_views


urlpatterns = [
    path('', views.loginView, name='login'),
    path('logout/', views.logoutView, name='logout'),
    path('superadmin/', include("superadmin.urls")),
    path('company/', include('company.urls')),
    path('media/<path:path>', core_views.protectedDocument, name='protected_document'),
    path('employee/', include('employee.urls')),

    #password reset
    path('password_reset/', core_views.password_reset_request, name='password_reset'),
    path('password_reset/<uidb64>/<token>/', core_views.password_reset_confirm, name='password_reset_confirm'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)