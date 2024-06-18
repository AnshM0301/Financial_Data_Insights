from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    contact = forms.CharField(max_length=15)

    class Meta:
        model = User
        fields = ['first_name','last_name','username', 'email', 'contact','password1', 'password2']