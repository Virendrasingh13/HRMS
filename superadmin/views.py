from django.shortcuts import render
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from core.models import *
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.mail import EmailMessage
from django.utils.html import format_html
from django.conf import settings

from django.utils import timezone
from datetime import date,datetime, timedelta
import calendar
from django.utils.timezone import make_aware

# Decorator to check if user is superadmin

def superadmin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if getattr(request.user, 'role', None) != 'SUPERADMIN':
            logout(request)
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Home page: show superadmin and companies with employee counts

# @login_required
@superadmin_required
def superadminHome(request):
    superadmin = User.objects.filter(role='SUPERADMIN').first()
    companies = Company.objects.all().order_by('-created_at')[:9]
    # Add employee count for each company
    companies_data = []
    for company in companies:
        companies_data.append({
            'company': company,
            'employee_count': company.employees.count(),
        })
    return render(request, 'superadmin/superadmin_home.html', {
        'superadmin': superadmin,
        'companies_data': companies_data,
    })

# Companies page: show all companies with details and employee count

# @login_required
@superadmin_required
def superadminCompanies(request):
    query = request.GET.get('q')  # 'q' is the input field name in HTML
    if query:
        companies = Company.objects.filter(
            Q(company_name__icontains=query) |
            Q(admin_name__icontains=query)
        )
    else:
        companies = Company.objects.all()

    total_companies = companies.count()
    active_companies = companies.filter(status='Active').count()
    pending_companies = companies.filter(status='Inactive').count()

    paginator = Paginator(companies, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    companies_data = []
    for company in page_obj:
        companies_data.append({
            'company': company,
            'employee_count': company.employees.count(),
        })

    return render(request, 'superadmin/superadmin_companies.html', {
        'companies_data': companies_data,
        'total_companies': total_companies,
        'active_companies': active_companies,
        'pending_companies': pending_companies,
        'page_obj': page_obj,
        'search_query': query,
    })

# Countries page: show all countries

# @login_required
@superadmin_required
def superadminCountries(request):
    sort = request.GET.get('sort', '').strip()
    order = request.GET.get('order', 'asc').strip()
    query = request.GET.get('q', '').strip()
    countries = Country.objects.all()

    # Apply search
    if query:
        countries = countries.filter(name__icontains=query)

    # Apply sorting
    if sort == 'status':
        countries = countries.order_by('-status' if order == 'desc' else 'status')
    elif sort == 'name':
        countries = countries.order_by('-name' if order == 'desc' else 'name')

    count = countries.count()

    # Apply pagination
    paginator = Paginator(countries, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    countries = page_obj.object_list if page_obj.object_list.exists() else []

    context = {
        'countries': countries,
        'sort': sort,
        'order': order,
        'count': count,
        'page_obj': page_obj,
        'search_query': query,
    }

    # Handle POST request to add a new country
    if request.method == "POST":
        country_name = request.POST.get("countryName")
        country_code = request.POST.get("countryCurruncy")
        country_status = request.POST.get("countryStatus")

        if not country_name or not country_code or not country_status:
            context['error_message'] = 'All fields are required.'
            return render(request, 'superadmin/superadmin_countries.html', context)

        if Country.objects.filter(name=country_name, code=country_code).exists():
            context['error_message'] = 'Country with this name and code already exists.'
            return render(request, 'superadmin/superadmin_countries.html', context)

        # Create new country
        Country.objects.create(name=country_name, code=country_code, status=country_status)

        # Rebuild queryset with new data
        countries = Country.objects.all()
        if query:
            countries = countries.filter(name__icontains=query)
        if sort == 'status':
            countries = countries.order_by('-status' if order == 'desc' else 'status')
        elif sort == 'name':
            countries = countries.order_by('-name' if order == 'desc' else 'name')

        paginator = Paginator(countries, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        countries = page_obj.object_list if page_obj.object_list.exists() else []

        context = {
            'countries': countries,
            'sort': sort,
            'order': order,
            'count': countries.count(),
            'page_obj': page_obj,
            'search_query': query,
            'success_message': 'Country added successfully.',
        }
        return render(request, 'superadmin/superadmin_countries.html', context)

    return render(request, 'superadmin/superadmin_countries.html', context)




# @login_required
@superadmin_required
def superadminDeactiveCountry(request, country_id):
    try:
        country = Country.objects.get(id=country_id)
        country.status = 'Inactive'
        country.save()
        return redirect('superadmin_countries')
    except Country.DoesNotExist:
        return render(request, 'superadmin/superadmin_countries.html', {'error_message': 'Country not found.'})
    
# @login_required
@superadmin_required
def superadminActiveCountry(request, country_id):
    try:
        country = Country.objects.get(id=country_id)
        country.status = 'Active'
        country.save()
        return redirect('superadmin_countries')
    except Country.DoesNotExist:
        return render(request, 'superadmin/superadmin_countries.html', {'error_message': 'Country not found.'})

# @login_required
@superadmin_required
def superadminEditCompany(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return redirect('superadmin_companies')
    if request.method == 'POST':
        company_name = request.POST.get('companyname')
        country_id = request.POST.get('countryName')
        status = request.POST.get('status')
        admin_name = request.POST.get('fullname')
        if company_name:
            company.company_name = company_name
        if country_id:
            company.country_id_id = country_id
        if status:
            company.status = status
        if admin_name:
            company.admin_name = admin_name
        company.save()
        return redirect('superadmin_companies')
    countries = Country.objects.all()
    return render(request, 'superadmin/edit_company.html', {
        'company': company,
        'countries': countries,
    })

# @login_required
@superadmin_required
@superadmin_required
def superadminEditView(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return redirect('superadmin_companies')

    # ------------------------------
    # Documents Section
    # ------------------------------
    documents = CompanyDocument.objects.filter(company_id=company).order_by('-uploaded_at')
    doc_query = request.GET.get('q', '').strip()
    doc_sort = request.GET.get('sort', '').strip()

    if doc_query:
        documents = documents.filter(Q(name__icontains=doc_query))

    if doc_sort == 'name':
        documents = documents.order_by('name')
    else:
        documents = documents.order_by('-uploaded_at')

    doc_paginator = Paginator(documents, 10)
    doc_page_number = request.GET.get('page')
    doc_page_obj = doc_paginator.get_page(doc_page_number)

    if not doc_page_obj.object_list.exists():
        doc_page_obj = None

    total_docs = documents.count()

    # ------------------------------
    # Employees Section
    # ------------------------------
    emp_query = request.GET.get('eq', '').strip()
    employee_list = Employee.objects.filter(company_id=company)

    if emp_query:
        employee_list = employee_list.filter(
            Q(first_name__icontains=emp_query) |
            Q(last_name__icontains=emp_query) |
            Q(job_title__icontains=emp_query)
        )

    emp_paginator = Paginator(employee_list, 10)
    emp_page_number = request.GET.get('epage')
    emp_page_obj = emp_paginator.get_page(emp_page_number)

    emp_count = employee_list.count()

    # Payments (used for salaries)
    payments = Payment.objects.filter(employee__in=employee_list)
    for pay in payments:
        pay.salary_per_hour = round(pay.salary_per_hour * 176, 2)

    # ------------------------------
    # Final context
    # ------------------------------
    context = {
        'company': company,

        # Documents
        'documents': doc_page_obj,
        'page_obj': doc_page_obj,
        'count': documents.count(),
        'search_query': doc_query,
        'total_docs': total_docs,

        # Employees
        'employees': emp_page_obj,
        'emp_count': emp_count,
        'emp_search_query': emp_query,
        'payments': payments,
    }

    return render(request, 'superadmin/edit_view.html', context)


@superadmin_required
def superadminEditDocument(request, document_id, company_id):
    from core.models import CompanyDocument
    try:
        document = CompanyDocument.objects.get(id=document_id)
    except CompanyDocument.DoesNotExist:
        return redirect('superadmin_companies')
    if request.method == 'POST':
        document.name = request.POST.get('name', document.name)
        document.category = request.POST.get('category', document.category)
        document.status = request.POST.get('status', document.status)
        document.description = request.POST.get('description', document.description)
        if request.FILES.get('document'):
            document.document = request.FILES['document']
        document.save()

        # Email subject and link
        subject = f"✏️ Company Document Updated by {request.user.email}"
        dashboard_url = request.build_absolute_uri(f"/company/documents/")  # Adjust as needed

        # Email body
        html_message = format_html(
            """
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #d1ecf1; border-radius: 10px; background-color: #f0fcff;">
                <h2 style="color: #007bff;">✏️ Document Edited</h2>
                <p style="font-size: 15px; color: #34495e;">
                    A document belonging to <strong>{}</strong> was updated by <strong>{}</strong> ({})
                </p>
                <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                    <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                    <tr><td><strong>🔍 Status:</strong></td><td>{}</td></tr>
                </table>
                <br>
                <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                    📂 View Documents
                </a>
                <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated system notification.</p>
            </div>
            """,
            document.company_id.company_name or "the company",
            'Superadmin',
            request.user.email,
            document.name,
            document.category,
            document.description,
            document.status,
            dashboard_url
        )

        # Send the email
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[document.company_id.company_admin.email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)

        return redirect('superadmin_edit_view', company_id=document.company_id.id)
    return render(request, 'superadmin/edit_document.html', {'document': document})

# @login_required
@superadmin_required
def superadminUploadDocument(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return redirect('superadmin_companies')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category = request.POST.get('category')
        status = 'Approve'  # Always set to Active on upload
        file = request.FILES.get('document')
        if file:
            CompanyDocument.objects.create(
                company_id=company,
                name=name,
                document=file,
                status=status,
                category=category,
                description=description
            )

        # Sender & receiver info
        admin_email = company.company_admin.email
        superadmin_name = request.user.get_full_name() or request.user.username
        superadmin_email = request.user.email

        # Document link (adjust as per your routing)
        dashboard_url = request.build_absolute_uri(f"/company/documents/")

        # Subject
        subject = f"📄 New Document Uploaded by SuperAdmin ({superadmin_name})"

        # Compose the HTML email
        html_message = format_html(
            """
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #cce5ff; border-radius: 10px; background-color: #f0f8ff;">
                <h2 style="color: #007bff;">📁 New Company Document Uploaded</h2>
                <p style="font-size: 15px; color: #34495e;">
                    A new document has been uploaded for <strong>{}</strong> by the SuperAdmin <strong>{}</strong> ({})
                </p>
                <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                    <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                    <tr><td><strong>🔍 Status:</strong></td><td>Active</td></tr>
                </table>
                <br>
                <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                    🔍 View Documents
                </a>
                <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated notification from the system.</p>
            </div>
            """,
            company.company_name,
            superadmin_name,
            superadmin_email,
            name,
            category,
            description,
            dashboard_url
        )

        # Send the email
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)
        return redirect('superadmin_edit_view', company_id=company.id)
    return redirect('superadmin_edit_view', company_id=company.id)

# @login_required
@superadmin_required
def superadminDeleteCompany(request, company_id):
    try:
        company = Company.objects.get(id=company_id)
        # Delete all related documents and their files
        for doc in company.documents.all():
            if doc.document:
                doc.document.delete(save=False)
            doc.delete()
        company.delete()
        return redirect('superadmin_companies')
    except Company.DoesNotExist:
        return redirect('superadmin_companies')

# @login_required
@superadmin_required
def superadminDeleteDocument(request, document_id):
    try:
        document = CompanyDocument.objects.get(id=document_id)
        company_id = document.company_id.id
        if document.document:
            document.document.delete(save=False)
        document.delete()

        # Reference before deletion
        company = document.company_id
        admin_email = company.company_admin.email
        superadmin_name = request.user.email or request.user.username
        superadmin_email = request.user.email

        # Email content
        subject = f"🗑️ Document Deleted by SuperAdmin ({superadmin_name})"
        dashboard_url = request.build_absolute_uri(f"/company/documents/")

        html_message = format_html(
            """
            <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #f5c6cb; border-radius: 10px; background-color: #fff5f5;">
                <h2 style="color: #c0392b;">🗑️ Document Deleted</h2>
                <p style="font-size: 15px; color: #34495e;">
                    A document for <strong>{}</strong> has been <strong>deleted</strong> by SuperAdmin <strong>{}</strong> ({})
                </p>
                <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                    <tr><td><strong>📄 Document Name:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📁 Category:</strong></td><td>{}</td></tr>
                    <tr><td><strong>📝 Description:</strong></td><td>{}</td></tr>
                    <tr><td><strong>🔍 Status:</strong></td><td>{}</td></tr>
                </table>
                <br>
                <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #c0392b; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                    📂 View All Documents
                </a>
                <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated system notification.</p>
            </div>
            """,
            company.company_name,
            superadmin_name,
            superadmin_email,
            document.name,
            document.category,
            document.description,
            document.status,
            dashboard_url
        )

        # Send email
        email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[admin_email],
        )
        email.content_subtype = "html"
        email.send(fail_silently=True)

        return redirect('superadmin_edit_view', company_id=company_id)
    except CompanyDocument.DoesNotExist:
        return redirect('superadmin_companies')

@superadmin_required
def superadminEditCountry(request, country_id):
    try:
        country = Country.objects.get(id=country_id)
    except Country.DoesNotExist:
        return redirect('superadmin_countries')
    if request.method == 'POST':
        country_name = request.POST.get('countryName')
        country_code = request.POST.get('countryCurruncy')
        status = request.POST.get('countryStatus')
        if country_name:
            country.name = country_name
        if country_code:
            country.code = country_code
        if status:
            country.status = status
        country.save()
        return redirect('superadmin_countries')
    return render(request, 'superadmin/edit_country.html', {'country': country})

@superadmin_required
def paymentDetailsData(request, company_id, employee_id):
    try:
        employee = Employee.objects.get(id=employee_id)
        payment = Payment.objects.get(employee=employee_id)
        employees = Employee.objects.filter(company_id=employee.company)
        payments = Payment.objects.filter(employee__in=employees)
        documents = CompanyDocument.objects.filter(company_id=employee.company)

        for pay in payments:
            pay.salary_per_hour = round(pay.salary_per_hour*176,2)

    except Employee.DoesNotExist:
        return redirect('superadmin_edit_view', employee.company)
    
    context={
        'openModal':'open',
        'company': employee.company,
        'employees': employees,
        'documents': documents,
        'employee': employee,
        'payments': payments,
        'payment': payment,
    }
    return render(request, 'superadmin/edit_view.html', context)

@superadmin_required
def submitButtonPaymentDetails(request, company_id, employee_id):
    
    try:
        employee = Employee.objects.get(id=employee_id)
        payment = Payment.objects.get(employee=employee_id)
        employees = Employee.objects.filter(company_id=employee.company)
        payments = Payment.objects.filter(employee__in=employees)
        documents = CompanyDocument.objects.filter(company_id=employee.company)


        for pay in payments:
            pay.salary_per_hour = round(pay.salary_per_hour*176,2)

        context={
            'openModal': '',
            'company': employee.company,
            'employees' : employees,
            'documents': documents,
            'employee': employee,
            'payments': payments,
            'payment': payment,
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


            # Email details
                superadmin_name = request.user.get_full_name() or request.user.username
                superadmin_email = request.user.email
                employee_email = employee.user.email
                employee_name = employee.user.get_full_name() or employee.user.username

                subject = f"💰 Payment Details Updated by SuperAdmin ({superadmin_name})"
                dashboard_url = request.build_absolute_uri("/employee/payment/details/")

                html_message = format_html(
                    """
                    <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #bee5eb; border-radius: 10px; background-color: #e8f8ff;">
                        <h2 style="color: #007bff;">💼 Payment Information Updated</h2>
                        <p style="font-size: 15px; color: #34495e;">
                            Dear <strong>{}</strong>,<br><br>
                            Your payment details have been <strong>updated</strong> by the SuperAdmin <strong>{}</strong> ({})
                        </p>
                        <table style="font-size: 15px; margin-top: 10px; color: #2c3e50;">
                            <tr><td><strong>🔁 Payment Cycle:</strong></td><td>{}</td></tr>
                            <tr><td><strong>💵 Salary per Hour:</strong></td><td>${}</td></tr>
                        </table>
                        <br>
                        <a href="{}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: #ffffff; text-decoration: none; border-radius: 5px; margin-top: 20px;">
                            🔍 View Payment Details
                        </a>
                        <p style="font-size: 12px; margin-top: 30px; color: #95a5a6;">This is an automated system notification.</p>
                    </div>
                    """,
                    employee_name,
                    superadmin_name,
                    superadmin_email,
                    payment.payment_cycle,
                    payment.salary_per_hour,
                    dashboard_url
                )

                email = EmailMessage(
                    subject=subject,
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[employee_email],
                )
                email.content_subtype = "html"
                email.send(fail_silently=True)

                return redirect('superadmin_edit_view',employee.company.id)

            except Exception as e:
                # Catch-all for unexpected issues
                context['error_message']=f"An unexpected error occurred: {str(e)}"
                return redirect('superadmin_edit_view', employee.company.id)
            # return render(request, 'company/personal_profile.html',context)
            # return None, f"An unexpected error occurred: {str(e)}"

    except Employee.DoesNotExist:
        return redirect('superadmin_edit_view', employee.company)
    
    return render(request, 'superadmin/edit_view.html', context)