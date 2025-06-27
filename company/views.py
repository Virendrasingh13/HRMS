from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
# from core.models import User, Company, Country
from django.contrib.auth import logout
from core.models import Country, User, Company, Employee, Milestone, Project, CompanyDocument , EmployeeDocument, Payment
from django.db.models import Count, Q
from django.contrib import messages
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError
from django.utils import timezone
from datetime import date,datetime, timedelta
import calendar
from django.utils.timezone import make_aware
from django.utils.html import format_html

from django.core.paginator import Paginator
from django.db.models import Case, When, Value, IntegerField, Q

from django.core.validators import validate_email
from django.core.exceptions import ValidationError




# Decorator to check if user is superadmin

def company_admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if getattr(request.user, 'role', None) != 'COMPANY':
            logout(request)
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view



def register(request):
    if request.method == "POST":
        print("Registering user...")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = "COMPANY"
        username = request.POST.get("email")

        try:
            validate_email(email)
        except ValidationError:
            return render(request, 'register.html', {'error_message': 'Invalid email format'})
       
        if not email or not password or not role:
            return render(request, 'register.html', {'error_message': 'All fields are required.'})
       
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error_message': 'Email already exists.'})
       
        try:
            user = User.objects.create_user(email=email, password=password, role=role , username=username)
            user.save()
            print(f"User {email} registered successfully with role {role}")

            # messages.success(request, 'Registration Successfully! Please login')
            # return redirect('login')
            return render(request, 'login.html', {'messages': 'Registration Successfully! Please login'})
        except Exception as e:
            print(f"Error registering user: {e}")
            return render(request, 'register.html', {'error_message': 'Registration failed. Please try again.'})
   
    return render(request, 'register.html')


@company_admin_required
def emailVerify(request):
    if request.user.is_authenticated and request.user.status == 'Active':
        return redirect('business_detail')
    

    token = default_token_generator.make_token(request.user)
    uid = urlsafe_base64_encode(force_bytes(request.user.pk))
    verify_url = request.build_absolute_uri(f"/company/verify/{uid}/{token}/")
    subject = "Verify your email address"
    message = f"Hi,\n\nPlease verify your email by clicking the link below:\n{verify_url}\n\nThank you."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently=True)
    
    # This view can be used to handle email verification logic
    return render(request, 'company/email_verify.html', {'message': 'Please verify your email address.'})


