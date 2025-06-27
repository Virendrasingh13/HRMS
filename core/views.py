from multiprocessing import AuthenticationError
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, logout, login
# from .models import Country, User
from django.contrib.auth.models import User
from superadmin.urls import *
from superadmin.views import *
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
import mimetypes
import os
import urllib.parse
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from core.models import User


def error(message):
    raise NotImplementedError


def loginView(request):
    logout(request)  # Ensure user is logged out before login attempt
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user_obj = User.objects.get(email__iexact=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            print("User authenticated successfully")
            login(request,user)

            if user.role == 'SUPERADMIN':
                # login_main(request, user)
                return redirect('superadmin_home')
            elif user.role == 'COMPANY':
                return redirect('email_verify')
            elif user.role == 'EMPLOYEE':
                return redirect('employee_dashboard')
            else:
                return render(request, 'login.html', {'error_message': 'Invalid user role'})
        print("User not authenticated")
        return render(request, 'login.html', {'error_message': 'Invalid credentials'})
    return render(request, 'login.html')

def logoutView(request):
    logout(request)
    error_message = request.GET.get('error_message')
    if error_message:
        return render(request, 'login.html', {'error_message': error_message})
    return redirect('login')


@login_required
def employeeDashboard(request):
    return render(request, 'employee/employee_dashboard.html')


@login_required
def protectedDocument(request, path):
    # Decode URL-encoded path
    safe_path = urllib.parse.unquote(path)
    file_path = os.path.join(settings.MEDIA_ROOT, safe_path)
    if not os.path.isfile(file_path):
        raise Http404(f"File not found: {file_path}")
    content_type, _ = mimetypes.guess_type(file_path)
    return FileResponse(open(file_path, 'rb'), content_type=content_type)

def password_reset_request(request):
    return render(request, 'forgot_password.html')

def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password = request.POST.get('password')
            password2 = request.POST.get('password2')
            if password and password == password2 and len(password) >= 8:
                user.set_password(password)
                user.status = 'Active'
                user.save()
                if hasattr(user, 'employee_profile'):
                    user.employee_profile.status = 'Active'
                    user.employee_profile.save()
                print("Password set successfully")
                return render(request, 'login.html', {'messages': 'Password has been set successfully.'})
            else:
                return render(request, 'forgot_password.html', {'error_message': 'Passwords do not match or are too short.'})
        return render(request, 'forgot_password.html', {'validlink': True, 'uidb64': uidb64, 'token': token})
    else:
        return render(request, 'error.html', {'error_message': 'The password reset link is invalid or has expired.'})

