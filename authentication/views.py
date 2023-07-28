from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from reg_login import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token
from django.core.mail import EmailMessage, send_mail

# Create your views here.
def home(request):
    return render(request, "index.html")

def signup(request):

    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if User.objects.filter(username=username):
            messages.error(request, "Username already exists.")
            return redirect('home')
        
        if User.objects.filter(email=email):
            messages.error(request, "Email already exists.")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords did'nt match.")

        if not username.isalnum():
            messages.error(request, "Username must be alphanumeric.")
            return redirect('home')

        myuser = User.objects.create_user(username, email, pass1)
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your account has been successfully created. Confirm email.")

        # welcome email

        subject = "Welcome to gfg - django login"
        message = "Hello " + myuser.username + "confirm your email to activate your account. "
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently = True)


        # send confirmation email

        current_site = get_current_site(request)
        email_subject = "Confirm your email address."
        message2 = render_to_string('email_confirmation.html',
                                    {
                                        'username': myuser.username,
                                        'domain': current_site.domain,
                                        'uid': urlsafe_base64_encode(force_bytes(myuser.pk)),
                                        'token': generate_token.make_token(myuser)
                                    })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fail_silently = True
        email.send()
                                    
        return redirect('signin')

    return render(request, "signup.html")

def signin(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        pass1 = request.POST.get('pass1')

        user = authenticate(username = username, password = pass1)

        if user is not None:
            login(request, user)
            return render(request, "index.html", {'username': username})
        else:
            messages.error(request, "Bad Credentials!")
            return redirect('home')

    return render(request, "signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        # login(request, myuser)
        messages.success(request, "Your email has been confirmed. You can signin now.")

        return redirect('signin')
    else:
        return render(request, 'activation_failed.html')