def verifyEmail(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        # user.is_active = True
        user.status = "Active"
        user.save()
        print(f"Email verified for user {user.email}")
        return render(request, 'company/email_verifyed.html', {'message': 'Your email has been verified. You can now log in.'})
    else:
        return render(request, 'company/email_verifyed.html', {'message': 'Verification link is invalid or expired.'})


# @login_required
@company_admin_required
def businessDetail(request):
    if Company.objects.filter(company_admin=request.user).exists():
        return redirect('personal_detail')


    if request.method == "POST":
        company_name=request.POST.get('company_name')
        country_id=request.POST.get('country_id')
        
        try:
            country = Country.objects.get(id=country_id)
            Company.objects.create(company_name=company_name, country_id=country, company_admin=request.user)
            return redirect('personal_detail')

        except Country.DoesNotExist:
            country = None
    
    countries = Country.objects.all()  
    return render(request, 'company/business_detail.html',{'countries': countries})

# @login_required
@company_admin_required
def personalDetail(request):

    company = Company.objects.filter(company_admin=request.user).first()
    # print(company)
    if company and company.admin_name:
        return redirect('application_received')

    if request.method == "POST":
        admin_name = request.POST.get("admin_name")
        job_title = request.POST.get("job_title")
        job_desc = request.POST.get("job_desc")    #job description baki

        company = get_object_or_404(Company, company_admin=request.user)

        # Update the fields
        company.admin_name = admin_name
        company.job_title = job_title
        # company.job_desc = job_desc this field is not present in database
        company.save()
        return redirect('application_received')

    return render(request, 'company/personal_detail.html')


@company_admin_required
def applicationReceived(request):
    company = get_object_or_404(Company, company_admin=request.user)
    if company.status == 'Active':
        return redirect('company_dashboard')

    return render(request, 'company/application_received.html')


# @login_required
@company_admin_required
def companyDashboard(request):
    company = get_object_or_404(Company, company_admin=request.user)
    
    # Full employee queryset for counts
    employees_qs = Employee.objects.select_related('user')\
        .filter(company=company)
    
    active_count = employees_qs.filter(status='Active').count()
    inactive_count = employees_qs.filter(status='Inactive').count()
    total_count = employees_qs.count()

    # Get only 10 most recent employees for display
    employees = employees_qs.order_by('-created_at')[:5]  # Replace 'created_at' if needed

    countries = Country.objects.filter(
        employee_country__company=company
    ).annotate(
        employee_count=Count('employee_country', filter=Q(employee_country__company=company))
    ).distinct()

    context = {
        'employees': employees,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_count': total_count,
        'countries': countries,
        'company_admin_name': company.admin_name
    }

    return render(request, 'company/company_dashboard.html', context)


@company_admin_required
def companyEmployee(request):

    company = get_object_or_404(Company, company_admin=request.user)
    employees = Employee.objects.select_related('user').filter(company=company).order_by('status')
    count = Employee.objects.filter(company=company).count()

    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '').strip()
    #Search logic
    if query:
        employees = employees.filter(
            Q(first_name__icontains=query) 
        )
    # Sorting logic
    if sort == 'name':
        employees = employees.order_by('name')
    else:
        employees = employees.order_by('-created_at')


    # Pagination
    paginator = Paginator(employees, 10)  # Show 10 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    employees = page_obj  # 👈 overwrite employees with the paginated result

    if not page_obj.object_list.exists():
        page_obj = None
    context = {
        'search_query': query,
        'count': count,
        'employees': employees,
        'page_obj': page_obj,
    }
    return render(request,'company/company_employee.html',context)




# HIRE PERSON METHOD
def hirePersonStep1(request, hire_person_type):
    firstname = request.POST.get('firstname')
    lastname = request.POST.get('lastname')
    email = request.POST.get('email')
    employee_country = request.POST.get('employee_country')
    job_title = request.POST.get('job_title')

    try:
        validate_email(email)
    except ValidationError:
        return None, "Invalid email format"

    try:
        # 1. Create user
        user = User.objects.create_user(
            email=email,
            password="Changeme@123",
            role="EMPLOYEE",
            username=email
        )

        # 2. Fetch company & country
        company = get_object_or_404(Company, company_admin=request.user)
        country = Country.objects.get(id=employee_country)

        # 3. Create employee
        employee = Employee.objects.create(
            user=user,
            company=company,
            country_id=country,
            first_name=firstname,
            last_name=lastname,
            job_title=job_title,
            hire_person_type=hire_person_type
        )

        # Send password reset email
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_url = request.build_absolute_uri(f"/password_reset/{uid}/{token}/")
        subject = "Set your password for your new account"
        message = f"Hi,\n\nYou have been hired! Please set your password by clicking the link below:\n{reset_url}\n\nThank you."
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)

        return employee, None
    
    except IntegrityError as e:
        # Likely email already exists
        return None, "A user with that email already exists."

    except Company.DoesNotExist:
        # Unlikely, since get_object_or_404 raises Http404
        return None, "Invalid company reference."

    except Country.DoesNotExist:
        return None, "Selected country is invalid."

    except Exception as e:
        # Catch-all for unexpected issues
        return None, f"An unexpected error occurred: {str(e)}"
    

