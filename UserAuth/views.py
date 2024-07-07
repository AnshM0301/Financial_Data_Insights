from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from dashboard.models import Portfolio


def register(request):  # sourcery skip: extract-method, remove-redundant-fstring
    if request.method == "POST":
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = False
            user.is_superuser = False
            user.save()    
            Portfolio.objects.create(user=user)
            messages.success(request, 'Congratulations, Your account has been created! Please Login.')
            return redirect('login')
        
    else:
        form = UserRegisterForm()

    return render(request, 'UserAuth/register.html',{'form':form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f'You are now Successfully logged in as {username}')
                return redirect('home')
            else:
                messages.error(request, 'Invalid username or password!')
                # return JsonResponse({'danger': 'Invalid username or password!'})

        else:
            messages.error(request, 'Invalid username or password!')
            # return JsonResponse({'danger': 'Invalid username or password!'})

    else:
        form = AuthenticationForm()
    return render(request, 'UserAuth/login.html', {'form':form})

def logout_view(request):  # Add logout view
    logout(request)
    messages.info(request, 'You have been logged out')
    return redirect('home')  # Redirect to login page after logout

def profile(request): 
    return render(request, 'UserAuth/profile.html')




