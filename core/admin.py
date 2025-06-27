from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Country , Company, CompanyDocument , Employee, EmployeeDocument, Milestone, Project, Payment
from django.utils.translation import gettext_lazy as _

# Register your models here.
@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff','status')
    list_filter = ('role', 'is_active', 'is_staff')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role', {'fields': ('role','status')}),
    )

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('company_name','admin_name','job_title' ,'country_id','company_admin', 'status', 'created_at')
    search_fields = ('name', 'country_id__name')
    list_filter = ('status', 'country_id')
    raw_id_fields = ('country_id', 'company_admin')

@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    list_display = ('company_id', 'document', 'uploaded_at', 'status', 'category', 'description')
    search_fields = ('company_id__name', 'category')
    list_filter = ('status', 'category')
    raw_id_fields = ('company_id',)



@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ('name','employee', 'document', 'uploaded_at', 'status', 'category', 'description')
    search_fields = ('employee__user__email', 'category', 'description')
    list_filter = ('status', 'category', 'employee')
    raw_id_fields = ('employee',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'company', 'country_id', 'first_name', 'last_name','phone_number' ,'job_title', 'status', 'contract_duration',
        'notice_period', 'start_date', 'photo',
        'hire_person_type', 'contractor_type', 'work_location'
    )
    search_fields = ('user__email', 'company__company_name', 'first_name', 'last_name', 'job_title')
    list_filter = ('status', 'company', 'country_id', 'hire_person_type', 'contractor_type', 'work_location')
    raw_id_fields = ('user', 'company', 'country_id')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'name', 'salary_per_hour', 'description', 'created_at', 'modified_at')
    search_fields = ('name', 'employee__user__email')  # Assuming Employee has a related User with email
    list_filter = ('salary_per_hour',)


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'title', 'salary_per_hour', 'due_date')
    search_fields = ('title', 'employee__user__email')  # Adjust if needed
    list_filter = ('due_date', 'salary_per_hour')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('employee__user__email','payment_cycle','payment_frequency','salary_per_hour','last_salary_date','is_active','is_deleted','created_at','modified_at',)
    list_filter = ('payment_cycle', 'is_active', 'is_deleted')
    search_fields = ('employee__firstname', 'employee__lastname', 'employee__email')
    raw_id_fields = ('employee',)
    ordering = ('-created_at',)