def hirePersonStep2(request, employee, contractor_type):
    contract_duration=request.POST.get('contract_duration')
    work_location=request.POST.get('work_location')
    notice_period=request.POST.get('notice_period')
    #  GET EMAIL FROM COOCKIES
    # email = request.get_signed_cookie('email', salt='hire_person_email')

    try:
        if not employee.user.email:
            raise ValueError("Email not found in session.")

        employee.contract_duration=contract_duration
        employee.work_location=work_location
        employee.notice_period=notice_period
        employee.contractor_type=contractor_type
        employee.save()

        if contractor_type == 'Pay as go':
            name = request.POST.get('project_name')
            salary_per_hour = request.POST.get('project_salary_per_hour')
            description = request.POST.get('project_desc')
            # if name and salary_per_hour and description:
            Project.objects.create(
                employee=employee,
                name=name,
                salary_per_hour=salary_per_hour,
                description=description,
            )
        
        if contractor_type == 'Milestone':
            i = 1
            while True:
                title = request.POST.get(f'milestone{i}_name')
                salary_per_hour = request.POST.get(f'milestone{i}_salary_per_hour')
                due_date = request.POST.get(f'milestone{i}_due_date')

                if title and salary_per_hour and due_date:
                    Milestone.objects.create(
                        employee=employee,
                        title=title,
                        salary_per_hour=salary_per_hour,
                        due_date=due_date,
                    )
                    i += 1
                else:
                    break

        return employee,None
    
    except Exception as e:
        # Catch-all for unexpected issues
        return None, f"An unexpected error occurred: {str(e)}"




def hirePersonStep3(request, employee):
    start_date=request.POST.get('start_date')
    payment_cycle=request.POST.get('payment_cycle')
    # currency=request.POST.get('currency')        this feild is ref. from the country table
    salary_per_hour=request.POST.get('salary_per_hour')


    input_list = request.POST.getlist('payment_frequency')
    valid_values = [v for v in input_list if v]
    payment_frequency = valid_values[0] if valid_values else None


    try:
        if not employee.user.email:
            raise ValueError("Email not found in session.")

        employee.start_date=start_date
        employee.save()

        today=timezone.now()
        days_in_month=calendar.monthrange(today.year, today.month)[1]

        if payment_cycle == 'Twice in month':
            payment_frequency_date2=request.POST.get('payment_frequency_date2')

            # convert string timezone to date object 
            payment_frequency=make_aware(datetime.strptime(payment_frequency, "%Y-%m-%d"))
            payment_frequency_date2=make_aware(datetime.strptime(payment_frequency_date2, "%Y-%m-%d"))

            day1=payment_frequency.day
            day2=payment_frequency_date2.day

            # If payment date1 and date2 had lesser than 7 days then it gives error
            if (day2 - day1) < 7 or (day1 + days_in_month - day2) < 7:
                employee.user.delete()
                return None, "Payment dates gap should be at least of 7 days"

            # next salary date fixed
            if(today.day <= day1 or today.day> day2):
                next_salary_date=day1
                payment_frequency=day2
            else:
                next_salary_date=day2
                payment_frequency=day1

        elif payment_cycle == 'Monthly':
            # convert string timezone to date object 
            payment_frequency=make_aware(datetime.strptime(payment_frequency, "%Y-%m-%d"))
            payment_frequency=payment_frequency.day
            next_salary_date=payment_frequency
        
        elif payment_cycle == 'Weekly' or payment_cycle == 'Bi-weekly' :

            weekday_map = {
                "monday": 0,
                "tuesday": 1,
                "wednesday": 2,
                "thursday": 3,
                "friday": 4,
                "saturday": 5,
                "sunday": 6,
            }

            target_day_index = weekday_map.get(payment_frequency, None)
            if target_day_index is None:
                employee.user.delete()
                return None, "Invalid payment frequency day."

            curreny_day_index=today.weekday()

            days_until_target = (target_day_index - curreny_day_index) % 7
            if days_until_target == 0:
                days_until_target = 7

            next_salary_date=(today.day+days_until_target)%days_in_month

        else:
            employee.user.delete()
            return None, "Selected payment cycle is not valid!"

        Payment.objects.create(
                employee=employee,
                payment_cycle=payment_cycle,
                payment_frequency=str(payment_frequency),
                salary_per_hour=salary_per_hour,
                last_salary_date=start_date,
                next_salary_date=str(next_salary_date),
            )
        # 'currency': employee.company.country_id.code
        return employee, None
    
    except Exception as e:
        employee.user.delete()
        # Catch-all for unexpected issues
        return None, f"An unexpected error occurred: {str(e)}"



