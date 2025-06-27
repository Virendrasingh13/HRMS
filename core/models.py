from django.db import models
from datetime import date
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email=models.EmailField(unique=True)
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    class Role(models.TextChoices):
        SUPERADMIN = 'SUPERADMIN', _('SuperAdmin')
        COMPANY = 'COMPANY', _('Company')
        EMPLOYEE = 'EMPLOYEE', _('Employee')

    role = models.CharField(max_length=20, choices=Role.choices)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Inactive')
    

class Country(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)

    def __str__(self):
        return self.name

class Company(models.Model):
    STATUS_CHOICES= [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    company_name= models.CharField(max_length=100, unique=False)
    admin_name = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Inactive') 
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='company_country')
    created_at = models.DateTimeField(auto_now_add=True)
    company_admin = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='company_admin', null=True, blank=True
    )
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)

def company_directory_path(instance, filename):
    from django.utils.text import slugify
    return f'company_documents/{slugify(instance.company_id.company_name)}/{filename}'

class CompanyDocument(models.Model):
    STATUS_CHOICES= [
        ('Approve', 'Approve'),
        ('Under Review', 'Under Review'),
        ('Rejected', 'Rejected'),
    ]
    name = models.CharField(max_length=50, null=True, blank=True) 
    company_id = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to=company_directory_path, null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Under Review') 
    category = models.CharField(max_length=50, null=True, blank=True)  
    description = models.TextField(null=True, blank=True)
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)


    def __str__(self):
        return f"{self.company_id} - {self.document.name}"
    

class Employee(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]
    WORK_LOCATION_CHOICES = [
        ('On-site', 'On-site'),
        ('Remote', 'Remote'),
        ('Hybrid', 'Hybrid'),
    ]
    HIRE_PERSON_CHOICES = [
        ('Employee', 'Employee'),
        ('Contractor', 'Contractor'),
        ('Personal Profile', 'Personal Profile'),
    ]
    CONTRACTOR_TYPE_CHOICES = [
        ('Pay as go', 'Pay as go'),
        ('Fixed rate', 'Fixed rate'),
        ('Milestone', 'Milestone'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employees', null=True, blank=True)
    country_id = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='employee_country', null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Inactive')
    contract_duration = models.CharField(max_length=50, default='0')
    notice_period = models.CharField(max_length=50, null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now, null=True, blank=True)
    # start_date = models.DateField(default=date.today)
    photo = models.ImageField(upload_to='employee_photos/', null=True, blank=True)
    hire_person_type = models.CharField(max_length=50, choices=HIRE_PERSON_CHOICES, default='Contractor') #(employee,contractor,project)
    contractor_type = models.CharField(max_length=50, choices=CONTRACTOR_TYPE_CHOICES, null=True, blank=True) #(pay_as_go, milestone, fixedrate)
    work_location = models.CharField(max_length=10, choices=WORK_LOCATION_CHOICES, default='On-site') #(remote, onsite and hybrid)
    phone_number = models.CharField(max_length=15, null=True, blank=True) 
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)


class EmployeeDocument(models.Model):
    STATUS_CHOICES = [
        ('Approve', 'Approve'),
        ('Under Review', 'Under Review'),
        ('Rejected', 'Rejected'),
    ]
    name = models.CharField(max_length=50, null=True, blank=True, ) 
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(upload_to='employee_documents/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Under Review') 
    category = models.CharField(max_length=50, null=True, blank=True)  
    description = models.TextField(null=True, blank=True)
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)


    def __str__(self):
        return f"{self.employee.user.username} - {self.document.name}"
    



class Milestone(models.Model):
    employee=models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='milestones', null=True, blank=True)
    title=models.CharField(max_length=50, null=True, blank=True)
    salary_per_hour=models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date=models.DateField(default=date.today)
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)


class Project(models.Model):
    employee=models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='project', null=True, blank=True)
    name=models.CharField(max_length=50, null=True, blank=True)
    salary_per_hour=models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(null=True, blank=True)
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)


class Payment(models.Model):
    PAYMENT_CYCLE_CHOICES = [
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
        ('Bi-weekly', 'Bi-weekly'),
        ('Twice in month', 'Twice in month'),
    ]
    employee=models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='payment')
    payment_cycle = models.CharField(max_length=50, choices=PAYMENT_CYCLE_CHOICES, default='Monthly')
    payment_frequency = models.CharField(max_length=50, default='1') # if payment_cycle is bi-weekly then it is day or if cycle is monthly then it is date 
    salary_per_hour = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_salary_date = models.DateTimeField(default=timezone.now)
    next_salary_date = models.CharField(max_length=50, default='1') 
    last_salary_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_deleted=models.BooleanField(default=False)
    is_active=models.BooleanField(default=True)
    modified_at=models.DateTimeField(auto_now=True , null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True , null=True, blank=True)
