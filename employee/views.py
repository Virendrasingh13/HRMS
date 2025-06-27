from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.core.paginator import Paginator
from core.models import *
from django.utils.html import format_html

@login_required
def employee_dashboard(request):
    employee = get_object_or_404(Employee, user=request.user.id)
    payment = get_object_or_404(Payment, employee=employee.id)
    now = datetime.now().hour
 
    if 5 <= now < 12:
        greeting = "Good morning"
    elif 12 <= now < 17:
        greeting = "Good afternoon"
    elif 17 <= now < 22:
        greeting = "Good evening"
    else:
        greeting = "Hello"
 
    context = {
        'employee': employee,
        'role': request.user.role,
        'greeting': greeting,
        'payment': payment
    }
    return render(request, 'employee/employee_dashboard.html', context)

@login_required
def employee_documents(request):
    emp = Employee.objects.filter(user=request.user).first()
    count = EmployeeDocument.objects.filter(employee=emp).count()
    emp_documents = EmployeeDocument.objects.filter(employee=emp)
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', '').strip()
    if query:
        emp_documents = emp_documents.filter(
            Q(name__icontains=query) | Q(category__icontains=query)
        )
    # Sorting logic
    if sort == 'name':
        emp_documents = emp_documents.order_by('name')
    elif sort == 'category':
        # Custom order for status: Approve, Under Review, Rejected
        from django.db.models import Case, When, Value, IntegerField
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
    paginator = Paginator(emp_documents, 10)  # Show 10 documents per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if not emp_documents.exists():
        page_obj = None  # Handle case where no documents are found
    context = {
        'emp_documents': page_obj,
        'search_query': query,
        'count': count,
        'employee': emp,
        'page_obj': page_obj,
    }
    return render(request, 'employee/employee_documents.html', context)

@login_required
def employee_profile(request):
    countries = Country.objects.filter(status='Active').all()
    employee = Employee.objects.filter(user=request.user).first()
    if not employee:
        # Optionally handle if employee record does not exist
        return redirect('employee_dashboard')

    if request.method == 'POST':
        # Handle profile photo upload
        if 'photo' in request.FILES:
            employee.photo = request.FILES['photo']
            employee.save()
            return redirect('employee_profile')
        # Handle profile update
        employee.first_name = request.POST.get('first_name', employee.first_name)
        employee.last_name = request.POST.get('last_name', employee.last_name)
        country_id = request.POST.get('country_id')
        if country_id:
            try:
                employee.country_id_id = int(country_id)
            except Exception:
                pass
        employee.phone_number = request.POST.get('phone_number', employee.phone_number)
        employee.save()
        return redirect('employee_profile')

    context = {
        'employee': employee,
        'countries': countries,
    }
    return render(request, 'employee/employee_profile.html', context)

@login_required
def employeeUploadDocuments(request, employee_id, source=None):
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        return redirect('employee_documents')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category = request.POST.get('category')
        if source == 'company':
            status = 'Approve'  # Always set to Approve on upload by Company Admin
        else:
            status = 'Under Review'  # Always set to Under Review on upload by Employee
        file = request.FILES.get('document')
        if file:
            doc = EmployeeDocument.objects.create(
                employee=employee,
                name=name,
                document=file,
                status=status,
                category=category,
                description=description
            )
        # Send email on document upload
        if employee.company and employee.company.company_admin and employee.company.company_admin.email:
            if source == 'company':
                subject = f"📄 New Document Uploaded by {employee.company.company_admin.email}"
                uploader = employee.company.company_admin.email
                recipient_email = employee.user.email
            else:
                subject = f"📄 New Document Uploaded by {employee.user.email}"
                uploader = employee.user.username
                recipient_email = employee.company.company_admin.email

            dashboard_url = request.build_absolute_uri(f"/company/employee/personal_profile/{employee_id}/")

            html_message = format_html(
                """
                <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                    <h2 style="color: #2c3e50;">📢 New Document Notification</h2>
                    <p style="font-size: 15px; color: #34495e;">
                        A new document has been <strong>uploaded</strong> by <strong>{}</strong>.
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
                uploader, doc.name, doc.category, doc.description, doc.status, dashboard_url
            )

            email = EmailMessage(
                subject=subject,
                body=html_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            email.content_subtype = "html"  # This is important to send as HTML
            email.send(fail_silently=True)

        if source == 'employee':
            return redirect('employee_dashboard')
        elif source == 'company':
            return redirect('personal_profile', id=employee_id)
        
    return redirect('employee_documents')

@login_required
def employeeEditDocument(request, document_id, source=None):

    document = get_object_or_404(EmployeeDocument, id=document_id)
    if source == 'company':
        if request.method == 'POST':
            document.name = request.POST.get('name', document.name)
            document.category = request.POST.get('category', document.category)
            document.description = request.POST.get('description', document.description)
            document.status = request.POST.get('status', document.status)
            if request.FILES.get('document'):
                document.document = request.FILES['document']
            document.save()
            return redirect('personal_profile', id=document.employee.id)

        return render(request, 'company/employee_edit_document.html', {'document': document})

    # Only allow the owner employee to edit
    if document.employee.user != request.user and not document.employee.company:
        return HttpResponseForbidden("You do not have permission to edit this document.")
    if request.method == 'POST':
        document.name = request.POST.get('name', document.name)
        document.category = request.POST.get('category', document.category)
        document.description = request.POST.get('description', document.description)
        document.status = request.POST.get('status', document.status)
        if request.FILES.get('document'):
            document.document = request.FILES['document']
        document.save()
        # Send notification to company admin
        employee = document.employee
        if employee.company and employee.company.company_admin and employee.company.company_admin.email:
            subject = f"Document Edited by {employee.user.get_full_name() or employee.user.username}"
            dashboard_url = request.build_absolute_uri(f"/company/employee/personal_profile/{document.employee.id}/")
            message = (
                f"A document has been edited by {employee.user.get_full_name() or employee.user.username}.\n\n"
                f"Document Name: {document.name}\nCategory: {document.category}\nDescription: {document.description}\nStatus: {document.status}\n\n"
                f"View all documents: {dashboard_url}"
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.company.company_admin.email], fail_silently=True)
        if source == 'company':
            return redirect('personal_profile', id=document.employee.id)
        
        return redirect('employee_documents')
    return render(request, 'employee/edit_document.html', {'document': document})

@login_required
def employeeDeleteDocument(request, document_id, source=None):
    document = get_object_or_404(EmployeeDocument, id=document_id)
    # Only allow the owner employee to delete
    if document.employee.user != request.user and not document.employee.company:
        return HttpResponseForbidden("You do not have permission to delete this document.")
    employee = document.employee
    doc_name = document.name
    doc_category = document.category
    doc_description = document.description
    doc_status = document.status
    if document.document:
        document.document.delete(save=False)
    document.delete()
    # Send notification to company admin
    if employee.company and employee.company.company_admin and employee.company.company_admin.email:
        subject = f"Document Deleted by {employee.user.get_full_name() or employee.user.username}"
        dashboard_url = request.build_absolute_uri(f"/company/employee/personal_profile/{document.employee.id}/")
        message = (
            f"A document has been deleted by {employee.user.get_full_name() or employee.user.username}.\n\n"
            f"Document Name: {doc_name}\nCategory: {doc_category}\nDescription: {doc_description}\nStatus: {doc_status}\n\n"
            f"View all documents: {dashboard_url}"
        )
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [employee.company.company_admin.email], fail_silently=True)
    if source == 'company':
        return redirect('personal_profile', id=document.employee.id)
    return redirect('employee_documents')