@company_admin_required
def hirePerson(request):
    return render(request,'company/hire_person.html')


@company_admin_required
def hirePersonEmployee(request):
    countries = Country.objects.all()
    if request.method == "POST":

        employee, error = hirePersonStep1(request, 'Employee')
        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_employee.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        
        employee, error = hirePersonStep3(request,employee)
        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_employee.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })

        return redirect('company_dashboard')

        # email = request.get_signed_cookie('email', salt='hire_person_email')
        # THIS LINE GET EMAIL FROM COOCKIES

    return render(request,'company/hire_person_employee.html',{'countries': countries})


# HIRE PERSON CONTRACTOR METHOD
@company_admin_required
def hirePersonContractor(request):
    return render(request,'company/hire_person_contractor.html')


@company_admin_required
def hirePersonContractorPayAsGo(request):
    countries = Country.objects.all()
    if request.method == "POST":
        employee, error = hirePersonStep1(request, 'Contractor')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_pay_as_go.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        

        employee, error = hirePersonStep2(request, employee, 'Pay as go')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_pay_as_go.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        
        employee, error = hirePersonStep3(request,employee)

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_pay_as_go.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })

        return redirect('company_dashboard')


    return render(request,'company/hire_person_contractor_pay_as_go.html',{'countries': countries})


@company_admin_required
def hirePersonContractorFixedRate(request):
    countries = Country.objects.all()
    if request.method == "POST":
        employee, error = hirePersonStep1(request, 'Contractor')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_fixed_rate.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        

        employee, error = hirePersonStep2(request, employee, 'Fixed rate')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_fixed_rate.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        
        employee, error = hirePersonStep3(request,employee)

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_fixed_rate.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })

        return redirect('company_dashboard')

    return render(request,'company/hire_person_contractor_fixed_rate.html',{'countries': countries})


@company_admin_required
def hirePersonContractorMilestone(request):
    countries = Country.objects.all()
    if request.method == "POST":
        employee, error = hirePersonStep1(request, 'Contractor')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_milestone.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        

        employee, error = hirePersonStep2(request, employee, 'Milestone')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_milestone.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        
        employee, error = hirePersonStep3(request,employee)

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_contractor_milestone.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })

        return redirect('company_dashboard')

    return render(request,'company/hire_person_contractor_milestone.html',{'countries': countries})


@company_admin_required
def hirePersonPersonalProfile(request):
    countries = Country.objects.all()
    if request.method == "POST":
        employee, error = hirePersonStep1(request, 'Personal Profile')

        if error:
            # Handle the error (e.g. show it on the form)
            return render(request, "company/hire_person_personal_profile.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })
        
        try:
            Payment.objects.create(employee=employee)
        except Exception as error:
            return render(request, "company/hire_person_personal_profile.html", {
                "form_data": request.POST,
                "error_message": error,
                'countries': countries,
            })

        response = redirect('company_dashboard')
        # 4. Store email in signed cookie
        response.set_signed_cookie('email', employee.user.email, salt='hire_person_email', max_age=3600)
        return response

    # For GET method
    return render(request, 'company/hire_person_personal_profile.html', {'countries': countries})



@company_admin_required

def personalProfile(request, id):
    company = get_object_or_404(Company, company_admin=request.user)
    employee = get_object_or_404(Employee, id=id, company=company)
    payment = get_object_or_404(Payment, employee=employee)

    emp_documents = EmployeeDocument.objects.filter(employee=employee)
    count = emp_documents.count()

    # Search
    query = request.GET.get('q', '').strip()
    if query:
        emp_documents = emp_documents.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )

    # Sorting
    sort = request.GET.get('sort', '').strip()
    if sort == 'name':
        emp_documents = emp_documents.order_by('name')
    elif sort == 'category':
        emp_documents = emp_documents.annotate(
            status_order=Case(
                When(status__iexact='Approve', then=Value(0)),
                When(status__iexact='Under Review', then=Value(1)),
                When(status__iexact='Rejected', then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('status_order')
    elif sort == 'status':
        emp_documents = emp_documents.order_by('status')
    else:
        emp_documents = emp_documents.order_by('-uploaded_at')

    # Pagination
    paginator = Paginator(emp_documents, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Replace documents with paginated version
    emp_documents = page_obj  # 👈 now 'documents' will be paginated

    if not page_obj.object_list.exists():
        page_obj = None


    monthly_salary = round(payment.salary_per_hour * 176, 2)

    context = {
        'employee': employee,
        'payment': payment,
        'monthly_salary': monthly_salary,
        'documents': emp_documents,  # Use page_obj here
        'page_obj': page_obj,
        'search_query': query,
        'count': count
    }

    return render(request, 'company/personal_profile.html', context)



@company_admin_required
def companyDocument(request):

    company = get_object_or_404(Company, company_admin=request.user)
    documents = CompanyDocument.objects.filter(company_id=company)
    count = CompanyDocument.objects.filter(company_id=company).count()
    total_docs = documents.count()

    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '').strip()

    #Search logic
    if query:
        documents = documents.filter(
            Q(name__icontains=query) 
        )

    # Sorting logic
    if sort == 'name':
        documents = documents.order_by('name')
    else:
        documents = documents.order_by('-uploaded_at')
    # Pagination
    paginator = Paginator(documents, 10)  # Show 10 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if not documents.exists():
        page_obj = None  # Handle case where no employee found
    context = {
        'search_query': query,
        'count': count,
        'documents': page_obj,
        'page_obj': page_obj,
        'total_docs': total_docs
    }
    
    return render(request,'company/company_document.html', context)
    # return render(request,'company/company_document.html', {'documents': documents, 'total_docs': total_docs})


@company_admin_required
def companyUploadDocument(request):
    try:
        company = get_object_or_404(Company, company_admin=request.user)
    except Company.DoesNotExist:
        return redirect('company_document')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category = request.POST.get('category')
        document = request.FILES.get('document')
        if document:
            CompanyDocument.objects.create(
                company_id=company,
                name = name,
                document=document,
                status='Under Review',
                category=category,
                description=description
            )
            # Compose email subject and link
            subject = f"📄 New Document Uploaded by {company.company_name or company.admin_name}"
            dashboard_url = request.build_absolute_uri(f"/superadmin/companies/view/{company.id}")

            # Get super admin
            super_admin = User.objects.filter(role='SUPERADMIN').first()

            if super_admin:
                # Construct the HTML message
                html_message = format_html(
                    """
                    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                        <h2 style="color: #2c3e50;">📢 New Company Document Uploaded</h2>
                        <p style="font-size: 15px; color: #34495e;">
                            A new document has been uploaded by <strong>{}</strong>.
                        </p>
                        <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                            <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                            <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                            <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                            <tr><td><strong>🔍 Status:</strong></td><td>Under Review</td></tr>
                        </table>
                        <br>
                        <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #2c3e50; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                            📂 View Company Dashboard
                        </a>
                        <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated system notification.</p>
                    </div>
                    """,
                    company.company_admin.email or company.company_name,
                    document.name,
                    category,
                    description,
                    dashboard_url
                )

                # Send email
                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[super_admin.email],
                )
                email.content_subtype = "html"  # Important for HTML formatting
                email.send(fail_silently=True)

            messages.success(request, 'Document uploaded successfully!')
        return redirect('company_document' )
    return redirect('company_document')

@company_admin_required
def companyEditDocument(request, document_id):
    document = get_object_or_404(CompanyDocument, id=document_id, company_id__company_admin=request.user)
    company = get_object_or_404(Company, company_admin=request.user)

    if request.method == "POST":
        document.name = request.POST.get("name")
        document.description = request.POST.get("description")
        document.category = request.POST.get("category")

        # If a new file is uploaded
        if request.FILES.get("file"):
            document.document = request.FILES["file"]

        document.save()
        
        # Email subject and dashboard URL
        subject = f"✏️ Document Edited by {company.company_name or company.admin_name}"
        dashboard_url = request.build_absolute_uri(f"/superadmin/companies/view/{company.id}")

        # Get super admin
        super_admin = User.objects.filter(role='SUPERADMIN').first()

        if super_admin:
            html_message = format_html(
                """
                <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f0f9ff;">
                    <h2 style="color: #2c3e50;">✏️ Company Document Edited</h2>
                    <p style="font-size: 15px; color: #34495e;">
                        A document has been <strong>edited</strong> by <strong>{}</strong>.
                    </p>
                    <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                        <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                        <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                        <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                        <tr><td><strong>🔍 Status:</strong></td><td>{}</td></tr>
                    </table>
                    <br>
                    <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                        🔍 View Company Dashboard
                    </a>
                    <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated system notification.</p>
                </div>
                """,
                company.company_admin.email or company.company_name,
                document.name,
                document.category,
                document.description,
                document.status,
                dashboard_url
            )

            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[super_admin.email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=True)
        return redirect('company_document')

    return render(request, 'company/company_edit_document.html', {'document': document})

@company_admin_required
def companyDeleteDocument(request, document_id):
    document = get_object_or_404(CompanyDocument, id=document_id, company_id__company_admin=request.user)
    company = get_object_or_404(Company, company_admin=request.user)

    document.delete()
    # Prepare subject and dashboard URL
    subject = f"🗑️ Document Deleted by {company.company_name or company.admin_name}"
    dashboard_url = request.build_absolute_uri(f"/superadmin/companies/view/{company.id}")

    # Get super admin
    super_admin = User.objects.filter(role='SUPERADMIN').first()

    if super_admin:
        html_message = format_html(
            """
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #f5c6cb; border-radius: 10px; background-color: #fff5f5;">
                <h2 style="color: #c0392b;">🗑️ Document Deleted</h2>
                <p style="font-size: 15px; color: #34495e;">
                    A document has been <strong>deleted</strong> by <strong>{}</strong>.
                </p>
                <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                    <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                    <tr><td><strong>🔍 Status:</strong></td><td>{}</td></tr>
                </table>
                <br>
                <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #c0392b; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                    🧾 View Company Dashboard
                </a>
                <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated system notification.</p>
            </div>
            """,
            company.company_admin.email or company.company_name,
            document.name,
            document.category,
            document.description,
            document.status,
            dashboard_url
        )

        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[super_admin.email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
    return redirect('company_document')


@company_admin_required
def submitPaymentDetails(request, id):
    company = get_object_or_404(Company, company_admin=request.user)
    employee = get_object_or_404(Employee, id=id, company=company)
    payment = get_object_or_404(Payment, employee=id)
 
    documents = employee.documents.all()
    monthly_salary = round(payment.salary_per_hour * 176, 2)

    context = {
        'employee': employee,
        'payment' : payment,
        'monthly_salary': monthly_salary,
        'documents': documents,
        'error_message': None
    }
 
    if(request.method == 'POST'):

        payment_cycle = request.POST.get('payment_cycle')
        salary_per_hour = request.POST.get('salary_per_hour')

        payment_frequency = request.POST.get('payment_frequency')


        try:
            if not employee.user.email:
                raise ValueError("Email not found in session.")

            # employee.start_date=start_date
            # employee.save()

            today=timezone.now()
            days_in_month=calendar.monthrange(today.year, today.month)[1]

            if payment_cycle == 'Twice in month':
                payment_frequency_date2=request.POST.get('payment_frequency_date2')

                # convert string timezone to date object 
                payment_frequency=make_aware(datetime.strptime(payment_frequency, "%Y-%m-%d"))
                payment_frequency_date2=make_aware(datetime.strptime(payment_frequency_date2, "%Y-%m-%d"))

                day1=payment_frequency.day
                day2=payment_frequency_date2.day

                # If payment date1 and date2 had lesser than 7 days then it gives error
                if (day2 - day1) < 7 or (day1 + days_in_month - day2) < 7:
                    context['error_message']="Payment dates gap should be at least of 7 days"
                    return render(request, 'company/personal_profile.html',context)
                    # return None, "Payment dates gap should be at least of 7 days"

                # next salary date fixed
                if(today.day <= day1 or today.day> day2):
                    next_salary_date=day1
                    payment_frequency=day2
                else:
                    next_salary_date=day2
                    payment_frequency=day1

            elif payment_cycle == 'Monthly':
                # convert string timezone to date object 
                payment_frequency=make_aware(datetime.strptime(payment_frequency, "%Y-%m-%d"))
                payment_frequency=payment_frequency.day
                next_salary_date=payment_frequency
            
            elif payment_cycle == 'Weekly' or payment_cycle == 'Bi-weekly' :

                weekday_map = {
                    "monday": 0,
                    "tuesday": 1,
                    "wednesday": 2,
                    "thursday": 3,
                    "friday": 4,
                    "saturday": 5,
                    "sunday": 6,
                }

                target_day_index = weekday_map.get(payment_frequency, None)
                if target_day_index is None:
                    context['error_message']="Invalid payment frequency day."
                    return render(request, 'company/personal_profile.html',context)
                    # return None, "Invalid payment frequency day."

                curreny_day_index=today.weekday()

                days_until_target = (target_day_index - curreny_day_index) % 7
                if days_until_target == 0:
                    days_until_target = 7

                next_salary_date=(today.day+days_until_target)%days_in_month

            else:
                context['error_message']="Selected payment cycle is not valid!"
                return render(request, 'company/personal_profile.html',context)
                # return None, "Selected payment cycle is not valid!"

            payment.payment_cycle=payment_cycle
            payment.payment_frequency=str(payment_frequency)
            payment.salary_per_hour=salary_per_hour
            payment.next_salary_date=str(next_salary_date)
            payment.save()
            
            # Payment instance is assumed to exist (already updated)
            sender_name = employee.company.company_name
            recipient_email = employee.user.email

            subject = f"💰 Payment Details Updated by {sender_name}"
            dashboard_url = request.build_absolute_uri(f"/employee/payment/details/")

            html_message = format_html(
                """
                <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #bee5eb; border-radius: 10px; background-color: #e8f8ff;">
                    <h2 style="color: #007bff;">💼 Payment Information Updated</h2>
                    <p style="font-size: 15px; color: #34495e;">
                        Your payment details have been <strong>updated</strong> by <strong>{}</strong>.
                    </p>
                    <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                        <tr><td><strong>👤 Employee:</strong></td><td>{}</td></tr>
                        <tr><td><strong>🔁 Payment Cycle:</strong></td><td>{}</td></tr>
                        <tr><td><strong>💵 Salary per Hour:</strong></td><td>${}</td></tr>
                    </table>
                    <br>
                    <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                        🔍 View Payment Details
                    </a>
                    <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated notification from the system.</p>
                </div>
                """,
                employee.company.company_admin.email,
                employee.first_name + " " + employee.last_name,
                payment.payment_cycle,
                payment.salary_per_hour,
                dashboard_url
            )

            # Send the email
            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.content_subtype = "html"
            email.send(fail_silently=True)


            return redirect('personal_profile', employee.id)
                
        except Exception as e:
            # Catch-all for unexpected issues
            context['error_message']=f"An unexpected error occurred: {str(e)}"
            return render(request, 'company/personal_profile.html',context)
            # return None, f"An unexpected error occurred: {str(e)}"

    return render(request, 'company/personal_profile.html', context)

def employeeEditDocument(request, document_id , employee_id):
    document = get_object_or_404(EmployeeDocument, id=document_id)
    # employee_id = document.employee.id
    employee = get_object_or_404(Employee, id=employee_id)
    # employee = document.employee.id
    context = {
        'document':document,
        'employee_id': employee_id,
    }
    if request.method == "POST":
        document.name = request.POST.get("name")
        document.description = request.POST.get("description")
        document.category = request.POST.get("category")
        document.status = request.POST.get("status")
        # If a new file is uploaded
        if request.FILES.get("file"):
            document.document = request.FILES["file"]

        document.save()

        # Send email to the employee
        uploader = employee.company.company_admin.email
        recipient_email = employee.user.email

        subject = f"📄 Document Updated by {uploader}"

        dashboard_url = request.build_absolute_uri(f"/company/employee/personal_profile/{employee_id}/")

        html_message = format_html(
            """
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                <h2 style="color: #2c3e50;">✏️ Document Updated</h2>
                <p style="font-size: 15px; color: #34495e;">
                    A document has been <strong>updated</strong> by <strong>{}</strong>.
                </p>
                <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                    <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                    <tr><td><strong>🔍 Status:</strong></td><td>{}</td></tr>
                </table>
                <br>
                <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #2c3e50; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                    📂 View All Documents
                </a>
                <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated email from the document management system.</p>
            </div>
            """,
            uploader, document.name, document.category, document.description, document.status, dashboard_url
        )

        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        email.content_subtype = "html"  # Send as HTML
        email.send(fail_silently=True)
        return redirect('personal_profile' , employee_id)

    return render(request, 'company/employee_edit_document.html', context)

def employeeDeleteDocument(request,document_id,employee_id):
    document = get_object_or_404(EmployeeDocument, id=document_id)
    if document.document:
        document.document.delete(save=False)
    document.delete()

    # Email sender and receiver
    uploader = document.employee.company.company_admin.email
    recipient_email = document.employee.user.email

    # Email subject and URL
    subject = f"🗑️ Document Deleted by {uploader}"
    dashboard_url = request.build_absolute_uri(f"/company/employee/personal_profile/{employee_id}/")

    # HTML Message
    html_message = format_html(
        """
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #fff0f0;">
            <h2 style="color: #c0392b;">🗑️ Document Deleted</h2>
            <p style="font-size: 15px; color: #34495e;">
                A document has been <strong>deleted</strong> by <strong>{}</strong>.
            </p>
            <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                <tr><td><strong>🔍 Status:</strong></td><td>{}</td></tr>
            </table>
            <br>
            <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #c0392b; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                🔁 View Profile
            </a>
            <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated notification from the document system.</p>
        </div>
        """,
        uploader, document.name, document.category, document.description, document.status, dashboard_url
    )

    # Send the email
    email = EmailMessage(
        subject=subject,
        body=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=True)
    

    return redirect('personal_profile' , employee_id)

@company_admin_required
def companyEditEmployee(request, id):
    try:
        employee = Employee.objects.get(id=id)
        countries = Country.objects.all() 
    except Company.DoesNotExist:
        return redirect('company_employee')
    
    if request.method == 'POST':
        if 'photo' in request.FILES:
            employee.photo = request.FILES['photo']
            employee.save()
            return redirect('company_edit_employee', id)
        
        country_id = request.POST.get("country")
        country_obj = Country.objects.get(id=country_id)

        employee.first_name = request.POST.get("first_name")
        employee.last_name = request.POST.get("last_name")
        employee.country_id = country_obj
        employee.status = request.POST.get("status")
        employee.work_location = request.POST.get("work_location")
        employee.job_title = request.POST.get("job_title")
        employee.phone_number = request.POST.get("phone_number")
        employee.save()

        return redirect('company_employee')


    context = {
        'employee': employee,
        'countries': countries
    }

    return render(request, 'company/edit_employee.html', context)